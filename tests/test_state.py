"""Step 2.1 check: a game state can be created from a layout file."""

from engine import rules
from engine.state import create_state_from_file


def test_state_from_layout_file():
    state = create_state_from_file(1)
    assert len(state.banks) == rules.NUM_BANKS
    assert len(state.shops) == 2
    assert state.day == 1 and state.tick == 0
    for bank in state.banks:
        assert bank.vault.cash == rules.STARTING_VAULT_CASH
        assert len(bank.atms) == 8
        assert all(atm.cash == 0 and atm.bank == bank.number for atm in bank.atms)
        assert len(bank.ultimas) == rules.ULTIMAS_PER_BANK
        for ultima in bank.ultimas:
            assert ultima.node == bank.vault.node
            assert ultima.hp == rules.MAX_HP and ultima.ammo == rules.MAX_AMMO
            assert ultima.cargo == 0


def test_every_bank_gets_the_same_fill_rates():
    state = create_state_from_file(1)
    rate_sets = [sorted(atm.fill_rate for atm in bank.atms) for bank in state.banks]
    assert all(rates == rate_sets[0] for rates in rate_sets)
    assert all(rules.FILL_RATE_MIN <= r <= rules.FILL_RATE_MAX for r in rate_sets[0])


def test_same_layout_gives_same_state():
    assert create_state_from_file(5) == create_state_from_file(5)


def test_number_of_ultimas_is_a_setup_option():
    state = create_state_from_file(1, ultimas_per_bank=2)
    assert all(len(bank.ultimas) == 2 for bank in state.banks)
