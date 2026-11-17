"""Small file-backed raw-state fixtures, including installed callback provenance."""
import copy
import shutil
import tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from recovery_prefix_v1 import Evidence
from endpoint_timing_policy_streaming_v2 import load
from cp1r3_raw_admission_v1 import Audit

out=D/'CP1r3_raw_state_schema_validation_01';out.mkdir(exist_ok=False)
release=Path(read(D/'cp1r3_distinct_input_cohort_01/plan.json')['release'])
scratch=Path(tempfile.mkdtemp(prefix='cp1r3-raw-schema-',dir='/tmp'))
flow=scratch/'flow';flow.mkdir();graph=flow/'graph.xml';graph.write_text('<tiny_graph/>\n')


def regular(state):
    run=state/'runs/state';run.mkdir(parents=True)
    for name,text in [('packed.net','pack\n'),('placed.place','place\n'),('routed.route','header\nNet 1 (tiny)\nNode: 1\n'),
        ('stdout.log','Completed routing consistency check successfully.\nFinal critical path delay (least slack): 12.3457 ns\nVPR succeeded\n')]:
        (run/name).write_text(text)
    trace=run/'native_sta_frontier.jsonl'
    trace.write_text('\n'.join(__import__('json').dumps(row) for row in [
        dict(type='timing_metrics',least_slack_CPD_s=1.23456789e-8),
        dict(type='endpoint',node=1,atom_pin=2,name='tiny',setup_tags=[dict(launch=0,capture=0,slack_s=.5)],hold_tags=[]),
        dict(type='pin'),dict(type='complete',endpoint_rows=1,pin_rows=1)])+'\n')
    Path(str(trace)+'.constraints.echo').write_text('constraint\n');vector=load(trace)
    write(state/'endpoint_vector.json',vector)
    write(state/'completion.json',dict(passed=True,status='native_analysis_terminal',run=str(run),route_body_sha256=route_body(run/'routed.route')))
    write(state/'input_seal.json',dict(passed=True,inputs={str(graph):dict(passed=True,sha256=sha(graph))}))
    write(run/'manifest.json',dict(status='completed',returncode=0,command=['binary','--read_rr_graph',str(graph)],
        metrics=dict(native_full_check_passed=True,critical_path_ns=12.3457),shared_inputs={str(graph):dict(sha256=sha(graph))},
        outputs={name:dict(sha256=sha(run/name)) for name in ['packed.net','placed.place','routed.route','stdout.log']}))
    write(run/'independent_audit.json',dict(audit=dict(passed=True,errors=[],route=dict(overused_rr_nodes=0),
        inputs=dict(rr_graph=str(graph),rr_graph_sha256=sha(graph),route=str(run/'routed.route'),route_sha256=sha(run/'routed.route'))),
        physical_metrics=dict(planar_wirelength_excluding_sb_half_nodes=2,sb_pairs_used=1,cb_crossing_output_sources_used=0)))
    return run


worker=flow/'worker';wr=regular(worker);candidate=flow/'materialized';cr=regular(candidate)
native,restored=wr/'candidate',wr/'candidate_restored'
for dest,label in [(native,'candidate'),(restored,'restored_source')]:
    dest.mkdir()
    for name in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:shutil.copyfile(wr/name,dest/name)
    (dest/'native_state_gate.txt').write_text(label+' FULL fresh_STA actual_installed_trees\n')
fragment='H3D_ACTUAL_STATE_BEGIN candidate\nCompleted routing consistency check successfully.\nH3D_ACTUAL_STATE_COMPLETE candidate\n'
(wr/'stdout.log').write_text((wr/'stdout.log').read_text()+fragment)
m=read(wr/'manifest.json');m['outputs']['stdout.log']['sha256']=sha(wr/'stdout.log');write(wr/'manifest.json',m)
write(worker/'candidate_exports.json',dict(passed=True,candidate_gate_present=True,candidate=str(native),restored=str(restored)))
(cr/'stdout.log').write_text(fragment)
m=read(cr/'manifest.json');m.update(execution_scope='standalone_installed_candidate_callback',observed_state_kind='installed_candidate',
    source_worker_completion=str(worker/'completion.json'),actual_installed_candidate=dict(sha256=sha(native/'routed.route')),
    serialized_candidate_route_provenance=dict(same_complete_physical_tree_verified=True,route=str(cr/'routed.route'),sha256=sha(cr/'routed.route')))
