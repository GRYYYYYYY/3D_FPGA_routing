"""Check the actual zero-progress preimage and reject altered provenance."""
import copy
import datetime
import hashlib
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(D))
from vertical_cost_zero_progress_transition_v1 import reconcile

read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
E = D/'vertical_cost_baseline_dev_01/execution'
O = Path(__file__).resolve().parent
zero, progress, terminal = [read(E/n) for n in ['zero_equivalence.json', 'progress.json', 'completion.json']]
path = str(E/'progress.json')
actual = reconcile(zero, progress, terminal, path)
rows = [dict(name='actual_exact_original_progress_preimage', passed=True)]
mutations = [
    ('zero_passed', lambda z,p,t: z.update(passed=False)),
    ('zero_mode', lambda z,p,t: z.update(mode='weighted')),
    ('zero_equivalence', lambda z,p,t: z.update(zero_equivalence_passed=False)),
    ('zero_permission', lambda z,p,t: z.update(positive_weights_permitted=False)),
    ('terminal_status', lambda z,p,t: t.update(status='running')),
    ('terminal_accounted', lambda z,p,t: t.update(all_roles_accounted=False)),
    ('terminal_zero', lambda z,p,t: t.update(zero_equivalence_passed=False)),
    ('role_missing', lambda z,p,t: p.pop('weight_2')),
    ('role_extra', lambda z,p,t: p.update(unregistered={})),
    ('zero_extra_field', lambda z,p,t: p['weight_0'].update(extra=True)),
    ('zero_evaluation', lambda z,p,t: p['weight_0'].update(evaluation='different')),
    ('zero_cpd', lambda z,p,t: p['weight_0'].update(cpd_s=1.)),
    ('zero_resources', lambda z,p,t: p['weight_0']['resources'].update(SB_pairs=8)),
    ('zero_policies', lambda z,p,t: p['weight_0']['policies'].clear()),
    ('zero_quality', lambda z,p,t: p['weight_0'].update(quality_admitted=False)),
    ('zero_verification', lambda z,p,t: p['weight_0'].update(verification_status='failed')),
    ('zero_rollback', lambda z,p,t: p['weight_0'].update(rollback_verified=True)),
    ('original_digest', lambda z,p,t: z['source_sha256'].update({path:'0'*64})),
]
for name, mutate in mutations:
    z,p,t = copy.deepcopy(zero),copy.deepcopy(progress),copy.deepcopy(terminal)
    mutate(z,p,t)
    if name.startswith(('zero_', 'role_')):
        t['roles'] = copy.deepcopy(p)
    try:
        reconcile(z,p,t,path)
    except (AssertionError, KeyError):
        rows.append(dict(name=name, passed=True, rejected=True))
    else:
        raise AssertionError(name)
reg = read(O/'registration.json')
assert sha(reg['original_frozen_auditor']) == reg['original_sha256']
assert sha(reg['development_auditor']) == reg['development_sha256']
result = dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              passed=True, tests=len(rows), rows=rows, actual_zero_progress_transition=actual,
              native_calls=0, STA_calls=0, large_graph_or_raw_vector_reads=0,
              full_weighted_admission_executed=False, quality_admitted=False,
              qualification='Exact original preimage and negative small-metadata guards only; all actual-byte gates remain required under the serial slot.')
(O/'transition_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(dict(passed=True, tests=len(rows), remaining_immutable_bindings=len(actual['immutable_source_sha256'])))
