"""Step 2.6 check: one game produces a replay file we can read back."""

import networkx as nx
import pytest

from engine import rules
from engine.actions import Collect, Move
from engine.game import play_week
from engine.replay import Recorder, load_replay
from engine.state import create_state_from_file

TOTAL_TICKS = rules.DAYS_PER_WEEK * rules.TICKS_PER_DAY


def shuttle_controller(state):
    """Test script: each bank's first Ultima shuttles between its first ATM
    and its vault (it may use the full map; real brains will not)."""
    actions = {}
    for bank in state.banks:
        ultima = bank.ultimas[0]
        atm = bank.atms[0].node
        goal = bank.vault.node if ultima.cargo > 0 else atm
        if ultima.edge is None and ultima.node == atm and ultima.cargo == 0:
            actions[ultima.id] = Collect()
            continue
        here = ultima.node if ultima.edge is None else ultima.edge[1]
        path = nx.shortest_path(state.graph, here, goal, weight="length")
        actions[ultima.id] = Move(tuple(path[1:] if ultima.edge is None else path))
    return actions


def play_recorded_game(path):
    state = create_state_from_file(1)
    recorder = Recorder()
    play_week(state, shuttle_controller, recorder)
    recorder.save(state, path)
    return state


@pytest.fixture(scope="module")
def game(tmp_path_factory):
    path = tmp_path_factory.mktemp("replays") / "game.json.gz"
    state = play_recorded_game(path)
    return state, path, load_replay(path)


def test_replay_has_a_frame_per_tick_and_the_layout(game):
    state, _, replay = game
    assert len(replay["frames"]) == TOTAL_TICKS + 1
    assert len(replay["meta"]["vaults"]) == rules.NUM_BANKS
    assert len(replay["meta"]["atms"]) == rules.NUM_BANKS * 8
    assert len(replay["meta"]["ultimas"]) == rules.NUM_BANKS * rules.ULTIMAS_PER_BANK
    assert all(len(f["ultimas"]) == len(replay["meta"]["ultimas"]) for f in replay["frames"])


def test_final_frame_matches_the_game(game):
    state, _, replay = game
    last = replay["frames"][-1]
    assert last["vault_cash"] == [round(bank.vault.cash, 1) for bank in state.banks]


def test_events_add_up(game):
    state, _, replay = game
    events = replay["events"]
    collected = sum(e["amount"] for e in events if e["type"] == "collect")
    delivered = sum(e["amount"] for e in events if e["type"] == "deliver")
    lost = sum(e["amount"] for e in events if e["type"] == "day_end_loss")
    assert collected > 0
    assert collected == pytest.approx(delivered + lost)
    gained = sum(bank.vault.cash - rules.STARTING_VAULT_CASH for bank in state.banks)
    assert delivered == pytest.approx(gained)
    day_ends = [e for e in events if e["type"] == "day_end"]
    assert [e["day"] for e in day_ends] == [1, 2, 3, 4, 5]
    assert all(e["tick"] == rules.TICKS_PER_DAY - 1 for e in day_ends)


def test_same_game_gives_identical_file(game, tmp_path):
    _, first_path, _ = game
    second_path = tmp_path / "again.json.gz"
    play_recorded_game(second_path)
    assert first_path.read_bytes() == second_path.read_bytes()
