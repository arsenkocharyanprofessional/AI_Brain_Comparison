"""The template every brain follows.

One brain object plays one bank for the whole week, so anything it stores on
itself (seen enemies, learned fill rates, plans) is kept across days.

Each tick the game calls decide(view) with the bank's view (engine/view.py)
and expects back a dict: Ultima id -> action (Move or Collect from
engine/actions.py). An Ultima left out, or given None, waits this tick.
"""

from engine.view import BankView


class Brain:
    name = "Brain"

    def decide(self, view: BankView) -> dict:
        raise NotImplementedError
