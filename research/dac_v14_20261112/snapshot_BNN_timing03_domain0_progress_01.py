"""Snapshot small existing phase receipts; never infer whole-arm completion."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

batch = D/'BNN_interleaved_timing_03'; case = batch/'domain_0'; flow = case/'flow'
out = D/'BNN_timing03_domain0_progress_01'; assert not out.exists()
assert not (case/'completion.json').exists()
q = read(batch/'queue/status.json'); assert q['case']=='domain_0'
reg = read(batch/'queue/registration.json')
owner = process_identity(reg['pid']); worker = process_identity(q['pid'])
assert owner and owner['state']!='Z' and owner['start_ticks']==reg['start_ticks']
assert worker and worker['state']!='Z' and worker['start_ticks']==q['start_ticks']
active = read(flow/'active_child.json'); child = process_identity(active['pid'])
assert child and child['state']!='Z' and child['start_ticks']==active['start_ticks']
assert active['phase']=='complete_current_STA_timing'
out.mkdir(); (out/'metadata').mkdir(); copies=[]
def capture(p,name):
    data=p.read_bytes(); dest=out/'metadata'/name; dest.write_bytes(data)
    copies.append(dict(original=str(p),copy=str(dest),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    return json.loads(data)
stages = capture(flow/'stages.json','completed_stages.json')
assert len(stages)==3 and all(r['status']=='completed' and r['returncode']==0 for r in stages)
capture(batch/'queue/status.json','queue_status.json')
capture(flow/'active_child.json','active_child.json')
resource = capture(flow/'resource_flow/repair/completion.json','resource_completion.json')
assert resource['passed']
steps = capture(flow/'timing/steps.json','timing_steps.json')
attempts = capture(flow/'timing/attempts.json','timing_attempts.json')
resume = capture(flow/'timing/resume_state.json','timing_resume_state.json')
write(out/'completion.json',dict(passed=True,kind='readonly_metadata_observation_not_method_completion',
    observed_at=datetime.now(timezone.utc).isoformat(),case='domain_0',queue_owner=owner,measured_wrapper=worker,
    actual_active_child=child,phase=active['phase'],completed_phase_costs=[{k:r[k] for k in ['phase','status','returncode','complete_process_seconds']} for r in stages],
    timing_accepted_steps_observed=len(steps),timing_attempts_observed=len(attempts),timing_round_observed=resume['round_number'],
    complete_arm_verified=False,complete_arm_seconds=None,paired_ratio=None,new_independent_inputs=0,
    new_native_calls_by_snapshot=0,new_STA_calls_by_snapshot=0,copies=copies,
    source_sha256={str(Path(__file__).resolve()):sha(Path(__file__).resolve())},
    qualification='Existing deterministic queue continues. Metadata files are individually copied, not a globally atomic state. No large input bytes, full STA vectors or native queries are re-read. Phase times are not added into complete time. Original whole verifier and all four-role matching remain pending.'))
print(dict(passed=True,case='domain_0',completed_phases=len(stages),complete_arm_verified=False,timing_steps=len(steps)))
