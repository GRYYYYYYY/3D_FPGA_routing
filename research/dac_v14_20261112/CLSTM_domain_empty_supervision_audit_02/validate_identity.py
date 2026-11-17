"""Exercise the exact metadata exception and reject contradictory identities."""
import copy
import datetime
import hashlib
import json
import sys
from pathlib import Path

O=Path(__file__).resolve().parent
D=O.parent
sys.path.insert(0,str(D))
from empty_interrupted_supervision_identity_v1 import corroborate
from recovery_prefix_v1 import live_identity

read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
registration=read(O/'registration.json')
tx=Path(registration['original_inventory_row']['transaction'])
bad=Path(registration['exact_empty_path'])
active=read(tx/'reuse_on_native_supervision.active.json')
worker=read(tx/'reuse_on/registration.json')
completion=read(tx/'reuse_on/completion.json')
seal=read(tx/'reuse_on/input_seal.json')
actor=read(Path(registration['original_inventory_row']['flow'])/'resource_flow/repair/registration.json')
dead={**{k:not live_identity(active[k]['pid'],active[k]['start_ticks']) for k in ['supervisor','child']},
      'worker':not live_identity(worker['pid'],worker['start_ticks']),
      'actor':not live_identity(actor['pid'],actor['start_ticks'])}
args=[str(bad),str(bad),sha(bad),registration['source_sha256'][str(bad)],active,worker,completion,seal,dead]
proof=corroborate(*args)
tests=[dict(name='actual_exact_empty_file_and_sealed_dead_identities',passed=True)]
changes=[
    ('wrong_path',lambda a:a.__setitem__(0,'other')),
    ('nonempty_bytes',lambda a:a.__setitem__(2,'0'*64)),
    ('historical_digest_changed',lambda a:a.__setitem__(3,'0'*64)),
    ('missing_supervisor',lambda a:a[4].pop('supervisor')),
    ('changed_child_pid',lambda a:a[4]['child'].update(pid=1)),
    ('changed_child_ticks',lambda a:a[4]['child'].update(start_ticks='1')),
    ('aliased_supervisor',lambda a:a[4].update(supervisor=copy.deepcopy(a[4]['child']))),
    ('missing_dead_identity',lambda a:a[8].pop('actor')),
    ('live_supervisor',lambda a:a[8].update(supervisor=False)),
    ('live_child',lambda a:a[8].update(child=False)),
    ('live_worker',lambda a:a[8].update(worker=False)),
    ('live_actor',lambda a:a[8].update(actor=False)),
    ('unsealed_worker',lambda a:a[6].update(passed=False)),
    ('incomplete_worker',lambda a:a[6].update(process_status='running')),
    ('not_observation',lambda a:a[6].update(observation_only=False)),
    ('missing_FULL',lambda a:a[6]['checks'].pop('native_FULL')),
    ('failed_FULL',lambda a:a[6]['checks'].update(native_FULL=False)),
    ('failed_physical',lambda a:a[6]['checks'].update(physical_audit=False)),
    ('failed_input_seal',lambda a:a[7].update(passed=False)),
    ('malformed_dead_flag',lambda a:a[8].update(actor='true')),
]
for name,change in changes:
    altered=copy.deepcopy(args);change(altered)
    try:
        corroborate(*altered)
    except (AssertionError,KeyError):
        tests.append(dict(name=name,passed=True,rejected=True))
    else:
        raise AssertionError(name)
assert all(sha(p)==h for p,h in registration['source_sha256'].items())
result=dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            passed=True,tests=len(tests),rows=tests,actual_metadata_corroboration=proof,
            full_stage_byte_request_STA_vector_audit_executed=False,
            quality_or_candidate_admitted=False,new_native_or_STA_calls=0,
            qualification='Identity and sealed metadata guards only. No raw graph/STA/vector read, no replacement of the original empty or failed records.')
(O/'identity_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(dict(passed=True,tests=len(tests),actual_identities_dead=True,full_admission=False))
