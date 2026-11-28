"""The game state: everything that exists in one game at one moment.

A state is created from a saved layout. Bank numbers are seats: bank 0 owns
vaults[0] and every ATM marked with bank 0. Which brain plays which seat is
decided later, by the game runner.
"""

import random
from dataclasses import dataclass, field

from engine import rules
from engine.layout import Layout, load_layout


@dataclass
class ATM:
    node: int
    bank: int
    fill_rate: float          # hidden from brains: cash added per tick
    cash: float = 0.0         # Monday starts empty


@dataclass
class Vault:
    node: int
    bank: int
    cash: float = rules.STARTING_VAULT_CASH


@dataclass
class Shop:
    node: int


@dataclass
class Ultima:
    id: str                   # for example "B2-U3": bank 2, Ultima 3
    bank: int
    node: int                 # where it stands; starts at its vault
    hp: int = rules.MAX_HP
    ammo: int = rules.MAX_AMMO
    cargo: float = 0.0


@dataclass
class Bank:
    number: int
    vault: Vault
    atms: list[ATM]
    ultimas: list[Ultima]


@dataclass
class GameState:
    layout: Layout
    banks: list[Bank]
    shops: list[Shop]
    day: int = 1              # 1 = Monday ... 5 = Friday
    tick: int = 0             # tick within the day, 0 to 599
    atms_by_node: dict[int, ATM] = field(default_factory=dict)


def draw_fill_rates(layout: Layout) -> list[list[float]]:
    """One set of 8 rates per layout, given to every bank in its own order.

    All banks get exactly the same rates, so they have identical income
    potential. Rates come from the layout seed only, so all 5 rotations of a
    layout see the same rates in the same seats.
    """
    rng = random.Random(f"fill-rates-{layout.seed}")
    atms_per_bank = len(layout.atms_of(0))
    rate_set = [rng.uniform(rules.FILL_RATE_MIN, rules.FILL_RATE_MAX) for _ in range(atms_per_bank)]
    per_bank = []
    for _ in range(len(layout.vaults)):
        rates = rate_set[:]
        rng.shuffle(rates)
        per_bank.append(rates)
    return per_bank


def create_bank(layout: Layout, number: int, rates: list[float], ultimas_per_bank: int) -> Bank:
    vault_node = layout.vaults[number]
    atms = [ATM(node, number, rate) for node, rate in zip(layout.atms_of(number), rates)]
    ultimas = [Ultima(f"B{number}-U{i}", number, vault_node) for i in range(ultimas_per_bank)]
    return Bank(number, Vault(vault_node, number), atms, ultimas)


def create_state(layout: Layout, ultimas_per_bank: int = rules.ULTIMAS_PER_BANK) -> GameState:
    """A fresh Monday morning game on this layout."""
    rates = draw_fill_rates(layout)
    banks = [create_bank(layout, n, rates[n], ultimas_per_bank) for n in range(len(layout.vaults))]
    state = GameState(layout, banks, [Shop(node) for node in layout.shops])
    state.atms_by_node = {atm.node: atm for bank in banks for atm in bank.atms}
    return state


def create_state_from_file(layout_number: int, ultimas_per_bank: int = rules.ULTIMAS_PER_BANK) -> GameState:
    return create_state(load_layout(layout_number), ultimas_per_bank)
