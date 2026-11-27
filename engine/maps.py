"""Download, clean, save and load the Yerevan road maps.

Each map is a square around Republic Square. "Size" is half the side of the
square, so the 2000 m map covers 4 km x 4 km. Only drivable streets are kept,
and one way streets stay one way.

Two files per size live in data/maps/:
  yerevan_2000m_raw.graphml   the streets exactly as downloaded
  yerevan_2000m.graphml       the cleaned map that the game uses

Run with internet access the first time:
    python -m engine.maps
It downloads the biggest map once, cuts the smaller squares out of it, and
saves raw and cleaned files. If the raw files already exist it skips the
download and only redoes the cleaning, so a change to the cleaning rules
never needs the busy map server again.
Map data from OpenStreetMap contributors.
"""

import time
from pathlib import Path

import networkx as nx
import osmnx as ox

# Republic Square, Yerevan (latitude, longitude)
CENTER = (40.1777, 44.5126)

# Half side of each square map, in meters
MAP_SIZES_M = (2000, 2500, 3000)

MAPS_DIR = Path(__file__).resolve().parent.parent / "data" / "maps"

# The public map server is often busy, so we wait and try again.
RETRY_WAITS_S = (30, 60, 120, 240)


def raw_map_path(size_m: int) -> Path:
    """Where the map exactly as downloaded lives."""
    return MAPS_DIR / f"yerevan_{size_m}m_raw.graphml"


def map_path(size_m: int) -> Path:
    """Where the cleaned map used by the game lives."""
    return MAPS_DIR / f"yerevan_{size_m}m.graphml"


# Downloading

def download_map(size_m: int) -> nx.MultiDiGraph:
    """Download the drivable streets in a square around the center."""
    return ox.graph_from_point(
        CENTER, dist=size_m, dist_type="bbox", network_type="drive", simplify=True
    )


def download_with_retries(size_m: int) -> nx.MultiDiGraph:
    """Download a map, waiting longer after each failed try."""
    for wait_s in RETRY_WAITS_S:
        try:
            return download_map(size_m)
        except Exception as error:  # server busy, timeout, dropped connection
            print(f"  Server problem ({type(error).__name__}). Retrying in {wait_s} s ...")
            time.sleep(wait_s)
    return download_map(size_m)  # last try; if it fails, the error is shown


def cut_square(big_map: nx.MultiDiGraph, size_m: int) -> nx.MultiDiGraph:
    """Cut a smaller square around the center out of a bigger map."""
    bbox = ox.utils_geo.bbox_from_point(CENTER, dist=size_m)
    return ox.truncate.truncate_graph_bbox(big_map, bbox)


def download_raw_maps() -> None:
    """Download the biggest map once, then cut the smaller ones from it.

    One download instead of three is kinder to the busy server, and it
    guarantees that all three maps share exactly the same streets.
    """
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    biggest = max(MAP_SIZES_M)
    print(f"Downloading the {biggest} m map ...")
    big_map = download_with_retries(biggest)
    for size in MAP_SIZES_M:
        graph = big_map if size == biggest else cut_square(big_map, size)
        ox.save_graphml(graph, raw_map_path(size))


# Cleaning

def clean_map(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Make the map safe to drive on.

    1. Keep only the biggest part where every intersection can reach every
       other one (respecting one way streets). Pieces outside it are places a
       robot could drive into and never leave, or never reach at all.
    2. Remove streets that start and end at the same intersection (small
       loops). They never help a route.
    Street lengths are already in meters (OSMnx measures them).
    """
    cleaned = ox.truncate.largest_component(graph, strongly=True)
    cleaned = nx.MultiDiGraph(cleaned)  # a copy we are allowed to change
    cleaned.remove_edges_from(list(nx.selfloop_edges(cleaned, keys=True)))
    return cleaned


def save_clean_maps() -> None:
    """Clean every raw map and save the result for the game."""
    for size in MAP_SIZES_M:
        ox.save_graphml(clean_map(load_raw_map(size)), map_path(size))


# Loading (works offline)

def load_graph(path: Path) -> nx.MultiDiGraph:
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Run: python -m engine.maps")
    return ox.load_graphml(path)


def load_raw_map(size_m: int) -> nx.MultiDiGraph:
    """The map exactly as downloaded."""
    return load_graph(raw_map_path(size_m))


def load_map(size_m: int) -> nx.MultiDiGraph:
    """The cleaned map. This is the one the game uses."""
    return load_graph(map_path(size_m))


def describe(graph: nx.MultiDiGraph) -> str:
    """Short summary: intersections, street pieces, total street length."""
    total_km = sum(length for _, _, length in graph.edges(data="length")) / 1000
    return (
        f"{graph.number_of_nodes()} intersections, "
        f"{graph.number_of_edges()} street pieces, {total_km:.0f} km of street"
    )


if __name__ == "__main__":
    if not all(raw_map_path(size).exists() for size in MAP_SIZES_M):
        download_raw_maps()
    save_clean_maps()
    for size in MAP_SIZES_M:
        print(f"{size} m map: {describe(load_raw_map(size))}")
        print(f"  after cleaning: {describe(load_map(size))}")
