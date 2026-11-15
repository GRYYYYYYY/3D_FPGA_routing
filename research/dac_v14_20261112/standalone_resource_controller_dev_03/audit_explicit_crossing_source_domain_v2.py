"""Check a whole-net source whitelist; never label it retained-tree reuse."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace

p = argparse.ArgumentParser()
p.add_argument('--batch', type=Path, required=True)
p.add_argument('--role', required=True)
a = p.parse_args()
b = a.batch.resolve()
role = read(b / 'registration.json')['roles'][a.role]
worker = b / a.role
rd = run_dir(worker)
assert read(worker / 'completion.json')['passed']
assert role['crossing_reuse_enabled'] and not role['domain_failure_release']
source = Path(role['source'])
audit = read(b / (a.role + '_audit/analysis.json'))
assert audit['passed']
tokens = list(map(int, Path(role['explicit_crossings']).read_text().split()))
assert tokens[:3] == [1, 31767, len(tokens) - 3]
allowed = set(tokens[3:])
assert len(allowed) == len(tokens) - 3
original = next(r for r in stream_trace(source / 'routed.route') if r['net'] == 31767)
assert role['removed_pins']=={'31767':[1,2,3,4],'62707':[1]}
assert sorted(n.pin for n in original['trace'] if n.kind == 'SINK') == [1, 2, 3, 4]
crossings = [(x, y) for x, y in zip(original['trace'], original['trace'][1:])
             if x.switch != -1 and x.low[2] != y.low[2]]
cb = {x.inode for x, y in crossings if x.kind == 'OPIN'}
sb_pairs = {tuple(sorted([x.inode, y.inode])) for x, y in crossings if x.kind != 'OPIN'}
assert cb == {265308} and sb_pairs == {(5916265, 8689817)}
if role['allowed_resource_kind'] == 'CB':
    assert allowed == cb
else:
    assert role['allowed_resource_kind'] == 'SB'
    assert allowed == {5916265, 8689817}
manifest = read(rd / 'manifest.json')
assert manifest['environment']['VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS'] == role['explicit_crossings']
assert manifest['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE'] == '0'
rows = [l.split() for l in (rd / 'vertical_domain.log').read_text().splitlines()]
assert rows[-1][0] == 'COMPLETE' and rows[-1][-1] == 'occupancy_restored'
observed = []
for r in rows[:-1]:
    if r[0] == 'ALLOW':
        net, pin, count = map(int, r[1:4])
        assert net == 31767 and count == len(allowed) and set(map(int, r[4:])) == allowed
        observed.append((net, pin))
    else:
        assert r[0] == 'CHECK' and r[-1] == '1'
assert observed == [(r['net'], r['pin']) for r in [q for q in role['queries'] if q['net']==31767][:len(observed)]]
actual = []
files = [Path(__file__).resolve(), b / 'registration.json', worker / 'completion.json',
         rd / 'manifest.json', rd / 'vertical_domain.log', b / (a.role + '_audit/analysis.json'),
         source / 'routed.route', Path(role['explicit_crossings'])]
if audit.get('candidate_route'):
    rec = next(r for r in stream_trace(audit['candidate_route']) if r['net'] == 31767)
    actual = [(x.inode, y.inode) for x, y in zip(rec['trace'], rec['trace'][1:])
              if x.switch != -1 and x.low[2] != y.low[2]]
    assert {x for x, y in actual} <= allowed
    resources = {('CB', x) if x in cb else ('SB', tuple(sorted([x, y]))) for x, y in actual}
    assert len(resources) <= 1
    files.append(Path(audit['candidate_route']))
write(b / (a.role + '_domain_audit.json'), dict(passed=True, enabled=True,
      explicit_whole_net_source_restriction=True, retained_crossing_reuse=False,
      allowed_resource_kind=role['allowed_resource_kind'], allowed_sources=sorted(allowed),
      actual_candidate_crossings=actual, transaction_completed=bool(int(rows[-1][1])),
      source_sha256={str(f): sha(f) for f in files},
      qualification='Allows one existing source-net crossing resource (CB or both directions of one SB pair), even though whole-net pruning retains no crossing. This is a separate explicit native-search constraint, not retained-tree reuse or a native infeasibility certificate. Domain release disabled. All actual crossing edges/closure checks obey the whitelist; candidate FULL/STA and independent capacity/scope audit remain mandatory.'))
