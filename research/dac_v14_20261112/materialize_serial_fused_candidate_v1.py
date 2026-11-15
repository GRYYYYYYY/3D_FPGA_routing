"""Materialize a real standalone installed-candidate observation; no new VPR call."""
import argparse,copy,shutil,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import load
from full_route_graph_cache import FullRouteGraphCache

sys.path.insert(0,str(D.parents[1]/'scripts'))
import flatland_benchmark as study

def materialize(worker,output,graph_cache):
    started=time.monotonic();worker=Path(worker).resolve();b=Path(output).resolve()
    closed=read(worker/'completion.json');assert closed['passed']
    exports=read(worker/'candidate_exports.json');assert exports['passed'] and exports['candidate_gate_present']
    reg=read(worker/'registration.json');assert reg['candidate_full_STA']
    assert all(sha(f)==h for f,h in reg['source_sha256'].items())
    source=Path(closed['run']);native=Path(exports['candidate']);restored=Path(exports['restored'])
    assert (native/'native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
    assert (restored/'native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
    assert route_body(restored/'routed.route')==route_body(source/'routed.route')
    before=load(source/'native_sta_frontier.jsonl');recovered=load(restored/'native_sta_frontier.jsonl')
    assert all(before[k]==recovered[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
    text=(source/'stdout.log').read_text();begin='H3D_ACTUAL_STATE_BEGIN candidate\n';end='H3D_ACTUAL_STATE_COMPLETE candidate\n'
    assert text.count(begin)==text.count(end)==1
    fragment=text.split(begin,1)[1].split(end,1)[0]
    assert 'Completed routing consistency check successfully.' in fragment
    vector=load(native/'native_sta_frontier.jsonl');assert vector['constraints_sha256']==before['constraints_sha256']
    manifest=copy.deepcopy(read(source/'manifest.json'));graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
    cache=FullRouteGraphCache(graph,graph_cache)
    artifacts=[worker/'completion.json',worker/'registration.json',worker/'candidate_exports.json',source/'manifest.json',source/'stdout.log',native/'routed.route',native/'native_sta_frontier.jsonl',native/'native_state_gate.txt',restored/'routed.route',restored/'native_sta_frontier.jsonl',restored/'native_state_gate.txt',Path(graph_cache)/'completion.json']
    hashes={str(f):sha(f) for f in [Path(__file__).resolve(),*artifacts]}
    b.mkdir(exist_ok=False);rd=b/'runs/state';rd.mkdir(parents=True)
    for name in ['packed.net','placed.place']:shutil.copy2(source/name,rd/name)
    for name in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:
        if (native/name).exists():shutil.copy2(native/name,rd/name)
    (rd/'stdout.log').write_text(begin+fragment+end)
    manifest.update(name='state',cwd=str(rd),status='completed',execution_scope='standalone_installed_candidate_callback',
        command_semantics='Actual standalone worker command loaded the source route. This candidate was installed, FULL checked, observed with a new STA object and printed inside that same process; no candidate LOAD or extra native execution is claimed.',
        observed_state_kind='installed_candidate',source_worker_completion=str(worker/'completion.json'),
        actual_installed_candidate=dict(route=str(native/'routed.route'),sha256=sha(native/'routed.route'),gate=str(native/'native_state_gate.txt')),
        wall_seconds=None,native_analysis_calls_new=0,outputs={n:dict(sha256=sha(rd/n),bytes=(rd/n).stat().st_size) for n in ['packed.net','placed.place','routed.route','stdout.log']})
    manifest['metrics']=dict(native_full_check_passed=True,routing_success_reported=True,critical_path_ns=vector['cpd_s']*1e9,
        routing_success_semantics='Actual installed candidate FULL/fresh STA callback, not initial routing success.',metrics_source='Dedicated candidate vector and exact native checker log fragment')
    write(rd/'manifest.json',manifest);write(rd/'pair_check.json',dict(passed=True,scope='Exact worker packing and placement.'))
    oldbase=study.BASE;oldreader=study.cr.read_graph_evidence
    study.BASE=b;study.cr.read_graph_evidence=cache.evidence
    try:audit=study.audit_batch({'fixture':{'original_graph':str(graph)}},[manifest],b/'independent_native_analysis_audit.json')
    finally:study.BASE=oldbase;study.cr.read_graph_evidence=oldreader
    assert audit['passed'] and audit['legal_count']==1
    assert all(sha(f)==h for f,h in hashes.items())
    write(b/'endpoint_vector.json',vector);write(b/'registration.json',dict(source_sha256=hashes,source_worker=str(worker),actual_candidate=str(native)))
    write(rd/'analysis_gate.json',dict(passed=True,native_candidate_FULL_fresh_STA=True,physical_capacity_audit=True,source_restored=True))
    result=dict(passed=True,status='standalone_candidate_materialization_terminal',run=str(rd),native_analysis_calls=0,
        consumed_already_executed_worker_receipt=True,full_precision_cpd_s=vector['cpd_s'],source_sha256=hashes,
        route_body_sha256=route_body(rd/'routed.route'),complete_materialization_seconds=time.monotonic()-started,
        qualification='Dedicated actual installed candidate gate/vector and independent physical/capacity audit. Complete execution time belongs to the outer worker/flow. Source input manifest is never relabeled as a candidate LOAD.')
    write(b/'completion.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--full-graph-cache',type=Path,required=True);a=p.parse_args()
    print(materialize(a.worker,a.output,a.full_graph_cache),flush=True)
