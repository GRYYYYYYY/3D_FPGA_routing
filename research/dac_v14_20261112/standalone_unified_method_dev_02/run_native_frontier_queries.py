import collections,hashlib,json
def fingerprint(case, mode):
    """Canonical exact solver input; mode0 never reads the occupancy filter."""
    payload = [case['net'], case['pin'], case['sink'], mode, sorted(case['retained']), sorted(((int(n), float(v)) for (n, v) in case['anchors'].items())), sorted(case['blocked']) if mode else []]
    return hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()

def groups(path):
    result = collections.defaultdict(list)
    for line in path.open():
        fields = line.split()
        assert fields[0] in ['RESULT', 'EDGE']
        key = tuple(map(int, fields[1:4]))
        result[key].append(line)
    assert all((lines[0].startswith('RESULT ') for lines in result.values()))
    return result

def write_cases(path, cases):
    with path.open('w') as stream:
        stream.write(str(len(cases)) + '\n')
        for c in cases:
            stream.write(' '.join(map(str, [c['net'], c['pin'], c['sink'], len(c['retained']), len(c['anchors']), len(c['blocked'])])) + '\n')
            stream.write(' '.join(map(str, c['retained'])) + '\n')
            for (node, delay) in sorted(c['anchors'].items(), key=lambda pair: int(pair[0])):
                stream.write(f'{node} {delay:.17g}\n')
            stream.write(' '.join(map(str, c['blocked'])) + '\n')

def make_case(connection, traces, kinds, delays, owners, capacities):
    (net, pin, sink) = (connection['net'], connection['pin'], connection['sink'])
    trace = traces[net]['trace']
    nodes = {n.inode: n for n in trace}
    (parents, switches) = ({}, {})
    children = collections.defaultdict(set)
    for (a, z) in zip(trace, trace[1:]):
        if a.switch == -1:
            continue
        assert z.inode not in parents or parents[z.inode] == a.inode
        parents[z.inode] = a.inode
        switches[a.inode, z.inode] = a.switch
        children[a.inode].add(z.inode)
    (removed, node) = (set(), sink)
    assert not children[sink]
    while node in parents:
        if children[node] - removed or (node != sink and kinds[node] == 'SINK'):
            break
        removed.add(node)
        node = parents[node]
    (retained, root) = (set(nodes) - removed, trace[0].inode)
    (prefixes, stack) = ({root: 0.0}, [root])
    while stack:
        parent = stack.pop()
        for child in children[parent]:
            assert child not in prefixes
            prefixes[child] = prefixes[parent] + delays[switches[parent, child]]
            stack.append(child)
    assert prefixes.keys() == nodes.keys()
    assert any((n.inode == sink and n.pin == pin and (n.kind == 'SINK') for n in trace))
    anchors = {str(n): prefixes[n] for n in sorted(retained) if kinds[n] not in ['SINK', 'IPIN']}
    blocked = {n for (n, cap) in enumerate(capacities) if len(owners.get(n, [])) - int(n in nodes) >= cap}
    assert not retained & blocked
    (original, node) = ([], sink)
    while node in parents:
        original.append(node)
        node = parents[node]
    original.append(node)
    original.reverse()
    at = max((i for (i, n) in enumerate(original) if n in retained))
    assert str(original[at]) in anchors and (not set(original[at:]) & blocked)
    other = {n.inode for n in trace if n.kind == 'SINK' and n.pin is not None and (n.pin != pin)}
    assert other <= retained and sink not in other
    return dict(net=net, pin=pin, sink=sink, root=root, original_nodes=sorted(nodes), retained=sorted(retained), removed=sorted(removed), anchors=anchors, blocked=sorted(blocked), current_physical_seconds=prefixes[sink], original_path=original, other_sinks=sorted(other), tree_edges=[[u, v, sw, delays[sw]] for ((u, v), sw) in switches.items()], anchor_eligibility='Retained SOURCE/OPIN/channel; no IPIN/SINK anchors; same semantics as original capacity reference.', domain='Full-device graph; no single-cross restriction.')
