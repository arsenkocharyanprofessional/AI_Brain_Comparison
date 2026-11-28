"""The tick loop: how time moves in a game.

A week is 5 days (Monday to Friday) of 600 ticks each. Every tick:
  1. ATMs fill.
  2. Every Ultima's action is resolved, all from the same starting snapshot,
     in this fixed order: shots, handovers, movement, collection, automatic
     vault drop off. (Each phase is added in its own build step.)
After the last tick of a day comes the day end. After Friday the game is over.
"""

from engine import rules
from engine.state import GameState


# Clock

def is_over(state: GameState) -> bool:
    return state.day > rules.DAYS_PER_WEEK


def advance_clock(state: GameState) -> None:
    """Move to the next tick; after the last tick of a day, end the day."""
    state.tick += 1
    if state.tick == rules.TICKS_PER_DAY:
        end_day(state)


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
    for bank in state.banks:
        for ultima in bank.ultimas:
            ultima.node = bank.vault.node
            ultima.hp = rules.MAX_HP
            ultima.ammo = rules.MAX_AMMO
            ultima.cargo = 0.0
    state.day += 1
    state.tick = 0


# One tick

def play_tick(state: GameState) -> None:
    fill_atms(state)
    # Action phases (shots, handovers, movement, collection, drop off)
    # are added in steps 2.3, 2.4 and stage 5.
    advance_clock(state)


def play_week(state: GameState) -> None:
    while not is_over(state):
        play_tick(state)