m['outputs']['stdout.log']['sha256']=sha(cr/'stdout.log');m['metrics']['critical_path_ns']=load(cr/'native_sta_frontier.jsonl')['cpd_s']*1e9;write(cr/'manifest.json',m)
done=read(candidate/'completion.json');done.update(status='standalone_candidate_materialization_terminal',native_analysis_calls=0,
    consumed_already_executed_worker_receipt=True,source_sha256={str(worker/'completion.json'):sha(worker/'completion.json')});write(candidate/'completion.json',done)
write(candidate/'registration.json',dict(source_worker=str(worker),source_sha256=done['source_sha256']))
(candidate/'input_seal.json').unlink() # Fixture only: this schema deliberately has no fake input seal.
write(cr/'analysis_gate.json',dict(passed=True,native_candidate_FULL_fresh_STA=True,physical_capacity_audit=True,source_restored=True))
write(candidate/'independent_native_analysis_audit.json',dict(passed=True,legal_count=1,failed_count=0))
checks=[]
for state in [worker,candidate]:
    a=Audit(release,Evidence());result=a.state(state,flow);a.e.unchanged();assert result['actual_FULL_raw_STA_and_original_physical_proof_bound']
    checks.append('raw_'+state.name+'_fixture')


def rejected(name,path,mutator):
    old=path.read_bytes()
    try:
        mutator(path)
        try:Audit(release,Evidence()).state(candidate,flow)
        except (AssertionError,ValueError,KeyError):checks.append(name)
        else:raise RuntimeError('Accepted corrupted fixture: '+name)
    finally:path.write_bytes(old)


rejected('changed_candidate_gate',native/'native_state_gate.txt',lambda p:p.write_text('candidate unchecked\n'))
rejected('changed_restored_gate',restored/'native_state_gate.txt',lambda p:p.write_text('restored unchecked\n'))
rejected('raw_trace_truncation',cr/'native_sta_frontier.jsonl',lambda p:p.write_text(p.read_text().rsplit('\n',2)[0]+'\n'))
rejected('changed_constraints',Path(str(cr/'native_sta_frontier.jsonl')+'.constraints.echo'),lambda p:p.write_text('other\n'))
def vector_change(path):
    value=read(path);value['cpd_s']+=1e-18;write(path,value)
rejected('tiny_exact_CPD_change',candidate/'endpoint_vector.json',vector_change)
def proof_change(path):
    value=read(path);value['audit']['inputs']['route_sha256']='0'*64;write(path,value)
rejected('physical_proof_wrong_route',cr/'independent_audit.json',proof_change)
def count_change(path):
    value=read(path);value['audit']['route']['overused_rr_nodes']=1;write(path,value)
rejected('physical_overuse',cr/'independent_audit.json',count_change)
def kind_change(path):
    value=read(path);value['observed_state_kind']='source';write(path,value)
rejected('source_mislabelled_as_candidate',cr/'manifest.json',kind_change)
reused=flow/'physical_reuse';rr=regular(reused)
shutil.copyfile(wr/'independent_audit.json',rr/'independent_audit.json')
write(reused/'physical_audit_reuse.json',dict(passed=True,original=str(wr/'independent_audit.json'),
    original_sha256=sha(wr/'independent_audit.json'),exact_route_sha256=sha(wr/'routed.route'),graph_sha256=sha(graph)))
assert Audit(release,Evidence()).state(reused,flow)['actual_FULL_raw_STA_and_original_physical_proof_bound']
checks.append('exact_physical_proof_reuse_without_rewriting_original')
reuse_receipt=read(reused/'physical_audit_reuse.json');reuse_receipt['exact_route_sha256']='0'*64;write(reused/'physical_audit_reuse.json',reuse_receipt)
try:Audit(release,Evidence()).state(reused,flow)
except AssertionError:checks.append('wrong_physical_reuse_bytes_rejected')
else:raise RuntimeError('Accepted false physical-reuse binding')
write(out/'validation.json',dict(passed=True,checks=checks,fixture=scratch.as_posix(),
    real_experiment_state_admitted=False,new_native_or_STA_calls=0,
    source_sha256={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(D/'cp1r3_raw_admission_v1.py'):sha(D/'cp1r3_raw_admission_v1.py')},
    qualification='Small synthetic on-disk state fixtures exercise real parsers and proof bindings, including owner callback provenance. No real graph/route/raw STA consumed; no experimental evidence inferred.'))
print(dict(passed=True,checks=len(checks),actual_experiment_admission=False))
