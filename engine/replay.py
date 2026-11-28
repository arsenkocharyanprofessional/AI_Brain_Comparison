"""Replay files: everything the viewer needs to play a game back.

A replay holds:
  meta    the layout: map size, vault, ATM and shop positions, Ultima ids
  frames  one snapshot after every tick (frame 0 is the start of the game):
          every vault's cash, and for every Ultima its position, HP, ammo
          and cargo
  events  the full event log

Positions are stored as latitude and longitude (6 decimals, about 0.1 m) so
the map in the browser can use them directly. Files are gzip compressed JSON.
"""

import gzip
import io
import json
from pathlib import Path

from engine.geometry import node_xy, to_lonlat
from engine.state import GameState
from engine.vision import ultima_xy


def lat_lon(x: float, y: float) -> list[float]:
    lon, lat = to_lonlat(x, y)
    return [round(lat, 6), round(lon, 6)]


def node_lat_lon(state: GameState, node: int) -> list[float]:
    return lat_lon(*node_xy(state.graph, node))


def game_meta(state: GameState) -> dict:
    return {
        "layout_seed": state.layout.seed,
        "size_m": state.layout.size_m,
        "vaults": [node_lat_lon(state, bank.vault.node) for bank in state.banks],
        "atms": [{"bank": atm.bank, "pos": node_lat_lon(state, atm.node)}
                 for bank in state.banks for atm in bank.atms],
        "shops": [node_lat_lon(state, shop.node) for shop in state.shops],
        "ultimas": [ultima.id for bank in state.banks for ultima in bank.ultimas],
    }


def frame(state: GameState) -> dict:
    """One snapshot. Ultimas are listed in the same order as meta["ultimas"]."""
    ultimas = []
    for bank in state.banks:
        for ultima in bank.ultimas:
            ultimas.append(lat_lon(*ultima_xy(state.graph, ultima))
                           + [ultima.hp, ultima.ammo, round(ultima.cargo, 1)])
    return {
        "vault_cash": [round(bank.vault.cash, 1) for bank in state.banks],
        "ultimas": ultimas,
    }


class Recorder:
    """Collects a frame after every tick; save() writes the replay file."""

    def __init__(self):
        self.frames: list[dict] = []
        self.meta: dict | None = None

    def record(self, state: GameState) -> None:
        if self.meta is None:
            self.meta = game_meta(state)
        self.frames.append(frame(state))

    def save(self, state: GameState, path: Path) -> None:
        replay = {"meta": self.meta, "frames": self.frames, "events": state.events}
        # No time stamp or file name inside the file, so the same game always
        # gives a byte for byte identical file.
        with open(path, "wb") as out:
            with gzip.GzipFile(fileobj=out, mode="wb", mtime=0, filename="") as raw:
                with io.TextIOWrapper(raw, encoding="utf-8") as file:
                    json.dump(replay, file, separators=(",", ":"))


def load_replay(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return json.load(file)
