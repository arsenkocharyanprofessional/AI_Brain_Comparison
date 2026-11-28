"""Step 2.4 check: a scripted Ultima empties an ATM and fills its vault."""

import networkx as nx
import pytest

from engine import rules
from engine.actions import Collect, Move
from engine.game import play_tick
from engine.state import create_state_from_file


@pytest.fixture
def state():
    return create_state_from_file(1)


def drive_to(state, ultima, target, max_ticks=500):
    """Drive along the shortest route until standing at target."""
    path = nx.shortest_path(state.graph, ultima.node, target, weight="length")
    for _ in range(max_ticks):
        if ultima.node == target and ultima.edge is None:
            return
        remaining = tuple(path[path.index(ultima.node) + 1:])
        play_tick(state, {ultima.id: Move(remaining)})
    raise AssertionError("never arrived")


def test_scripted_ultima_moves_atm_cash_into_its_vault(state):
    bank = state.banks[0]
    ultima = bank.ultimas[0]
    atm = bank.atms[0]
    drive_to(state, ultima, atm.node)
    cash_before_collect = atm.cash + atm.fill_rate        # the tick starts by filling
    play_tick(state, {ultima.id: Collect()})
    collected = ultima.cargo
    assert collected == pytest.approx(min(rules.ATM_CAP, cash_before_collect))
    assert atm.cash == 0
    vault_before = bank.vault.cash
    drive_to(state, ultima, bank.vault.node)
    assert ultima.cargo == 0
    assert bank.vault.cash == pytest.approx(vault_before + collected)


def test_collect_is_limited_by_free_cargo_space(state):
    bank = state.banks[0]
    ultima = bank.ultimas[0]
    atm = bank.atms[0]
    ultima.node = atm.node
    ultima.cargo = 450.0
    atm.cash = 300.0 - atm.fill_rate                      # 300 after this tick's filling
    play_tick(state, {ultima.id: Collect()})
    assert ultima.cargo == pytest.approx(rules.CARGO_CAPACITY)
    assert atm.cash == pytest.approx(150.0)


def test_cannot_collect_from_a_rival_atm(state):
    ultima = state.banks[0].ultimas[0]
    ultima.node = state.banks[1].atms[0].node
    with pytest.raises(ValueError):
        play_tick(state, {ultima.id: Collect()})


def test_cannot_collect_away_from_an_atm(state):
    ultima = state.banks[0].ultimas[0]       # standing at its vault
    with pytest.raises(ValueError):
        play_tick(state, {ultima.id: Collect()})


def test_drop_off_needs_no_action_and_only_at_own_vault(state):
    bank = state.banks[0]
    ultima = bank.ultimas[0]
    ultima.cargo = 200.0
    ultima.node = state.banks[1].vault.node   # a rival's vault: nothing happens
    play_tick(state)
    assert ultima.cargo == 200.0 and bank.vault.cash == rules.STARTING_VAULT_CASH
    ultima.node = bank.vault.node             # own vault: dropped off with no action
    play_tick(state)
    assert ultima.cargo == 0 and bank.vault.cash == rules.STARTING_VAULT_CASH + 200
