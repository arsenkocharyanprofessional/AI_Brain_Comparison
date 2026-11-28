"""Collecting cash at ATMs and dropping it off at the vault.

Collect: an Ultima standing at one of its own bank's ATMs takes as much cash
as fits in its free cargo space. This is the Ultima's action for the tick.

Drop off: an Ultima that ends the tick standing at its own vault puts all its
cargo into the vault automatically. It costs no action.
"""

from engine import rules
from engine.state import GameState, Ultima


def standing_at(ultima: Ultima, node: int) -> bool:
    """True if the Ultima stands exactly at this intersection (not mid street)."""
    return ultima.edge is None and ultima.node == node


def free_space(ultima: Ultima) -> float:
    return rules.CARGO_CAPACITY - ultima.cargo


def collect(state: GameState, ultima: Ultima) -> float:
    """Move cash from the ATM into the Ultima. Returns the amount taken."""
    atm = state.atms_by_node.get(ultima.node)
    if ultima.edge is not None or atm is None:
        raise ValueError(f"{ultima.id} is not standing at an ATM")
    if atm.bank != ultima.bank:
        raise ValueError(f"{ultima.id} cannot collect from bank {atm.bank}'s ATM")
    amount = min(atm.cash, free_space(ultima))
    atm.cash -= amount
    ultima.cargo += amount
    return amount


def drop_off(state: GameState, ultima: Ultima) -> float:
    """If the Ultima stands at its own vault, empty its cargo into the vault."""
    vault = state.banks[ultima.bank].vault
    if not standing_at(ultima, vault.node) or ultima.cargo == 0:
        return 0.0
    amount = ultima.cargo
    vault.cash += amount
    ultima.cargo = 0.0
    return amount
