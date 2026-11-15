"""Exercise actual sealed transition and exact native reuse without routing."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resolve_transaction_history_v1 import resolve
from current_native_reuse_resource import match
from explicit_envelope_timing_policy import decide
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity

out=D/'vector_then_strict_preflight_01';out.mkdir(exist_ok=False)
actor=D/'rejection_feedback_controller_dev_01/endpoint'
snapshot=out/'observed_attempts.json';snapshot.write_bytes((actor/'attempts.json').read_bytes())
history=resolve([snapshot])
tx=actor/'round_001/proposal_01/transaction';role=read(tx/'registration.json')['roles']['current_group']
hit=match(role,history);assert hit and Path(hit['batch'])==tx and Path(hit['evaluation'])==tx/'current_group_evaluation'
initial=Path(role['state']);candidate=Path(hit['evaluation'])
assert problem_identity(run_dir(initial))==problem_identity(run_dir(candidate))
caps=read(D/'low_resource_dual_timing_02/absolute_limits.json')
before=read(initial/'endpoint_vector.json');after=read(candidate/'endpoint_vector.json')
metrics=read(run_dir(candidate)/'independent_audit.json')['physical_metrics']
resources=dict(wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'])
decisions={policy:decide(policy,before,after,resources,cpd_limit_s=before['cpd_s'],resource_limits=caps,native_valid=True,transaction_complete=True) for policy in ['strict','endpoint_vector']}
assert decisions['strict']['accepted'] and not decisions['endpoint_vector']['accepted']
assert resources==dict(wirelength=2061293,SB_pairs=45,CB_sources=5060)
assert after['cpd_s']==1.3421610489672275e-08
write(out/'completion.json',dict(passed=True,actual_sealed_first_strict_transition=decisions,
    exact_native_reuse=hit,native_calls=0,complete_actor_test=False,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),snapshot,D/'queue_vector_then_strict_comparison_01.py',D/'resolve_transaction_history_v1.py',D/'current_native_reuse_resource.py',tx/'registration.json',initial/'endpoint_vector.json',candidate/'endpoint_vector.json']},
    qualification='Actual source/request match and policy proof for the known first strict candidate. Not a completed new trajectory. Queue binds actual vector terminal state only after closure; full native candidate checks remain mandatory.'))
print(dict(passed=True,exact_native_reuse=True,strict_accepts=True,vector_rejects=True,native_calls=0),flush=True)
