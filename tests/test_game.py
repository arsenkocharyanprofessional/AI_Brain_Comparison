"""Step 2.2 check: a 5 day run with idle Ultimas."""

import pytest

from engine import rules
from engine.game import is_over, play_tick, play_week
from engine.state import create_state_from_file


def play_one_day(state):
    for _ in range(rules.TICKS_PER_DAY):
        play_tick(state)


def test_clock_moves_through_the_week():
    state = create_state_from_file(1)
    play_one_day(state)
    assert (state.day, state.tick) == (2, 0)
    play_week(state)
    assert is_over(state)
    assert state.day == rules.DAYS_PER_WEEK + 1


def test_atm_cash_after_monday_is_rate_times_ticks_capped():
    state = create_state_from_file(1)
    play_one_day(state)
    for atm in state.atms_by_node.values():
        expected = min(rules.ATM_CAP, atm.fill_rate * rules.TICKS_PER_DAY)
        assert atm.cash == pytest.approx(expected)


def test_idle_week_fills_every_atm_and_leaves_vaults_alone():
    state = create_state_from_file(1)
    play_week(state)
    assert all(atm.cash == rules.ATM_CAP for atm in state.atms_by_node.values())
    assert all(bank.vault.cash == rules.STARTING_VAULT_CASH for bank in state.banks)


def test_day_end_sends_everyone_home_repaired_and_empty():
    state = create_state_from_file(1)
    ultima = state.banks[0].ultimas[0]
    ultima.node = state.banks[1].vault.node   # pretend it drove away
    ultima.hp, ultima.ammo, ultima.cargo = 30, 2, 450.0
    play_one_day(state)
    assert ultima.node == state.banks[0].vault.node
    assert (ultima.hp, ultima.ammo, ultima.cargo) == (rules.MAX_HP, rules.MAX_AMMO, 0.0)
