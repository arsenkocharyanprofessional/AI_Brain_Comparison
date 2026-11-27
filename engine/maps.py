"""Download, cache and load the Yerevan road maps.

Each map is a square around Republic Square. "Size" is half the side of the
square, so the 2000 m map covers 4 km x 4 km. Only drivable streets are kept,
and one way streets stay one way.

The biggest map is downloaded once and the smaller squares are cut out of it.
Run once with internet access to create the cached files:
    python -m engine.maps
After that the game loads the maps from data/maps/ and never needs internet.
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


def map_path(size_m: int) -> Path:
    """Where the cached map of this size lives."""
    return MAPS_DIR / f"yerevan_{size_m}m.graphml"


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


def cache_all_maps() -> None:
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
        ox.save_graphml(graph, map_path(size))


def load_map(size_m: int) -> nx.MultiDiGraph:
    """Load a cached map. Works offline."""
    path = map_path(size_m)
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Run: python -m engine.maps")
    return ox.load_graphml(path)


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


def load_clean_map(size_m: int) -> nx.MultiDiGraph:
    """Load a cached map and clean it. This is the map the game uses."""
    return clean_map(load_map(size_m))


def describe(graph: nx.MultiDiGraph) -> str:
    """Short summary: intersections, street pieces, total street length."""
    total_km = sum(length for _, _, length in graph.edges(data="length")) / 1000
    return (
        f"{graph.number_of_nodes()} intersections, "
        f"{graph.number_of_edges()} street pieces, {total_km:.0f} km of street"
    )


if __name__ == "__main__":
    cache_all_maps()
    for size in MAP_SIZES_M:
        print(f"{size} m map: {describe(load_map(size))}")
        print(f"  after cleaning: {describe(load_clean_map(size))}")
