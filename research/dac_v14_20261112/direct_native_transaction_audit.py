"""Audit actual fused route trees without constructing another serialized candidate.

This checks scope/edges/capacity, not timing acceptance or independent physical
resource accounting. It never changes the ordered native route used for search.
"""
import collections
from itertools import zip_longest
from pathlib import Path
import time

from coordinated_repair_tree import from_trace, nodes, prefixes, prune_sinks
from immutable_rr_audit_cache import GraphAuditCache
from retained_prefix_workflow import read, sha, write


def parse_transaction(text, expected_queries):
    rows = [line.split() for line in text.splitlines()]
    assert rows and rows[-1][0] == 'COMPLETE' and rows[-1][-1] == 'occupancy_restored'
    last = rows[-1]
    assert len(last) == 6 and last[1] in ['0', '1']
    kept = collections.defaultdict(set)
    raw = collections.defaultdict(list)
    queries, attempts = [], []
    for row in rows[:-1]:
        tag = row[0]
        if tag == 'KEEP':
            net, node = map(int, row[1:3])
            assert node not in kept[net], 'Repeated retained node'
            kept[net].add(node)
        elif tag == 'NODE':
            raw[int(row[1])].append((int(row[2]), int(row[3]), int(row[4]), int(row[5]), float(row[6])))
        elif tag == 'QUERY':
            queries.append(dict(net=int(row[1]), pin=int(row[2]), feasible=bool(int(row[3])),
                criticality=float(row[4]), pushes=int(row[5]), pops=int(row[6]), seconds=float(row[7])))
        elif tag == 'ATTEMPT':
            attempts.append(dict(net=int(row[1]), pin=int(row[2]), pressure=float(row[3]),
                                 found=bool(int(row[4])), feasible=bool(int(row[5]))))
        else:
            assert tag in ['FAIL_TARGET', 'FAIL_EDGE', 'OCC', 'MODE', 'DOMAIN_RELEASE'], tag
    expected = [(q['net'], q['pin']) for q in expected_queries]
    actual = [(q['net'], q['pin']) for q in queries]
    assert actual == expected[:len(actual)], 'Actual query scope/order differs'
    succeeded = last[1] == '1'
    if succeeded:
        assert int(last[2]) == int(last[3]) == len(expected) == len(queries)
        assert all(q['feasible'] for q in queries)
    return dict(succeeded=succeeded, kept=dict(kept), raw=dict(raw), queries=queries,
                attempts=attempts, native_transaction_seconds=float(last[4]))


def check_scope(original, candidate, logged_rows, retained_nodes, removed_pins, switches):
    """Check terminals, retained edges and actual/logged replacement in one tree."""
    retained = prune_sinks(original, removed_pins)
    assert retained_nodes == nodes(retained), 'Native pruning differs from requested scope'
    roots = [node for node, parent, sw, pin, delay in logged_rows if parent < 0]
    assert roots == [original['root']]
    assert len({row[0] for row in logged_rows}) == len(logged_rows), 'Repeated native NODE'
    logged = dict(root=roots[0],
        edges={node: (parent, sw, switches[sw]) for node, parent, sw, pin, delay in logged_rows if parent >= 0},
        sinks={pin: node for node, parent, sw, pin, delay in logged_rows if pin > 0})
    assert len(logged['sinks']) == sum(row[3] > 0 for row in logged_rows), 'Repeated native sink'
    prefixes(logged)
    assert logged == candidate, 'Actual native candidate differs from transaction NODE log'
    assert candidate['root'] == original['root'] and candidate['sinks'] == original['sinks'], 'Terminal mapping changed'
    assert all(candidate['edges'].get(n) == edge for n, edge in retained['edges'].items()), 'Retained edge changed'
    before, after = prefixes(original), prefixes(candidate)
    changes = [dict(pin=pin, before_s=before[sink], after_s=after[sink])
               for pin, sink in candidate['sinks'].items() if before[sink] != after[sink]]
    return dict(retained_nodes=len(retained_nodes), other_branch_edges_unchanged=True,
                terminal_set_unchanged=True), changes


