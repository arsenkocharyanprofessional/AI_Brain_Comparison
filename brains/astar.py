"""A* route search on a bank's known map (shared base, used by every brain).

Finds the shortest drive between two intersections using only known streets.
The guide (heuristic) is the straight line distance to the goal, which never
overestimates the real drive, so the route found is always a shortest one.

Every search counts its nodes: one node is one intersection taken from the
open list and expanded. These counts feed the thinking cost metric.
"""

import heapq
from dataclasses import dataclass

from engine.geometry import distance, node_xy

# Map lengths come from OpenStreetMap and positions from our flat meters, so
# a few streets are up to 0.16% shorter than the straight line between their
# ends. Scaling the guide down keeps it a true lower bound on every street
# (tests/test_astar.py checks this on all 3 maps).
GUIDE_SCALE = 0.998


@dataclass(frozen=True)
class Route:
    path: tuple[int, ...]     # intersections from start to goal, both included
    length_m: float


@dataclass(frozen=True)
class SearchResult:
    route: Route | None       # None when the goal cannot be reached on known streets
    nodes_expanded: int


def street_length(graph, start: int, end: int) -> float:
    """Length of the shortest street from start to end (parallel streets exist)."""
    return min(data["length"] for data in graph[start][end].values())


def rebuild_path(came_from: dict, goal: int) -> tuple[int, ...]:
    path = [goal]
    while path[-1] in came_from:
        path.append(came_from[path[-1]])
    return tuple(reversed(path))


def astar(graph, start: int, goal: int) -> SearchResult:
    if start not in graph:
        raise ValueError(f"Route search must start on the known map; {start} is not on it")
    if goal not in graph:
        return SearchResult(None, 0)  # for example a rival vault not seen yet
    goal_xy = node_xy(graph, goal)

    def guide(node: int) -> float:
        return GUIDE_SCALE * distance(node_xy(graph, node), goal_xy)

    best_known = {start: 0.0}       # shortest drive found so far to each intersection
    came_from = {}
    done = set()
    # Entries are (estimated total, order added, node); the order makes ties
    # break the same way every run, so games stay deterministic.
    open_list = [(guide(start), 0, start)]
    added = 1
    expanded = 0

    while open_list:
        _, _, node = heapq.heappop(open_list)
        if node in done:
            continue  # an older, longer entry for a node already finished
        if node == goal:
            route = Route(rebuild_path(came_from, goal), best_known[goal])
            return SearchResult(route, expanded)
        done.add(node)
        expanded += 1
        for neighbor in graph.successors(node):
            if neighbor in done:
                continue
            drive = best_known[node] + street_length(graph, node, neighbor)
            if drive < best_known.get(neighbor, float("inf")):
                best_known[neighbor] = drive
                came_from[neighbor] = node
                heapq.heappush(open_list, (drive + guide(neighbor), added, neighbor))
                added += 1

    return SearchResult(None, expanded)
