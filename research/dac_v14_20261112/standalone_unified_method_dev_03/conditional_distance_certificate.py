"""Reuse an audited exact relaxed path in a stricter capacity snapshot.

The solver/core/graph provenance must be checked by the caller. A completed
relaxed optimum is also the restricted optimum when the restricted domain is a
subset, its anchors are unchanged, and that witness remains feasible. This is a
conditional zero-RC path statement, never a whole-route/STA acceptance rule.
"""
import math

def certify(relaxed,restricted,answer,switch_delays):
    """Return a conditional equality certificate, or an explicit cache miss."""
    if any(relaxed[k]!=restricted[k] for k in ['net','pin','sink','retained','anchors']):
        return dict(certified=False,reason='Target, retained tree or anchor delays changed')
    if not set(relaxed['blocked'])<=set(restricted['blocked']):
        return dict(certified=False,reason='Restricted search is not a subset of the relaxed domain')
    if answer['stop']!=0 or answer['distance_s']!=answer['lower_s'] or not math.isfinite(answer['distance_s']):
        return dict(certified=False,reason='No completed exact relaxed optimum')
    path=answer['suffix_nodes'];switches=answer['suffix_switches'];retained=set(relaxed['retained'])
    if not path or len(path)!=len(set(path)) or path[-1]!=relaxed['sink'] or str(path[0]) not in relaxed['anchors']:
        return dict(certified=False,reason='Invalid relaxed path endpoints or ancestry')
    if set(path)&retained!={path[0]} or set(path)&set(restricted['blocked']):
        return dict(certified=False,reason='Relaxed optimum witness is infeasible in the restricted snapshot')
    assert len(switches)+1==len(path)
    cost=relaxed['anchors'][str(path[0])]+sum(switch_delays[s] for s in switches)
    assert abs(cost-answer['distance_s'])<1e-23,'Path-cost audit differs from exact-driver result'
    return dict(certified=True,lower_s=answer['lower_s'],upper_s=answer['distance_s'],distance_s=answer['distance_s'],new_queries=0,
                reason='Restricted optimum is bounded below by the exact relaxed optimum and above by the same feasible witness',
                qualification='Conditional path equality under unchanged graph/core/anchors and the explicit capacity filter; no whole-route legality, native STA or acceptance conclusion.')
