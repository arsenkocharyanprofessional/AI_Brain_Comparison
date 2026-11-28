"""Step 3.1 check: the brain interface (what a brain sees, what it returns)."""

import dataclasses

import networkx as nx
import pytest

from brains.base import Brain
from engine import rules
from engine.actions import Collect, Move
from engine.game import is_over, play_tick
from engine.runner import brain_controller, play_game
from engine.state import create_state_from_file
from engine.view import BankView, EnemySighting, cargo_label


class IdleBrain(Brain):
    """The "do nothing" brain: never gives an order. Used only in tests."""

    name = "Idle"

    def __init__(self):
        self.views = []

    def decide(self, view):
        self.views.append(view)
        return {}


class FixedOrdersBrain(Brain):
    """Gives the same orders every tick."""

    def __init__(self, orders):
        self.orders = orders

    def decide(self, view):
        return self.orders


class RouteBrain(Brain):
    """Drives one Ultima along a fixed route, sending what is left of it each tick."""

    def __init__(self, ultima_id, route):
        self.ultima_id = ultima_id
        self.route = list(route)

    def decide(self, view):
        me = next(ultima for ultima in view.ultimas if ultima.id == self.ultima_id)
        heading_to = me.node if me.edge is None else me.edge[1]
        remaining = self.route[self.route.index(heading_to):]
        return {self.ultima_id: Move(tuple(remaining))}


@pytest.fixture
def state():
    return create_state_from_file(1)


def view_of(state, bank_number):
    """The view bank_number's brain would get right now."""
    brain = IdleBrain()
    others = [IdleBrain() for _ in state.banks]
    others[bank_number] = brain
    brain_controller(others)(state)
    return brain.views[0]


# A full game

def test_five_do_nothing_brains_play_a_full_week(state):
    brains = [IdleBrain() for _ in state.banks]
    play_game(state, brains)
    assert is_over(state)
    total_ticks = rules.DAYS_PER_WEEK * rules.TICKS_PER_DAY
    for number, brain in enumerate(brains):
        assert len(brain.views) == total_ticks
        assert {view.bank for view in brain.views} == {number}
        clock = [(view.day, view.tick) for view in brain.views]
        assert clock[0] == (1, 0) and clock[-1] == (rules.DAYS_PER_WEEK, rules.TICKS_PER_DAY - 1)
    assert all(bank.vault.cash == rules.STARTING_VAULT_CASH for bank in state.banks)


def test_view_clock_and_own_bank(state):
    view = view_of(state, 2)
    bank = state.banks[2]
    assert (view.day, view.tick, view.ticks_left) == (1, 0, rules.TICKS_PER_DAY)
    assert view.vault_node == bank.vault.node
    assert view.vault_cash == rules.STARTING_VAULT_CASH
    assert view.vault_nodes == tuple(b.vault.node for b in state.banks)
    assert [u.id for u in view.ultimas] == [u.id for u in bank.ultimas]
    assert view.known_nodes == bank.knowledge.seen_nodes
    assert set(view.known_map.nodes) == bank.knowledge.seen_nodes


# Hidden information

def field_names(cls):
    return {field.name for field in dataclasses.fields(cls)}


def test_view_holds_exactly_the_allowed_information():
    """A whitelist: adding anything to the view must be a conscious change here."""
    assert field_names(BankView) == {
        "bank", "day", "tick", "ticks_left", "vault_node", "vault_cash", "vault_nodes",
        "ultimas", "known_nodes", "known_map", "atm_owners", "shops", "atm_cash_here", "enemies"}
    # Enemies: no exact cargo, ammo or fill rates, only a rough cargo label.
    assert field_names(EnemySighting) == {
        "id", "bank", "node", "edge", "progress_m", "xy", "hp", "cargo_label"}


def test_own_atm_cash_only_while_standing_at_it(state):
    bank = state.banks[0]
    own_atm = bank.atms[0]
    rival_atm = state.banks[1].atms[0]
    own_atm.cash, rival_atm.cash = 123.0, 77.0
    assert view_of(state, 0).atm_cash_here == {}

    bank.ultimas[0].node = own_atm.node
    bank.ultimas[1].node = rival_atm.node
    assert view_of(state, 0).atm_cash_here == {own_atm.node: 123.0}


