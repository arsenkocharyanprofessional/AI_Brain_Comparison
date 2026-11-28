"""The tick loop: how time moves in a game.

A week is 5 days (Monday to Friday) of 600 ticks each. Every tick:
  1. ATMs fill.
  2. Every Ultima's action is resolved, all from the same starting snapshot,
     in this fixed order: shots, handovers, movement, collection, automatic
     vault drop off. (Each phase is added in its own build step.)
  3. Every Ultima looks around, and its bank learns what it sees.
After the last tick of a day comes the day end. After Friday the game is over.
"""

from engine import rules
from engine.actions import Collect, Move
from engine.cash import collect, drop_off
from engine.events import log_event
from engine.movement import move
from engine.state import GameState
from engine.vision import update_knowledge


# Clock

def is_over(state: GameState) -> bool:
    return state.day > rules.DAYS_PER_WEEK


def advance_clock(state: GameState) -> None:
    """Move to the next tick; after the last tick of a day, end the day."""
    if state.tick == rules.TICKS_PER_DAY - 1:
        end_day(state)
    else:
        state.tick += 1


# ATMs

def fill_atms(state: GameState) -> None:
    """Every ATM gains its fill rate, but never goes above the cap."""
    for atm in state.atms_by_node.values():
        atm.cash = min(rules.ATM_CAP, atm.cash + atm.fill_rate)


# Day end

def end_day(state: GameState) -> None:
    """Everyone is teleported home, repaired and reloaded; carried cash is lost.

    ATMs keep their cash overnight and do not fill at night.
    """
    for ultima in all_ultimas(state):
        if ultima.cargo > 0:
            log_event(state, "day_end_loss", ultima=ultima.id, amount=ultima.cargo)
    log_event(state, "day_end", vault_cash=[bank.vault.cash for bank in state.banks])
    for bank in state.banks:
        for ultima in bank.ultimas:
            ultima.node = bank.vault.node
            ultima.edge = None
            ultima.progress_m = 0.0
            ultima.hp = rules.MAX_HP
            ultima.ammo = rules.MAX_AMMO
            ultima.cargo = 0.0
    state.day += 1
    state.tick = 0


# One tick

def all_ultimas(state: GameState):
    for bank in state.banks:
        yield from bank.ultimas


def movement_phase(state: GameState, actions: dict) -> None:
    for ultima in all_ultimas(state):
        action = actions.get(ultima.id)
        if isinstance(action, Move):
            move(state.graph, ultima, action)


def collection_phase(state: GameState, actions: dict) -> None:
    for ultima in all_ultimas(state):
        if isinstance(actions.get(ultima.id), Collect):
            amount = collect(state, ultima)
            log_event(state, "collect", ultima=ultima.id, atm=ultima.node, amount=amount)


def drop_off_phase(state: GameState) -> None:
    for ultima in all_ultimas(state):
        amount = drop_off(state, ultima)
        if amount > 0:
            log_event(state, "deliver", ultima=ultima.id, amount=amount)


def play_tick(state: GameState, actions: dict | None = None) -> None:
    """Play one tick. actions maps an Ultima id to its action for this tick."""
    actions = actions or {}
    fill_atms(state)
    # Shots and handovers come in stage 5.
    movement_phase(state, actions)
    collection_phase(state, actions)
    drop_off_phase(state)
    update_knowledge(state)   # everyone looks around from their new spot
    advance_clock(state)


def play_week(state: GameState, controller=None, recorder=None) -> None:
    """Play the whole week.

    controller(state) returns the actions for the next tick (brains plug in
    here in stage 3). recorder, if given, saves a replay frame after each tick.
    """
    if recorder is not None:
        recorder.record(state)
    while not is_over(state):
        actions = controller(state) if controller is not None else {}
        play_tick(state, actions)
        if recorder is not None:
            recorder.record(state)
