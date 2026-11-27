"""Place vaults, ATMs and shops on a map.

Vaults: 5 vaults sit on a ring around the center, evenly spaced like the
points of a star. The ring is turned by a random angle (from the seed), so
different layouts put the vaults on different streets.

Shops: 2 shops on opposite sides of the center, on a smaller inner ring.

ATMs: 40 ATMs (8 per bank) dropped at random spots all over the map, then
owners are shuffled so every bank's ATMs are mixed with rivals' ATMs.
"""

import math
import random
from dataclasses import dataclass

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

NUM_SHOPS = 2
# Shop ring radius as a share of the vault ring radius (small map: 500 m)
SHOP_RING_SHARE = 0.5

ATMS_PER_BANK = 8
# An ATM may sit at most this far from its random spot
MAX_ATM_SNAP_M = 150
# No two ATMs closer than this, so they spread out
MIN_ATM_GAP_M = 200
MAX_ATM_TRIES = 20_000


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


# Shops

def place_shops(graph: nx.MultiDiGraph, size_m: int, vaults: list, rng: random.Random) -> list:
    """Pick 2 shop intersections on opposite sides of the center.

    Shops must be well connected and their safe zones must not overlap any
    vault safe zone.
    """
    candidates = [
        n for n in well_connected_nodes(graph)
        if far_from_all(graph, n, vaults, 2 * SAFE_ZONE_RADIUS_M)
    ]
    radius_m = SHOP_RING_SHARE * RING_RADIUS_SHARE * size_m
    for _ in range(MAX_RING_TRIES):
        angle = rng.uniform(0, math.pi)
        spots = [
            (radius_m * math.cos(angle), radius_m * math.sin(angle)),
            (-radius_m * math.cos(angle), -radius_m * math.sin(angle)),
        ]
        shops = [nearest_node(graph, candidates, spot) for spot in spots]
        if all(snap_m <= MAX_SNAP_DISTANCE_M for _, snap_m in shops):
            return [node for node, _ in shops]
    raise RuntimeError(f"Could not place shops on the {size_m} m map")


# ATMs

def far_from_all(graph, node, others: list, min_gap_m: float) -> bool:
    """True if this intersection is at least min_gap_m from every other one."""
    here = node_xy(graph, node)
    return all(distance(here, node_xy(graph, other)) >= min_gap_m for other in others)


def random_spot(size_m: int, rng: random.Random) -> tuple[float, float]:
    """A random point anywhere in the square map, in meters."""
    return rng.uniform(-size_m, size_m), rng.uniform(-size_m, size_m)


def place_atm_spots(graph, size_m: int, protected: list, rng: random.Random) -> list:
    """Pick 40 ATM intersections spread evenly over the whole map.

    Random spots are spread evenly over the area (not over intersections), so
    the dense center does not get all the ATMs. Each spot snaps to the nearest
    intersection. ATMs stay outside safe zones and apart from each other.
    """
    all_nodes = sorted(graph.nodes)
    wanted = NUM_BANKS * ATMS_PER_BANK
    atms = []
    for _ in range(MAX_ATM_TRIES):
        node, snap_m = nearest_node(graph, all_nodes, random_spot(size_m, rng))
        if (
            snap_m <= MAX_ATM_SNAP_M
            and far_from_all(graph, node, protected, SAFE_ZONE_RADIUS_M)
            and far_from_all(graph, node, atms, MIN_ATM_GAP_M)
        ):
            atms.append(node)
            if len(atms) == wanted:
                return atms
    raise RuntimeError(f"Could not place {wanted} ATMs on the {size_m} m map")


def assign_atm_owners(atms: list, rng: random.Random) -> dict:
    """Give each bank 8 ATMs at random, so banks are mixed across the map."""
    owners = [bank for bank in range(NUM_BANKS) for _ in range(ATMS_PER_BANK)]
    rng.shuffle(owners)
    return dict(zip(atms, owners))


# Whole layout

@dataclass
class Layout:
    """Where everything stands on one map. Nodes are OSM intersection ids."""

    size_m: int
    seed: int
    vaults: list        # vaults[bank] = node
    shops: list         # 2 nodes
    atm_owner: dict     # node -> bank

    def atms_of(self, bank: int) -> list:
        return [node for node, owner in self.atm_owner.items() if owner == bank]


def generate_layout(graph: nx.MultiDiGraph, size_m: int, seed: int) -> Layout:
    """Build one layout. The same map, size and seed always give the same layout."""
    rng = random.Random(seed)
    vaults = place_vaults(graph, size_m, rng)
    shops = place_shops(graph, size_m, vaults, rng)
    atms = place_atm_spots(graph, size_m, vaults + shops, rng)
    return Layout(size_m, seed, vaults, shops, assign_atm_owners(atms, rng))
