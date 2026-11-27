"""Download, cache and load the Yerevan road maps.

Each map is a square around Republic Square. "Size" is half the side of the
square, so the 2000 m map covers 4 km x 4 km. Only drivable streets are kept,
and one way streets stay one way.

Run once with internet access to create the cached files:
    python -m engine.maps
After that the game loads the maps from data/maps/ and never needs internet.
Map data from OpenStreetMap contributors.
"""

from pathlib import Path

import networkx as nx
import osmnx as ox

# Republic Square, Yerevan (latitude, longitude)
CENTER = (40.1777, 44.5126)

# Half side of each square map, in meters
MAP_SIZES_M = (2000, 2500, 3000)

MAPS_DIR = Path(__file__).resolve().parent.parent / "data" / "maps"


def map_path(size_m: int) -> Path:
    """Where the cached map of this size lives."""
    return MAPS_DIR / f"yerevan_{size_m}m.graphml"


def download_map(size_m: int) -> nx.MultiDiGraph:
    """Download the drivable streets in a square around the center."""
    return ox.graph_from_point(
        CENTER, dist=size_m, dist_type="bbox", network_type="drive", simplify=True
    )


def cache_map(size_m: int) -> Path:
    """Download one map and save it to data/maps/."""
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    graph = download_map(size_m)
    path = map_path(size_m)
    ox.save_graphml(graph, path)
    return path


def load_map(size_m: int) -> nx.MultiDiGraph:
    """Load a cached map. Works offline."""
    path = map_path(size_m)
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing. Run: python -m engine.maps")
    return ox.load_graphml(path)


def describe(graph: nx.MultiDiGraph) -> str:
    """Short summary: intersections, street pieces, total street length."""
    total_km = sum(length for _, _, length in graph.edges(data="length")) / 1000
    return (
        f"{graph.number_of_nodes()} intersections, "
        f"{graph.number_of_edges()} street pieces, {total_km:.0f} km of street"
    )


if __name__ == "__main__":
    for size in MAP_SIZES_M:
        print(f"Downloading {size} m map ...")
        cache_map(size)
    for size in MAP_SIZES_M:
        print(f"{size} m map: {describe(load_map(size))}")
