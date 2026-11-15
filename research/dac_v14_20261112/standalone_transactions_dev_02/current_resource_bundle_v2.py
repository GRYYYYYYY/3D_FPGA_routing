"""Uniform distinct-net resource bundles and exact native request serialization."""

def select_cuts(candidates,size,start=0):
    """Take first ranked distinct nets in one current-state rank window."""
    assert isinstance(size,int) and size>0 and isinstance(start,int) and start>=0
    selected=[];nets=set()
    for cut in candidates[start:]:
        if cut['net'] in nets:continue
        assert cut['pins'] and cut['retained_crossing_sources'] and cut['removed_crossing_resources']>0
        selected.append(cut);nets.add(cut['net'])
        if len(selected)==size:break
    return selected


def serialize_request(cuts):
    """Return a free native multi-net transaction and its explicit query order."""
    assert cuts and len({r['net'] for r in cuts})==len(cuts)
    queries=sorted([q for cut in cuts for q in cut['ordered_queries']],key=lambda q:(-q['raw_criticality'],q['net'],q['pin']))
    assert len({(q['net'],q['pin']) for q in queries})==len(queries)
    request=str(len(cuts))+'\n'+''.join(' '.join(map(str,[r['net'],len(r['pins']),*r['pins']]))+'\n' for r in cuts)+'0\n'+str(len(queries))+'\n'+''.join(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\n" for q in queries)
    domain=str(len(cuts))+'\n'+''.join(str(cut['net'])+'\n' for cut in cuts)
    return request,domain,queries
