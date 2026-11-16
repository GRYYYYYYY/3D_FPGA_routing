"""Merge same-current cuts; preserve weights and leave owner nets unrestricted."""
from pathlib import Path
from current_resource_bundle_v2 import serialize_request

def compose(sharing,owner):
    for key in ['state','source','objective','seed_order','original_budget','fixed_resource_limits','fixed_target_paths']:
        assert sharing[key]==owner[key],('Mismatched current context',key)
    assert not sharing['fixed_target_paths'] and not owner.get('crossing_reuse_enabled') and not owner.get('domain_failure_release')
    queries={};pins={}
    for role in [sharing,owner]:
        assert {(int(n),p) for n,ps in role['removed_pins'].items() for p in ps}=={(q['net'],q['pin']) for q in role['queries']}
        for q in role['queries']:
            key=q['net'],q['pin']
            if key in queries:assert queries[key]==q,'Conflicting current weights require fresh STA selection'
            queries[key]=q.copy()
        for net,values in role['removed_pins'].items():pins.setdefault(int(net),set()).update(values)
    cuts=[dict(net=n,pins=sorted(ps),ordered_queries=[q for (net,pin),q in queries.items() if net==n]) for n,ps in sorted(pins.items())]
    request,_,ordered=serialize_request(cuts)
    tokens=Path(sharing['crossing_domain']).read_text().split();original=set(map(int,tokens[1:]))
    assert sharing['crossing_reuse_enabled'] and len(original)==int(tokens[0])==len(tokens)-1
    assert original<=set(map(int,sharing['removed_pins']))
    guided=sorted(original-set(map(int,owner['removed_pins'])))
    assert guided and set(guided).isdisjoint(map(int,owner['removed_pins']))
    return dict(request=request,queries=ordered,removed_pins={str(n):sorted(ps) for n,ps in sorted(pins.items())},domain_nets=guided,domain_text=str(len(guided))+'\n'+''.join(str(n)+'\n' for n in guided),shared_nets=sorted(set(map(int,sharing['removed_pins']))&set(map(int,owner['removed_pins']))))
