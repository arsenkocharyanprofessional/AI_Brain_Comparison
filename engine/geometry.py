"""Turn map coordinates (longitude, latitude) into meters.

Our maps are at most 6 km wide, so a flat approximation around Republic
Square is accurate to well under a meter. Positions in meters make straight
line distances simple: plain Pythagoras.
"""

import math

from engine.maps import CENTER

METERS_PER_DEGREE_LAT = 110_574
METERS_PER_DEGREE_LON = 111_320 * math.cos(math.radians(CENTER[0]))


def to_meters(lon: float, lat: float) -> tuple[float, float]:
    """Position in meters east (x) and north (y) of Republic Square."""
    x = (lon - CENTER[1]) * METERS_PER_DEGREE_LON
    y = (lat - CENTER[0]) * METERS_PER_DEGREE_LAT
    return x, y


def node_xy(graph, node) -> tuple[float, float]:
    """Position of an intersection in meters."""
    data = graph.nodes[node]
    return to_meters(data["x"], data["y"])


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Straight line distance in meters."""
    return math.hypot(a[0] - b[0], a[1] - b[1])