class DirectTransactionAudit:
    """One immutable graph-cache owner, reusable across current-state transactions."""
    def __init__(self, graph, cache_directory):
        self.cache = GraphAuditCache(graph, cache_directory)
        self.paths = [self.cache.graph, self.cache.directory/'completion.json'] + [
            self.cache.directory/name for name in read(self.cache.directory/'completion.json')['payload_sha256']]
        self.stats = {str(p): self._stat(p) for p in self.paths}

    @staticmethod
    def _stat(path):
        s = Path(path).stat()
        return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]

    def require_static(self):
        assert all(self._stat(p) == value for p, value in self.stats.items()), 'Immutable audit cache changed'

    def audit(self, worker, role, output):
        from resource_opportunity_census import stream_trace
        self.require_static()
        started = time.monotonic()
        output = Path(output).resolve()
        output.mkdir(exist_ok=False)
        assert not role['fixed_target_paths'], 'This resource-repair API does not cover forced-path reservations'
        assert all(sha(p) == h for p, h in role['source_sha256'].items())
        job = Path(worker['job'])
        origin = read(job/'completion.json')
        keys = ['static_identity','fingerprint','passed','route_sha256','native_directory',
                'native_options','artifact_sha256','candidate_full_STA_passed','native_transaction_succeeded']
        assert all(worker[k] == origin[k] for k in keys), 'Unbound native worker view'
        registry = read(job.parent/'registration.json')
        assert origin['passed'] and origin['static_identity'] == registry['identity']
        options = origin['native_options']
        assert options['operation'] in ['repair_fused','repair_feedback_fused']
        assert options['objective'] == role['objective']
        assert options['inputs']['native_request.txt'] == sha(role['request'])
        assert options['operation'] == ('repair_feedback_fused' if role['domain_failure_release'] else 'repair_fused')
        if role['crossing_reuse_enabled']:
            assert options['inputs']['crossing_domain.txt'] == sha(role['crossing_domain'])
        else:
            assert 'crossing_domain.txt' not in options['inputs']
        source = Path(role['source'])
        assert sha(source/'routed.route') == sha(job/'routed.route') == origin['route_sha256']
        command = registry['command']
        graph = Path(command[command.index('--read_rr_graph')+1])
        assert graph == self.cache.graph
        assert registry['static_input_sha256'][str(graph)] == self.cache.receipt['graph_sha256']
        for flag, name in [('--net_file','packed.net'),('--place_file','placed.place')]:
            assert sha(source/name) == registry['static_input_sha256'][command[command.index(flag)+1]]
        native = Path(origin['native_directory'])
        checked = {}
        def bound(path):
            path = Path(path)
            assert str(path) in origin['artifact_sha256']
            digest = sha(path)
            assert digest == origin['artifact_sha256'][str(path)], str(path)
            checked[str(path)] = digest
            return path
        log = bound(native/'joint_native.log')
        parsed = parse_transaction(log.read_text(), role['queries'])
        assert parsed['succeeded'] == origin['native_transaction_succeeded']
        common = dict(passed=True, queries=parsed['queries'], attempts=parsed['attempts'],
            native_transaction_seconds=parsed['native_transaction_seconds'], graph_cache=self.cache.receipt,
            origin_receipt=str(job/'completion.json'), origin_receipt_sha256=sha(job/'completion.json'),
            source_route_sha256=origin['route_sha256'],
            assurance_kind='actual_native_transaction_scope_edges_capacity', independent_physical_audit=False,
            candidate_serialization_performed=False, cache_epoch_requires_final_seal=True,
            qualification='Direct actual-tree scope/edge/capacity audit. Native FULL/fresh STA and independent physical resource/end-of-actor checks remain separate. Ordered candidate bytes are never reconstructed or canonicalized; topology equivalence here is not a search/cache identity.')
        if parsed['succeeded']:
            assert origin['candidate_full_STA_passed']
            for folder, kind in [('candidate','candidate'),('candidate_restored','restored_source')]:
                gate = bound(native/folder/'native_state_gate.txt')
                assert gate.read_text() == kind+' FULL fresh_STA actual_installed_trees\n'
            for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
                assert sha(bound(native/name)) == sha(bound(native/'candidate_restored'/name)), 'Source STA was not restored'
            candidate = bound(native/'candidate/routed.route')
            removed = {int(net): pins for net, pins in role['removed_pins'].items()}
            assert set(parsed['raw']) == set(parsed['kept']) == set(removed)
            occupancy = collections.Counter()
            scope, changes = [], []
            inspected_nets = set()
            pairs = zip_longest(stream_trace(source/'routed.route'), stream_trace(candidate))
            for before, after in pairs:
                assert before is not None and after is not None, 'Net set changed'
                net = before['net']
                assert net == after['net'] and before['name'] == after['name'], 'Net identity/order changed'
                original = from_trace(before['trace'], self.cache.switches) if before['trace'] else None
                actual = from_trace(after['trace'], self.cache.switches) if after['trace'] else None
                if net not in removed:
                    assert actual == original, ('Unselected net changed', net)
                else:
                    assert original is not None and actual is not None
                    item, delta = check_scope(original, actual, parsed['raw'][net], parsed['kept'][net],
                                              removed[net], self.cache.switches)
                    scope.append(dict(net=net, **item))
                    changes.extend(dict(net=net, **row) for row in delta)
                    self.cache.require_edges((up,n,sw) for n,(up,sw,delay) in actual['edges'].items())
                    inspected_nets.add(net)
                if actual is not None:
                    occupancy.update(nodes(actual))
            assert inspected_nets == set(removed)
            self.cache.require_occupancy(occupancy)
            common.update(status='actual_candidate_scope_checked_pending_acceptance',
                candidate_route=str(candidate), candidate_sha256=sha(candidate), scope=scope, changed_delays=changes,
                complete_candidate_capacity_checked=True)
        else:
            common.update(status='native_transaction_failed_no_candidate', candidate_route=None,
                          rollback='Native reports occupancy_restored; immutable source preserved; no candidate admitted.')
        assert all(sha(p) == h for p,h in checked.items()), 'Consumed actual artifact changed'
        assert all(sha(p) == h for p,h in role['source_sha256'].items())
        self.require_static()
        common.update(complete_direct_audit_seconds=time.monotonic()-started,
                      consumed_artifact_sha256=checked, source_sha256={str(Path(__file__).resolve()):sha(__file__)})
        write(output/'analysis.json', common)
        return common
