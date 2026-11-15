"""Reproduce RouteTree::load_route_tree_Tdel only on an audited zero-RC graph.

This predicts connection delays, never endpoint STA or native route legality.
Intrinsic switch values and each accumulation are rounded to binary32, as in
VPR's float Tarrival/Tdel/Tchild routine. All R/C/Cin/Cout/Cinternal must be zero.
"""
import collections
import numpy as np


def node_delays(tree, *, audited_zero_rc):
    assert audited_zero_rc is True
    root=int(tree['root']);children=collections.defaultdict(list)
    for child,(parent,switch,delay) in tree['edges'].items():
        delay=np.float32(delay)
        assert np.isfinite(delay) and delay>=0
        children[int(parent)].append((int(child),delay))
    values={root:np.float32(0.)};stack=[root]
    with np.errstate(over='raise',invalid='raise'):
        while stack:
            parent=stack.pop()
            for child,delay in children[parent]:
                assert child not in values,'Cycle or multiple timing parents'
                values[child]=np.float32(values[parent]+delay)
                stack.append(child)
    assert set(values)=={root}|{int(n) for n in tree['edges']}
    return {node:float(delay) for node,delay in values.items()}


def sink_delays(tree, *, audited_zero_rc):
    values=node_delays(tree,audited_zero_rc=audited_zero_rc)
    return {int(pin):values[int(sink)] for pin,sink in tree['sinks'].items()}
