"""Stage 1 layout checks."""

import itertools
import random

import pytest

from engine.geometry import distance, node_xy
from engine.layout import (
    MIN_VAULT_GAP_M,
    MIN_VAULT_ROAD_COUNT,
    NUM_BANKS,
    place_vaults,
    road_count,
)
from engine.maps import MAP_SIZES_M, load_map

SEEDS = range(20)


@pytest.fixture(scope="module")
def maps():
    return {size: load_map(size) for size in MAP_SIZES_M}


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_vaults_are_far_apart_and_well_connected(maps, size_m):
    graph = maps[size_m]
    for seed in SEEDS:
        vaults = place_vaults(graph, size_m, random.Random(seed))
        assert len(set(vaults)) == NUM_BANKS
        for a, b in itertools.combinations(vaults, 2):
            assert distance(node_xy(graph, a), node_xy(graph, b)) >= MIN_VAULT_GAP_M
        assert all(road_count(graph, v) >= MIN_VAULT_ROAD_COUNT for v in vaults)


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_same_seed_gives_same_vaults(maps, size_m):
    graph = maps[size_m]
    first = place_vaults(graph, size_m, random.Random(7))
    second = place_vaults(graph, size_m, random.Random(7))
    assert first == second
