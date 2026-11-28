"""Stage 1 map checks: the cached maps load offline and are clean."""

import networkx as nx
import pytest

from engine.maps import MAP_SIZES_M, clean_map, load_map, load_raw_map


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_raw_map_loads(size_m):
    graph = load_raw_map(size_m)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_every_point_reaches_every_other(size_m):
    assert nx.is_strongly_connected(load_map(size_m))


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_lengths_in_meters_and_no_loops(size_m):
    graph = load_map(size_m)
    lengths = [length for _, _, length in graph.edges(data="length")]
    assert all(isinstance(length, float) and length > 0 for length in lengths)
    assert nx.number_of_selfloops(graph) == 0


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_saved_clean_map_matches_cleaning_rules(size_m):
    """Guards against someone changing the rules but not re-saving the maps."""
    expected = clean_map(load_raw_map(size_m))
    saved = load_map(size_m)
    assert set(saved.nodes) == set(expected.nodes)
    assert set(saved.edges(keys=True)) == set(expected.edges(keys=True))
