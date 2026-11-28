"""What a brain can tell an Ultima to do in one tick. One action per tick.

More action types (collect, shoot, hand over) are added in later steps.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    """Drive along this path of intersections, as far as speed allows.

    The first node must be the end of the street the Ultima is on (or, on a
    two way street, the start, to turn around). When standing at an
    intersection, the first node is the next intersection to drive to (a
    path that starts with the current intersection is also accepted).
    Brains may send the whole remaining route every tick.
    """

    path: tuple[int, ...]