def test_view_is_a_copy_the_brain_cannot_change_the_game(state):
    view = view_of(state, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.vault_cash = 10**6
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.ultimas[0].cargo = 600
    with pytest.raises(nx.NetworkXError):
        view.known_map.add_edge(1, 2)
    view.atm_owners[123] = 0
    assert 123 not in state.banks[0].knowledge.atm_owner


def test_view_does_not_grow_when_the_bank_learns_more(state):
    view = view_of(state, 0)
    before = len(view.known_map)
    state.banks[0].knowledge.seen_nodes.update(state.graph.nodes)
    assert len(view.known_map) == before


# Enemies in vision

def test_enemy_near_an_own_ultima_is_seen_with_a_rough_cargo_label(state):
    enemy = state.banks[1].ultimas[0]
    enemy.node = state.banks[0].vault.node   # parked right next to bank 0's Ultimas
    enemy.cargo, enemy.hp = 450.0, 80
    seen = view_of(state, 0).enemies
    assert len(seen) == 1
    sighting = seen[0]
    assert (sighting.id, sighting.bank, sighting.hp, sighting.cargo_label) == (enemy.id, 1, 80, "heavy")
    assert sighting.node == enemy.node


def test_enemies_far_away_are_not_seen(state):
    # At the start every Ultima is at its own vault, at least 800 m apart.
    for bank in state.banks:
        assert view_of(state, bank.number).enemies == ()


def test_cargo_labels():
    assert cargo_label(0) == "empty"
    assert cargo_label(0.5) == "light"
    assert cargo_label(299.9) == "light"
    assert cargo_label(300) == "heavy"
    assert cargo_label(600) == "heavy"


# Orders

def test_a_move_order_is_carried_out(state):
    bank = state.banks[0]
    ultima = bank.ultimas[0]
    known = state.graph.subgraph(bank.knowledge.seen_nodes)
    paths = nx.single_source_dijkstra_path(known, bank.vault.node, weight="length")
    target, path = max(paths.items(), key=lambda item: len(item[1]))
    controller = brain_controller([RouteBrain(ultima.id, path)] + [IdleBrain() for _ in range(4)])
    for _ in range(100):
        play_tick(state, controller(state))
    assert (ultima.node, ultima.edge) == (target, None)


def test_order_for_another_banks_ultima_is_refused(state):
    rival_id = state.banks[1].ultimas[0].id
    brains = [FixedOrdersBrain({rival_id: None})] + [IdleBrain() for _ in range(4)]
    with pytest.raises(ValueError, match="not its Ultima"):
        brain_controller(brains)(state)


def test_move_to_unseen_intersections_is_refused(state):
    bank = state.banks[0]
    unseen = next(node for node in state.graph.nodes if node not in bank.knowledge.seen_nodes)
    brains = [FixedOrdersBrain({bank.ultimas[0].id: Move((unseen,))})] + [IdleBrain() for _ in range(4)]
    with pytest.raises(ValueError, match="not seen"):
        brain_controller(brains)(state)


def test_unknown_action_is_refused(state):
    brains = [FixedOrdersBrain({state.banks[0].ultimas[0].id: "shoot"})] + [IdleBrain() for _ in range(4)]
    with pytest.raises(ValueError, match="unknown action"):
        brain_controller(brains)(state)


def test_collect_away_from_an_own_atm_is_refused(state):
    brains = [FixedOrdersBrain({state.banks[0].ultimas[0].id: Collect()})] + [IdleBrain() for _ in range(4)]
    with pytest.raises(ValueError, match="not standing at an ATM"):
        play_tick(state, brain_controller(brains)(state))


def test_each_bank_needs_its_own_brain_and_the_right_count(state):
    shared = IdleBrain()
    with pytest.raises(ValueError, match="its own brain"):
        play_game(state, [shared] * 5)
    with pytest.raises(ValueError, match="Need 5 brains"):
        play_game(state, [IdleBrain()])
