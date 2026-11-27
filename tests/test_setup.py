"""Step 0.1 check: every pinned library imports."""


def test_libraries_import():
    import matplotlib
    import networkx
    import numpy
    import osmnx
    import pandas
    import scipy

    assert osmnx.__version__ and networkx.__version__
