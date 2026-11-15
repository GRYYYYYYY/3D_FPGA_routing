"""Use exact unsigned lookup keys without copying a complete sorted edge array."""
import numpy as np


def edge_row_bounds(edges, node_count, switch_stride, source):
    source = int(source)
    assert edges.dtype.kind == 'u' and 0 <= source < node_count
    row_width = int(node_count)*int(switch_stride)
    keys = np.array([source*row_width, (source+1)*row_width], dtype=edges.dtype)
    return edges.searchsorted(keys)
