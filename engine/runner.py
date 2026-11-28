"""Play a game with one brain per bank.

Every tick, all 5 views are built first, from the same moment of the game,
and only then do the brains decide. So no brain can react to another
brain's orders of the same tick (ticks are simultaneous).

Every order is checked before the tick is played. Our brains are our own
code, so an order that breaks the rules is a bug: the game stops with a
clear error instead of quietly ignoring it.
"""

from engine.actions import Collect, Move
from engine.game import play_week
from engine.state import Bank, GameState
from engine.view import bank_view, ultima_positions

ALLOWED_ACTIONS = (Move, Collect)


def check_orders(bank: Bank, orders: dict) -> None:
    own_ids = {ultima.id for ultima in bank.ultimas}
    for ultima_id, action in orders.items():
        if ultima_id not in own_ids:
            raise ValueError(f"Bank {bank.number} gave an order to {ultima_id}, which is not its Ultima")
        if action is None:
            continue  # wait
        if not isinstance(action, ALLOWED_ACTIONS):
            raise ValueError(f"{ultima_id} got an unknown action: {action!r}")
        if isinstance(action, Move):
            unknown = [node for node in action.path if node not in bank.knowledge.seen_nodes]
            if unknown:
                raise ValueError(f"{ultima_id} was sent to intersections its bank has not seen: {unknown}")
        # Collecting away from an own ATM is refused by engine/cash.py.


def brain_controller(brains: list):
    """The function play_week calls each tick to get every Ultima's action."""

    def controller(state: GameState) -> dict:
        positions = ultima_positions(state)
        views = [bank_view(state, bank, positions) for bank in state.banks]
        actions = {}
        for bank, brain, view in zip(state.banks, brains, views):
            orders = brain.decide(view) or {}
            check_orders(bank, orders)
            actions.update(orders)
        return actions

    return controller


def play_game(state: GameState, brains: list, recorder=None) -> None:
    """Play the whole week. brains[n] plays bank n (seat n)."""
    if len(brains) != len(state.banks):
        raise ValueError(f"Need {len(state.banks)} brains, got {len(brains)}")
    if len({id(brain) for brain in brains}) != len(brains):
        # One object in two seats would share its memory between two banks.
        raise ValueError("Each bank needs its own brain object")
    play_week(state, brain_controller(brains), recorder)
