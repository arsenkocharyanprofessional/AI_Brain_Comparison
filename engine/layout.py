"""Place vaults, ATMs and shops on a map.

Step 1.3: vaults. The 5 vaults sit on a ring around the center, evenly
spaced like the points of a star. The ring is turned by a random angle (from
the seed), so different layouts put the vaults on different streets.
"""

import math
import random

import networkx as nx

from engine.geometry import distance, node_xy

NUM_BANKS = 5

# Ring radius as a share of the map's half side (2000 m map: 1000 m ring)
RING_RADIUS_SHARE = 0.5

# A vault may sit at most this far from its ideal spot on the ring
MAX_SNAP_DISTANCE_M = 250

MIN_VAULT_GAP_M = 800
SAFE_ZONE_RADIUS_M = 100

# "Well connected": at least this many different streets meet here
MIN_VAULT_ROAD_COUNT = 3

MAX_RING_TRIES = 200


def road_count(graph: nx.MultiDiGraph, node) -> int:
    """How many different neighboring intersections touch this one."""
    neighbors = set(graph.successors(node)) | set(graph.predecessors(node))
    neighbors.discard(node)
    return len(neighbors)


def well_connected_nodes(graph: nx.MultiDiGraph) -> list:
    """Intersections where a vault may stand, in a fixed order."""
    return sorted(n for n in graph.nodes if road_count(graph, n) >= MIN_VAULT_ROAD_COUNT)


def ideal_ring_points(radius_m: float, turn_rad: float) -> list[tuple[float, float]]:
    """5 evenly spaced points on a circle around the center."""
    points = []
    for i in range(NUM_BANKS):
        angle = turn_rad + i * 2 * math.pi / NUM_BANKS
        points.append((radius_m * math.cos(angle), radius_m * math.sin(angle)))
    return points


def nearest_node(graph, candidates: list, point: tuple[float, float]):
    """The candidate intersection closest to a point, and how far it is."""
    best = min(candidates, key=lambda n: (distance(node_xy(graph, n), point), n))
    return best, distance(node_xy(graph, best), point)


def vaults_far_enough_apart(graph, vaults: list) -> bool:
    for i, a in enumerate(vaults):
        for b in vaults[i + 1:]:
            if distance(node_xy(graph, a), node_xy(graph, b)) < MIN_VAULT_GAP_M:
                return False
    return True


def try_ring(graph, candidates: list, radius_m: float, turn_rad: float):
    """Snap each ring point to a nearby good intersection, or give up (None)."""
    vaults = []
    for point in ideal_ring_points(radius_m, turn_rad):
        node, snap_m = nearest_node(graph, candidates, point)
        if snap_m > MAX_SNAP_DISTANCE_M:
            return None  # no good street near this spot, e.g. in the gorge
        vaults.append(node)
    if not vaults_far_enough_apart(graph, vaults):
        return None
    return vaults


def place_vaults(graph: nx.MultiDiGraph, size_m: int, rng: random.Random) -> list:
    """Pick 5 vault intersections on a randomly turned ring.

    Tries random turns of the ring until every vault finds a well connected
    intersection close to its ideal spot. Same rng state gives same vaults.
    """
    candidates = well_connected_nodes(graph)
    radius_m = RING_RADIUS_SHARE * size_m
    for _ in range(MAX_RING_TRIES):
        turn_rad = rng.uniform(0, 2 * math.pi / NUM_BANKS)
        vaults = try_ring(graph, candidates, radius_m, turn_rad)
        if vaults is not None:
            return vaults
    raise RuntimeError(f"Could not place vaults on the {size_m} m map")
