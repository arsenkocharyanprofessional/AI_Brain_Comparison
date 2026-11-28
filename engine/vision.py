"""Fog of war: what each bank knows about the map.

Rules (CLAUDE.md):
* At the start a bank knows nothing of the roads, not even where its own
  ATMs are.
* Every Ultima sees everything within its vision circle (150 m).
* An intersection is known once any Ultima of the bank has seen it.
  A street is known once both of its end intersections are known.
  Brains plan routes only on known streets.
* Seeing an ATM's intersection reveals the ATM and its owner; the same
  for shops.
* Everything one Ultima sees is shared with its whole bank at once, and
  knowledge is kept all week.
"""

import math
from dataclasses import dataclass, field

import networkx as nx

from engine.geometry import node_xy, to_meters


# Where an Ultima is, in meters

def street_points(graph, edge: tuple) -> list[tuple[float, float]]:
    """The street's shape as points in meters, from its start to its end."""
    start, end, key = edge
    data = graph[start][end][key]
    if "geometry" in data:
        return [to_meters(lon, lat) for lon, lat in data["geometry"].coords]
    return [node_xy(graph, start), node_xy(graph, end)]


def point_on_street(graph, edge: tuple, progress_m: float) -> tuple[float, float]:
    """The spot progress_m meters along the street, following its shape."""
    start, end, key = edge
    points = street_points(graph, edge)
    pieces = [math.dist(a, b) for a, b in zip(points, points[1:])]
    # The official length and the drawn shape differ slightly; scale to the shape.
    share = min(1.0, progress_m / graph[start][end][key]["length"])
    to_go = share * sum(pieces)
    for (a, b), piece in zip(zip(points, points[1:]), pieces):
        if to_go <= piece and piece > 0:
            t = to_go / piece
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        to_go -= piece
    return points[-1]


def ultima_xy(graph, ultima) -> tuple[float, float]:
    if ultima.edge is None:
        return node_xy(graph, ultima.node)
    return point_on_street(graph, ultima.edge, ultima.progress_m)


# Fast lookup of intersections near a point

class NodeGrid:
    """Intersections sorted into square cells, so a vision check only looks
    at the few cells around a point instead of every intersection."""

    def __init__(self, graph, cell_m: float):
        self.cell_m = cell_m
        self.cells: dict[tuple[int, int], list] = {}
        for node in sorted(graph.nodes):
            x, y = node_xy(graph, node)
            self.cells.setdefault(self.cell_of(x, y), []).append((node, x, y))

    def cell_of(self, x: float, y: float) -> tuple[int, int]:
        return (math.floor(x / self.cell_m), math.floor(y / self.cell_m))

    def nodes_within(self, point: tuple[float, float], radius_m: float) -> list:
        cx, cy = self.cell_of(*point)
        reach = math.ceil(radius_m / self.cell_m)
        found = []
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                for node, x, y in self.cells.get((cx + dx, cy + dy), []):
                    if math.dist(point, (x, y)) <= radius_m:
                        found.append(node)
        return found


# What a bank knows

@dataclass
class Knowledge:
    seen_nodes: set = field(default_factory=set)
    atm_owner: dict = field(default_factory=dict)   # ATM node -> bank, once seen
    shops: set = field(default_factory=set)


def known_map(graph, knowledge: Knowledge) -> nx.MultiDiGraph:
    """The streets this bank knows: those with both ends seen."""
    return graph.subgraph(knowledge.seen_nodes)


def learn(state, knowledge: Knowledge, nodes: list) -> None:
    shop_nodes = {shop.node for shop in state.shops}
    for node in nodes:
        if node in knowledge.seen_nodes:
            continue
        knowledge.seen_nodes.add(node)
        if node in state.atms_by_node:
            knowledge.atm_owner[node] = state.atms_by_node[node].bank
        if node in shop_nodes:
            knowledge.shops.add(node)


def update_knowledge(state) -> None:
    """Every Ultima looks around; its bank learns what it sees."""
    for bank in state.banks:
        for ultima in bank.ultimas:
            here = ultima_xy(state.graph, ultima)
            learn(state, bank.knowledge, state.node_grid.nodes_within(here, state.vision_m))


def known_share(state, bank) -> float:
    """Share of the map's intersections this bank has seen (0 to 1)."""
    return len(bank.knowledge.seen_nodes) / state.graph.number_of_nodes()
