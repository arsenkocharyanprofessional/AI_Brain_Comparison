"""Step 1.1 check: the three cached maps load offline."""

import pytest

from engine.maps import MAP_SIZES_M, load_map


@pytest.mark.parametrize("size_m", MAP_SIZES_M)
def test_cached_map_loads(size_m):
    graph = load_map(size_m)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0
