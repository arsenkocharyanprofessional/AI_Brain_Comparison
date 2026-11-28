"""The event log: a list of everything that happened in a game, in order.

Metrics (cash collected, delivered, lost, and later fights) are counted from
this log after the game. Every event has the day, the tick and a type, plus
details that depend on the type.

Event types so far:
  collect       ultima, atm, amount     cash taken from an ATM
  deliver       ultima, amount          cash dropped off at the vault
  day_end_loss  ultima, amount          cash still carried at day end (lost)
  day_end       vault_cash              every bank's vault cash, by bank
"""

from engine.state import GameState


def log_event(state: GameState, event_type: str, **details) -> None:
    state.events.append({"day": state.day, "tick": state.tick, "type": event_type, **details})
