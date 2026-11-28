"""Step 3.2 check: A* route search on the known map."""

import math
import random

import networkx as nx
import pytest

from brains.astar import GUIDE_SCALE, astar, street_length
from engine.geometry import node_xy
from engine.maps import load_map
from engine.state import create_state_from_file

MAP_SIZES = (2000, 2500, 3000)


@pytest.fixture(scope="module", params=MAP_SIZES)
def graph(request):
    return load_map(request.param)


def random_pairs(graph, count, seed):
    rng = random.Random(seed)
    nodes = sorted(graph.nodes)
    return [(rng.choice(nodes), rng.choice(nodes)) for _ in range(count)]


def test_guide_never_overestimates_any_street(graph):
    for start, end, length in graph.edges(data="length"):
        straight = math.dist(node_xy(graph, start), node_xy(graph, end))
        assert GUIDE_SCALE * straight <= length


def test_routes_match_networkx_shortest_paths(graph):
    for start, goal in random_pairs(graph, 300, seed=1):
        result = astar(graph, start, goal)
        expected = nx.shortest_path_length(graph, start, goal, weight="length")
        assert result.route.length_m == pytest.approx(expected, abs=1e-6)


def test_route_is_a_real_drive_with_the_stated_length(graph):
    for start, goal in random_pairs(graph, 100, seed=2):
        route = astar(graph, start, goal).route
        assert route.path[0] == start and route.path[-1] == goal
        driven = sum(street_length(graph, a, b) for a, b in zip(route.path, route.path[1:]))
        assert driven == pytest.approx(route.length_m)


def test_same_start_and_goal_is_an_empty_drive(graph):
    node = min(graph.nodes)
    result = astar(graph, node, node)
    assert (result.route.path, result.route.length_m, result.nodes_expanded) == ((node,), 0.0, 0)


def test_expands_no_more_nodes_than_a_search_without_the_guide(graph):
    """A search without a guide (Dijkstra) expands every node closer than the goal."""
    for start, goal in random_pairs(graph, 50, seed=3):
        expanded = astar(graph, start, goal).nodes_expanded
        drive = nx.single_source_dijkstra_path_length(graph, start, weight="length")
        not_farther_than_goal = sum(1 for node in drive if node != goal and drive[node] <= drive[goal])
        assert expanded <= not_farther_than_goal


def test_search_uses_only_the_known_map():
    state = create_state_from_file(1)
    bank = state.banks[0]
    known = state.graph.subgraph(bank.knowledge.seen_nodes)
    for node in sorted(known.nodes)[:50]:
        route = astar(known, bank.vault.node, node).route
        if route is not None:
            assert set(route.path) <= bank.knowledge.seen_nodes


def test_unseen_goal_has_no_route_and_unseen_start_is_an_error():
    state = create_state_from_file(1)
    bank = state.banks[0]
    known = state.graph.subgraph(bank.knowledge.seen_nodes)
    rival_vault = state.banks[1].vault.node
    assert astar(known, bank.vault.node, rival_vault).route is None
    with pytest.raises(ValueError, match="known map"):
        astar(known, rival_vault, bank.vault.node)


def test_goal_seen_but_not_connected_has_no_route():
    graph = nx.MultiDiGraph()
    for node, x in ((1, 44.51), (2, 44.511), (3, 44.52)):
        graph.add_node(node, x=x, y=40.18)
    graph.add_edge(1, 2, length=90.0)
    graph.add_edge(2, 1, length=90.0)
    result = astar(graph, 1, 3)
    assert result.route is None and result.nodes_expanded == 2
