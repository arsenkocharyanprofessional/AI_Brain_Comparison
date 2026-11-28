"""Step 2.3 check: an Ultima driven along a fixed path arrives on time."""

import math

import networkx as nx
import pytest

from engine import rules
from engine.actions import Move
from engine.game import play_tick
from engine.movement import speed_m
from engine.state import create_state_from_file


@pytest.fixture
def state():
    return create_state_from_file(1)


def fixed_route(state):
    """Shortest route from bank 0's vault to bank 2's vault."""
    graph = state.graph
    start = state.banks[0].vault.node
    end = state.banks[2].vault.node
    path = nx.shortest_path(graph, start, end, weight="length")
    length = nx.shortest_path_length(graph, start, end, weight="length")
    return path, length


def remaining_route(ultima, path):
    """What a brain sends: the part of the route after the last node reached."""
    return tuple(path[path.index(ultima.node) + 1:])


def drive_until_arrival(state, ultima, path, max_ticks=1000):
    for tick in range(1, max_ticks + 1):
        play_tick(state, {ultima.id: Move(remaining_route(ultima, path))})
        if ultima.node == path[-1] and ultima.edge is None:
            return tick
    raise AssertionError("never arrived")


def test_empty_ultima_arrives_at_expected_tick(state):
    ultima = state.banks[0].ultimas[0]
    path, length = fixed_route(state)
    expected = math.ceil(length / rules.SPEED_M_PER_TICK)
    assert drive_until_arrival(state, ultima, path) == expected


def test_full_cargo_drives_at_70_percent(state):
    ultima = state.banks[0].ultimas[0]
    ultima.cargo = rules.CARGO_CAPACITY
    assert speed_m(ultima) == pytest.approx(0.7 * rules.SPEED_M_PER_TICK)
    path, length = fixed_route(state)
    expected = math.ceil(length / (0.7 * rules.SPEED_M_PER_TICK))
    assert drive_until_arrival(state, ultima, path) == expected


def test_half_cargo_is_in_between(state):
    ultima = state.banks[0].ultimas[0]
    ultima.cargo = rules.CARGO_CAPACITY / 2
    assert speed_m(ultima) == pytest.approx(0.85 * rules.SPEED_M_PER_TICK)


def test_part_way_along_a_street(state):
    """After one tick the Ultima has driven exactly 25 m along the route."""
    ultima = state.banks[0].ultimas[0]
    path, _ = fixed_route(state)
    play_tick(state, {ultima.id: Move(remaining_route(ultima, path))})
    passed = path[: path.index(ultima.node) + 1]
    driven = nx.path_weight(state.graph, passed, weight="length") + ultima.progress_m
    assert driven == pytest.approx(rules.SPEED_M_PER_TICK)


def test_every_street_can_be_driven_both_ways(state):
    graph = state.graph
    for start, end, length in graph.edges(data="length"):
        reverse_lengths = [d["length"] for d in graph[end][start].values()]
        assert any(abs(r - length) < 0.01 for r in reverse_lengths)


def test_path_must_follow_streets(state):
    graph = state.graph
    ultima = state.banks[0].ultimas[0]
    not_a_neighbor = next(n for n in sorted(graph.nodes)
                          if n != ultima.node and not graph.has_edge(ultima.node, n))
    with pytest.raises(ValueError):
        play_tick(state, {ultima.id: Move((not_a_neighbor,))})


def test_turn_around_mid_street(state):
    graph = state.graph
    u, v = next((u, v) for u, v, length in graph.edges(data="length")
                if length > 3 * rules.SPEED_M_PER_TICK)
    ultima = state.banks[0].ultimas[0]
    ultima.node = u
    play_tick(state, {ultima.id: Move((v,))})          # 25 m towards v
    play_tick(state, {ultima.id: Move((u,))})          # turn around, 25 m back
    assert ultima.node == u and ultima.edge is None


def test_day_end_takes_ultimas_off_the_street(state):
    ultima = state.banks[0].ultimas[0]
    path, _ = fixed_route(state)
    for _ in range(rules.TICKS_PER_DAY):
        play_tick(state, {ultima.id: Move(remaining_route(ultima, path))})
    assert ultima.node == state.banks[0].vault.node
    assert ultima.edge is None and ultima.progress_m == 0
