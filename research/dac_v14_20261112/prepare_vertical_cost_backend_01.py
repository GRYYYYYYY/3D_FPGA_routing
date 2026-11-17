"""Prepare an isolated multi-strength controller, preserving original backend."""
import ast
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root=D/'vertical_cost_baseline_dev_01'
parent=D/'run_joint_crossing_source_transactions_v3.py'
out=root/'run_vertical_cost_transactions.py';assert not out.exists()
original=parent.read_text();text=original;changes=[]
def replace(old,new):
    global text
    assert text.count(old)==1,old[:90]
    text=text.replace(old,new);changes.append(dict(old=old,new=new))

replace('from retained_prefix_workflow import D,read,write,sha,route_body',
        "sys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom retained_prefix_workflow import D,read,write,sha,route_body")
replace("selector_files=[D/'audit_selected_retained_domain_v1.py'",
        "selector_files=[D/'vertical_cost_evidence_v1.py',D/'vertical_cost_baseline_dev_01/plan.json',D/'vertical_cost_baseline_dev_01/run_vertical_cost_seed_analysis.py',D/'vertical_cost_baseline_dev_01/build/binding.json',D/'audit_selected_retained_domain_v1.py'")
old="""source_role=next(iter(reg['roles'].values()));empty=b/'source_empty_request.txt';empty.write_text('0\\n0\\n0\\n')
control=b/'source_serialization_control'
assert invoke('run_crossing_source_seed_analysis_v1.py',['--source',source_role['source'],'--batch',control,'--native-cases',empty,'--seed-order',source_role['seed_order'],'--candidate-full-sta'],'source_serialization_control')
loaded=Path(read(control/'candidate_exports.json')['candidate'])/'routed.route'"""
new="""root=D/'vertical_cost_baseline_dev_01'
assert list(reg['roles'])==['weight_0','weight_05','weight_1','weight_2']
weights=dict(zip(reg['roles'],[0.,.5,1.,2.]))
assert reg['vertical_cost_weights']==weights
assert all(role==read(root/'reference_role.json') for role in reg['roles'].values())
assert reg['current_resource_selector_after_commit'] is True
control=D/'robot_union_mechanism_02/transaction/source_serialization_control'
empty=control.parent/'source_empty_request.txt'
assert invoke('vertical_cost_evidence_v1.py',['--mode','source-control','--output',b/'source_control_reuse.json'],'source_control_readonly_admission')
reuse=read(b/'source_control_reuse.json');assert reuse['passed']
loaded=Path(reuse['source_control']['loaded_source_route'])"""
replace(old,new)
replace("for name,role in reg['roles'].items():\n state=", """for name,role in reg['roles'].items():
 if weights[name]>0:
  zero=b/'zero_equivalence.json'
  if not zero.exists():
   assert invoke('vertical_cost_evidence_v1.py',['--mode','zero','--transaction',b,'--role','weight_0','--output',zero],'zero_readonly_equivalence'), 'Preserve mismatch; no positive weight may run'
  assert read(zero)['passed'] and read(zero)['zero_equivalence_passed']
 state=""")
replace("ok=invoke('run_crossing_source_seed_analysis_v1.py',native_args,name+'_native')",
        "native_args+=['--vertical-cost-weight',weights[name]]\n  ok=invoke('vertical_cost_baseline_dev_01/run_vertical_cost_seed_analysis.py',native_args,name+'_native')")
replace(" write(b/'progress.json',results);print(name,results[name],flush=True)",
        """ write(b/'progress.json',results);print(name,results[name],flush=True)
 if weights[name]>0:
  assert invoke('vertical_cost_evidence_v1.py',['--mode','weighted','--weight',weights[name],'--transaction',b,'--role',name,'--output',b/(name+'_verification.json')],name+'_readonly_admission')""")
replace("control/'completion.json',control/'candidate_exports.json',loaded,empty,",
        "control/'completion.json',control/'candidate_exports.json',loaded,empty,b/'source_control_reuse.json',*b.glob('*equivalence.json'),*b.glob('*_verification.json'),")
replace("qualification='No external native reuse; selected retained-crossing domains with optional one-time failed-net release; explicit crossing masks are a separate legacy branch. Empty-source default control and actual source/candidate/restored gates counted. Complete shared multi-arm development workflow cost, not a standalone configuration runtime. Individual failures do not stop other arms or the research goal. Further searches must use each accepted current state and updated occupancy/STA.'",
        "qualification='Same-source fixed-group simple crossing-cost mechanism control, weights0/.5/1/2 preregistered. Historical actual empty serialization control reused only after independent byte/raw-STA/physical admission, creation cost not charged anew. Zero equivalence gates every positive strength. All new work and audit costs recorded. Imported multi-strength scope, not full-controller runtime, external-router reproduction or independent-input confirmation. Preserve failures, no gain and budget rejection.'")
ast.parse(text)
inverse=text
for c in reversed(changes):
    assert inverse.count(c['new'])==1
    inverse=inverse.replace(c['new'],c['old'])
assert inverse==original
out.write_text(text)
write(root/'backend_preparation.json',dict(passed=True,parent=str(parent),parent_sha256=sha(parent),
    backend=str(out),backend_sha256=sha(out),changes=changes,inverse_transform_exact=True,
    zero_gate_before_positive_strengths=True,actual_serialization_control_reused_only_after_independent_audit=True,
    native_or_STA_calls_new=0,build_executed=False,execution_queued=False,
    qualification='Prepared controller only. End-to-end preflight/negative-outcome audit and serial build/actual zero equivalence remain required before queue registration.'))
print(dict(passed=True,changes=len(changes),native_or_STA_calls_new=0))
