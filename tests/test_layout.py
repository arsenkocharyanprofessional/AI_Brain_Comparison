"""Stage 1 layout checks."""

import itertools
import random

import pytest

from engine.geometry import distance, node_xy
from engine.layout import (
    ATMS_PER_BANK,
    MIN_ATM_GAP_M,
    MIN_VAULT_GAP_M,
    MIN_VAULT_ROAD_COUNT,
    NUM_BANKS,
    NUM_SHOPS,
    SAFE_ZONE_RADIUS_M,
    far_from_all,
    generate_layout,
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


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_atms_and_shops_follow_the_rules(maps, size_m):
    graph = maps[size_m]
    for seed in SEEDS:
        layout = generate_layout(graph, size_m, seed)
        atms = list(layout.atm_owner)
        assert len(set(atms)) == NUM_BANKS * ATMS_PER_BANK
        assert all(len(layout.atms_of(bank)) == ATMS_PER_BANK for bank in range(NUM_BANKS))
        protected = layout.vaults + layout.shops
        for atm in atms:
            assert far_from_all(graph, atm, protected, SAFE_ZONE_RADIUS_M)
        for a, b in itertools.combinations(atms, 2):
            assert distance(node_xy(graph, a), node_xy(graph, b)) >= MIN_ATM_GAP_M
        assert len(set(layout.shops)) == NUM_SHOPS
        for shop in layout.shops:
            assert far_from_all(graph, shop, layout.vaults, 2 * SAFE_ZONE_RADIUS_M)


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_same_seed_gives_same_layout(maps, size_m):
    graph = maps[size_m]
    assert generate_layout(graph, size_m, 3) == generate_layout(graph, size_m, 3)
