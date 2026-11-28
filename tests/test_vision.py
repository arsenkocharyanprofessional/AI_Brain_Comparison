"""Step 2.5 check: fog of war."""

import math

import networkx as nx
import pytest

from engine import rules
from engine.actions import Move
from engine.game import play_tick
from engine.geometry import node_xy
from engine.state import create_state_from_file
from engine.vision import known_map, known_share, point_on_street, ultima_xy


@pytest.fixture
def state():
    return create_state_from_file(1)


def nodes_near(graph, point, radius):
    """Brute force: every intersection within radius of point."""
    return {n for n in graph.nodes if math.dist(node_xy(graph, n), point) <= radius}


def test_bank_starts_knowing_only_the_circle_around_its_vault(state):
    for bank in state.banks:
        vault_xy = node_xy(state.graph, bank.vault.node)
        assert bank.knowledge.seen_nodes == nodes_near(state.graph, vault_xy, rules.VISION_M)


def test_point_on_street_starts_and_ends_at_the_intersections(state):
    graph = state.graph
    for start, end, key, length in list(graph.edges(keys=True, data="length"))[:300]:
        edge = (start, end, key)
        assert math.dist(point_on_street(graph, edge, 0), node_xy(graph, start)) < 0.5
        assert math.dist(point_on_street(graph, edge, length), node_xy(graph, end)) < 0.5


def test_known_map_grows_as_an_ultima_drives_and_covers_what_it_saw(state):
    graph = state.graph
    bank = state.banks[0]
    ultima = bank.ultimas[0]
    target = bank.atms[0].node
    path = nx.shortest_path(graph, ultima.node, target, weight="length")
    expected = set(bank.knowledge.seen_nodes)
    sizes = [len(bank.knowledge.seen_nodes)]
    while not (ultima.node == target and ultima.edge is None):
        play_tick(state, {ultima.id: Move(tuple(path[path.index(ultima.node) + 1:]))})
        expected |= nodes_near(graph, ultima_xy(graph, ultima), rules.VISION_M)
        sizes.append(len(bank.knowledge.seen_nodes))
    assert sizes == sorted(sizes) and sizes[-1] > sizes[0]   # only ever grows
    assert bank.knowledge.seen_nodes == expected             # exactly what was seen
    assert target in bank.knowledge.atm_owner                # ATM discovered
    assert bank.knowledge.atm_owner[target] == 0


def test_knowledge_is_shared_inside_a_bank_only(state):
    graph = state.graph
    bank, rival = state.banks[0], state.banks[1]
    rival_before = set(rival.knowledge.seen_nodes)
    ultima = bank.ultimas[2]
    far = max(graph.nodes, key=lambda n: math.dist(node_xy(graph, n), node_xy(graph, bank.vault.node)))
    path = nx.shortest_path(graph, ultima.node, far, weight="length")
    for _ in range(40):
        play_tick(state, {ultima.id: Move(tuple(path[path.index(ultima.node) + 1:]))})
    assert rival.knowledge.seen_nodes == rival_before


def test_seeing_any_atm_reveals_its_owner(state):
    bank = state.banks[0]
    rival_atm = state.banks[3].atms[0]
    bank.ultimas[0].node = rival_atm.node                    # teleport for the test
    play_tick(state)
    assert bank.knowledge.atm_owner[rival_atm.node] == 3


def test_known_map_only_has_streets_with_both_ends_seen(state):
    bank = state.banks[0]
    roads = known_map(state.graph, bank.knowledge)
    seen = bank.knowledge.seen_nodes
    assert all(u in seen and v in seen for u, v in roads.edges())


def test_knowledge_survives_day_end(state):
    bank = state.banks[0]
    bank.ultimas[0].node = state.banks[2].vault.node         # see somewhere far
    play_tick(state)
    before = set(bank.knowledge.seen_nodes)
    for _ in range(rules.TICKS_PER_DAY):
        play_tick(state)
    assert before <= bank.knowledge.seen_nodes


def test_vision_range_is_a_setup_option():
    short = create_state_from_file(1, vision_m=50)
    normal = create_state_from_file(1)
    assert known_share(short, short.banks[0]) < known_share(normal, normal.banks[0])
