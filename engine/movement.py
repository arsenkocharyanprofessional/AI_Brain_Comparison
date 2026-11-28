"""Driving along streets.

An Ultima is either standing at an intersection or part way along a street.
Each tick it may drive up to its speed in meters, following a path of
intersections. If it reaches an intersection with distance to spare, it
continues onto the next street in the same tick. Every street is two way, so
an Ultima can also turn around anywhere.
"""

from engine import rules
from engine.actions import Move
from engine.state import Ultima


def speed_m(ultima: Ultima, capacity: float = rules.CARGO_CAPACITY) -> float:
    """25 m per tick when empty, falling in a straight line to 70% when full."""
    load_share = ultima.cargo / capacity
    slowdown = (1 - rules.FULL_CARGO_SPEED_SHARE) * load_share
    return rules.SPEED_M_PER_TICK * (1 - slowdown)


def shortest_street(graph, start: int, end: int) -> tuple:
    """The street (start, end, key) to use. Two parallel streets: take the shorter."""
    if not graph.has_edge(start, end):
        raise ValueError(f"No street between {start} and {end}")
    key = min(graph[start][end], key=lambda k: (graph[start][end][k]["length"], k))
    return (start, end, key)


def street_length(graph, edge: tuple) -> float:
    start, end, key = edge
    return graph[start][end][key]["length"]


def turn_around(graph, ultima: Ultima) -> None:
    """Drive the current street the other way, keeping the same spot."""
    start, end, _ = ultima.edge
    driven = ultima.progress_m
    ultima.edge = shortest_street(graph, end, start)
    ultima.progress_m = max(0.0, street_length(graph, ultima.edge) - driven)
    ultima.node = end


def move(graph, ultima: Ultima, action: Move) -> None:
    """Drive along the path for one tick."""
    budget = speed_m(ultima)
    path = list(action.path)
    if ultima.edge is None and path and path[0] == ultima.node:
        path.pop(0)  # paths from route search start with the current node

    if ultima.edge is not None and path:
        start, end, _ = ultima.edge
        if path[0] == start:
            turn_around(graph, ultima)
            path.pop(0)
        elif path[0] == end:
            path.pop(0)
        else:
            raise ValueError(f"{ultima.id} is on street {start}->{end}; path must start at one end")

    while budget > 0:
        if ultima.edge is None:
            if not path:
                return  # arrived at the end of the path
            ultima.edge = shortest_street(graph, ultima.node, path.pop(0))
            ultima.progress_m = 0.0
        remaining = street_length(graph, ultima.edge) - ultima.progress_m
        if budget < remaining:
            ultima.progress_m += budget
            return
        budget -= remaining
        ultima.node = ultima.edge[1]   # reached the end of this street
        ultima.edge = None
        ultima.progress_m = 0.0
