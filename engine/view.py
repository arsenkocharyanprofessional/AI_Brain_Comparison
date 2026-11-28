"""What one bank's brain is allowed to see at the start of a tick.

A brain never gets the game state itself, only its bank's view (CLAUDE.md,
Information and Fog):
* the clock,
* its own vault and its own Ultimas,
* the intersections, streets, ATMs (with owners) and shops its bank has seen,
* every vault's location (public),
* the cash in an own ATM, only while one of its Ultimas stands at it,
* enemy Ultimas inside the vision circle of any of its Ultimas: id, bank,
  position, HP and a rough cargo label (empty, light, heavy).

Hidden from every brain: ATM fill rates, rival ATM cash, rival vault cash
and the exact cargo of enemies.

The view is built from copies, so a brain cannot change the game through it.
"""

from dataclasses import dataclass

import networkx as nx

from engine import rules
from engine.cash import standing_at
from engine.geometry import distance
from engine.state import Bank, GameState, Ultima
from engine.vision import ultima_xy


@dataclass(frozen=True)
class OwnUltima:
    id: str
    node: int                 # last intersection reached
    edge: tuple | None        # street it is on (from, to, key), or None at an intersection
    progress_m: float         # meters driven along that street
    xy: tuple[float, float]   # position in meters
    hp: int
    ammo: int
    cargo: float


@dataclass(frozen=True)
class EnemySighting:
    id: str
    bank: int
    node: int
    edge: tuple | None
    progress_m: float
    xy: tuple[float, float]
    hp: int
    cargo_label: str          # "empty", "light" or "heavy"


@dataclass(frozen=True)
class BankView:
    bank: int
    day: int                  # 1 = Monday ... 5 = Friday
    tick: int                 # tick within the day, 0 to 599
    ticks_left: int           # ticks left today, this one included
    vault_node: int
    vault_cash: float
    vault_nodes: tuple[int, ...]          # every bank's vault, by bank number
    ultimas: tuple[OwnUltima, ...]
    known_nodes: frozenset
    known_map: nx.MultiDiGraph            # read only: streets with both ends seen
    atm_owners: dict                      # ATM node -> owning bank, for ATMs seen
    shops: frozenset
    atm_cash_here: dict                   # own ATM node -> cash, where an own Ultima stands
    enemies: tuple[EnemySighting, ...]


def cargo_label(cargo: float) -> str:
    if cargo == 0:
        return "empty"
    if cargo < rules.HEAVY_CARGO_FROM:
        return "light"
    return "heavy"


def ultima_positions(state: GameState) -> dict:
    """Every Ultima's position in meters, worked out once per tick for all views."""
    return {ultima.id: ultima_xy(state.graph, ultima) for bank in state.banks for ultima in bank.ultimas}


def own_ultima(ultima: Ultima, positions: dict) -> OwnUltima:
    return OwnUltima(ultima.id, ultima.node, ultima.edge, ultima.progress_m,
                     positions[ultima.id], ultima.hp, ultima.ammo, ultima.cargo)


def enemies_in_vision(state: GameState, bank: Bank, positions: dict) -> tuple[EnemySighting, ...]:
    """Every enemy Ultima within vision range of at least one own Ultima."""
    own_spots = [positions[ultima.id] for ultima in bank.ultimas]
    sightings = []
    for other in state.banks:
        if other is bank:
            continue
        for enemy in other.ultimas:
            enemy_xy = positions[enemy.id]
            if any(distance(spot, enemy_xy) <= state.vision_m for spot in own_spots):
                sightings.append(EnemySighting(
                    enemy.id, enemy.bank, enemy.node, enemy.edge, enemy.progress_m,
                    enemy_xy, enemy.hp, cargo_label(enemy.cargo)))
    return tuple(sightings)


def atm_cash_where_standing(state: GameState, bank: Bank) -> dict:
    cash = {}
    for ultima in bank.ultimas:
        atm = state.atms_by_node.get(ultima.node)
        if atm is not None and atm.bank == bank.number and standing_at(ultima, atm.node):
            cash[atm.node] = atm.cash
    return cash


def bank_view(state: GameState, bank: Bank, positions: dict) -> BankView:
    """positions: from ultima_positions(state), at this same moment."""
    knowledge = bank.knowledge
    known_nodes = frozenset(knowledge.seen_nodes)
    return BankView(
        bank=bank.number,
        day=state.day,
        tick=state.tick,
        ticks_left=rules.TICKS_PER_DAY - state.tick,
        vault_node=bank.vault.node,
        vault_cash=bank.vault.cash,
        vault_nodes=tuple(b.vault.node for b in state.banks),
        ultimas=tuple(own_ultima(ultima, positions) for ultima in bank.ultimas),
        known_nodes=known_nodes,
        # A NetworkX subgraph view: streets cannot be added or removed, and it
        # is built from the frozen copy, so it stays fixed even after the bank
        # learns more. shortcut: street data (length, shape) is shared with the
        # real map to save copying, so brains must only read it.
        known_map=state.graph.subgraph(known_nodes),
        atm_owners=dict(knowledge.atm_owner),
        shops=frozenset(knowledge.shops),
        atm_cash_here=atm_cash_where_standing(state, bank),
        enemies=enemies_in_vision(state, bank, positions),
    )
