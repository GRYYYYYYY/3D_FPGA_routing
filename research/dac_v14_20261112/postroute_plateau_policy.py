"""Explicit zero-RC componentwise-delay plateau acceptance factor."""
import math


def decide(native_valid, zero_rc_verified, before_cpd, after_cpd, before_sta,
           after_sta, physical, route_hash, seen_hashes):
    checks=dict(native_valid=bool(native_valid),zero_rc_verified=bool(zero_rc_verified),
                fresh_route=route_hash not in seen_hashes,
                physical_audit=bool(physical.get('passed')),
                other_nets_exact=bool(physical.get('other_net_traces_exact')),
                all_sinks_checked=physical.get('sink_connections',0)>0)
    finite=lambda x:isinstance(x,(int,float)) and math.isfinite(x)
    checks['CPD_nonworse']=finite(before_cpd) and finite(after_cpd) and after_cpd<=before_cpd
    for name in ['sWNS','sTNS','hWNS','hTNS']:
        a,b=before_sta.get(name),after_sta.get(name)
        checks[name+'_nonworse']=finite(a) and finite(b) and b>=a
    changed=physical.get('changed',[])
    checks['one_connection_changed']=len(changed)==1
    checks['physical_componentwise_improvement']=bool(changed) and all(
        finite(r.get('before_ns')) and finite(r.get('after_ns')) and
        0<=r['after_ns']<r['before_ns'] for r in changed)
    accepted=all(checks.values())
    return dict(accepted=accepted,checks=checks,
                kind=('strict_CPD_gain' if after_cpd<before_cpd else 'reported_CPD_plateau') if accepted else 'rejected',
                qualification='Single-connection policy on verified zero-RC inputs only. Other sink delays are unchanged within the physical audit tolerance (1e-12 relative and1e-24seconds absolute). Native printed metrics are compared at their reported precision. A plateau step is not itself a CPD improvement.')
