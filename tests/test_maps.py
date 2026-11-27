"""Step 1.1 check: the three cached maps load offline."""

import networkx as nx
import pytest

from engine.maps import MAP_SIZES_M, load_clean_map, load_map


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_cached_map_loads(size_m):
    graph = load_map(size_m)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_clean_map_every_point_reaches_every_other(size_m):
    graph = load_clean_map(size_m)
    assert nx.is_strongly_connected(graph)


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_clean_map_has_lengths_in_meters_and_no_loops(size_m):
    graph = load_clean_map(size_m)
    lengths = [length for _, _, length in graph.edges(data="length")]
    assert all(isinstance(length, float) and length > 0 for length in lengths)
    assert nx.number_of_selfloops(graph) == 0
