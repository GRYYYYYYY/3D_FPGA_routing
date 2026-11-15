"""One explicit whole transaction, including original-source control and acceptance.

This development entry is a building block of the complete controller. It does
not choose a benchmark-specific mechanism or terminate the research workflow.
"""
import argparse,fcntl,json,math,os,resource,shutil,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from endpoint_timing_policy_streaming_v2 import load,compare
from multiobjective_acceptance_v2 import decide
from current_resource_bundle_v2 import serialize_request
from observe import inputs

PACKAGE=Path(__file__).resolve().parent

def state_view(state):
    state=Path(state).resolve();closed=read(state/'completion.json');assert closed['passed']
    run=Path(closed['run']);manifest=read(run/'manifest.json');audit=read(run/'independent_audit.json')
    assert manifest['status']=='completed' and manifest['metrics']['native_full_check_passed'] and audit['audit']['passed']
    for name in ['routed.route','packed.net','placed.place']:assert sha(run/name)==manifest['outputs'][name]['sha256']
    vector=read(state/'endpoint_vector.json')
    assert vector==json.loads(json.dumps(load(run/'native_sta_frontier.jsonl'))),'State vector differs from complete actual trace'
    cmd=manifest['command'];physical=[]
    for path in [cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1]]:
        digest=sha(path);assert digest==manifest['shared_inputs'][path]['sha256'];physical.append(digest)
    physical += [sha(run/n) for n in ['packed.net','placed.place']]
    m=audit['physical_metrics'];axes=dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
    assert math.isfinite(vector['cpd_s']) and vector['cpd_s']>=0
    return dict(state=state,run=run,vector=vector,axes=axes,physical=physical)

def prepare(a):
    source=state_view(a.state);root=state_view(a.root_state)
    assert source['physical']==root['physical'] and compare(root['vector'],source['vector'])['compatible']
    config,paths,cache,command=inputs(a.inputs,a.output/'candidate')
    assert paths['route']==source['run']/'routed.route'
    assert all(sha(paths[k])==sha(source['run']/n) for k,n in [('packed','packed.net'),('placement','placed.place')])
    selected=read(a.selection/'completion.json');assert selected['passed']
    assert all(sha(f)==h for f,h in selected['source_sha256'].items()),'Stale selection input'
    assert all(sha(a.selection/n)==h for n,h in selected['artifact_sha256'].items()),'Stale selection artifact'
    for path in [source['run']/'routed.route',source['state']/'endpoint_vector.json',source['run']/'native_sta_frontier.jsonl']:
        assert selected['source_sha256'].get(str(path))==sha(path),'Selection belongs to a different source'
    assert a.rank>=0 and a.bundle_size>0
    if a.kind=='owner':
        assert a.domain_mode=='unrestricted' and not a.failure_release,'Unified owner coordination is unrestricted in both arms'
        data=read(a.selection/'owner.json');group=data['groups'][a.rank]
        assert group['eligible'] and group['target_screen']['eligible'] and group['owner_screen']['eligible']
        certificate=next(c for c in data['certificates'] if c['net']==group['target_net'])
        assert certificate['status']=='frozen_other_routes_force_two_distinct_crossing_resources'
        assert any(r['node']==group['escape_node'] and r['owner_net']==group['owner_net'] and r['capacity']==1 for r in certificate['local_exits'])
        cuts=[dict(net=net,pins=pins,ordered_queries=[q for q in group['queries'] if q['net']==net])
              for net,pins in [(group['target_net'],group['target_pins']),(group['owner_net'],group['owner_pins'])]]
    else:
        from current_resource_bundle_v2 import select_cuts
        cuts=select_cuts(read(a.selection/'crossing.json')['candidates'],a.bundle_size,a.rank)
    request,domain,queries=serialize_request(cuts)
    if a.kind=='owner':assert request==group['request'] and queries==group['queries']
    assert not a.failure_release or a.domain_mode=='retained'
    anchor=dict(CPD_s=root['vector']['cpd_s'],**root['axes'])
    limits=dict(root['axes'],wirelength=(root['axes']['wirelength']*1001+999)//1000)
    bound={}
    for view in [source,root]:
        for p in [view['state']/'completion.json',view['state']/'endpoint_vector.json',
                  *[view['run']/n for n in ['manifest.json','independent_audit.json','routed.route','packed.net','placed.place','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']]]:
            bound[str(p)]=sha(p)
    for p in [a.inputs.resolve(),a.selection/'completion.json',a.selection/'owner.json',a.selection/'crossing.json',PACKAGE/'artifact_manifest.json',*paths.values()]:bound[str(p)]=sha(p)
    b=a.output.resolve();b.mkdir(exist_ok=False)
    (b/'request.txt').write_text(request);(b/'domain.txt').write_text(domain);(b/'empty_request.txt').write_text('0\n0\n0\n')
    for n in ['request.txt','domain.txt','empty_request.txt']:bound[str(b/n)]=sha(b/n)
    role=dict(state=str(source['state']),source=str(source['run']),scope=a.kind,baseline='explicit_current_observation',
        request=str(b/'request.txt'),queries=queries,removed_pins={str(c['net']):c['pins'] for c in cuts},
        objective='weighted_soft',fixed_target_paths=False,crossing_reuse_enabled=a.domain_mode=='retained',
        domain_failure_release=a.failure_release,seed_order=a.seed_order,crossing_domain=str(b/'domain.txt'),
        original_budget=anchor,fixed_resource_limits=limits,source_sha256=bound)
    registration=dict(roles={'candidate':role},source_sha256=bound,root_state=str(root['state']),
        full_graph_cache=str(cache.directory),audit_cache=str(cache.g.directory),selection=str(a.selection),
        limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
        independent_input_interface=True,full_method_frozen=False)
    write(b/'registration.json',registration)
    return registration,source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['inputs','state','root-state','selection','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--kind',choices=['crossing','owner'],required=True)
    p.add_argument('--domain-mode',choices=['unrestricted','retained'],required=True)
    p.add_argument('--failure-release',action='store_true');p.add_argument('--rank',type=int,default=0)
    p.add_argument('--bundle-size',type=int,default=8);p.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],default='delay_rr_id')
    p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    a.output=a.output.resolve();a.selection=a.selection.resolve();assert not a.output.exists()
    assert shutil.disk_usage(a.output.parent).free>=80*1024**3
    lock=(a.output.parent/(a.output.name+'.lock')).open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    start=time.monotonic();reg,source=prepare(a);b=a.output
    if a.prepare_only:
        write(b/'preparation.json',dict(passed=True,native_calls_new=0,transaction_executed=False,registration_sha256=sha(b/'registration.json')));return
    costs=[]
    def invoke(script,args,tag):
        command=[sys.executable,str(PACKAGE/script),*map(str,args)];begin=time.monotonic()
        with (b/(tag+'.log')).open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]
            write(b/'active_child.json',dict(pid=child.pid,start_ticks=ticks,command=command,tag=tag))
            code=child.wait()
        costs.append(dict(tag=tag,returncode=code,complete_process_seconds=time.monotonic()-begin));write(b/'process_costs.json',costs)
        assert code==0,('Preserve failed execution; never automatically rerun',tag,code)
    common=['--inputs',a.inputs.resolve(),'--source',source['run'],'--seed-order',a.seed_order,'--candidate-full-sta']
    invoke('run_native_transaction_worker.py',[*common,'--batch',b/'source_control','--native-cases',b/'empty_request.txt'],'source_control')
    loaded=Path(read(b/'source_control/candidate_exports.json')['candidate'])/'routed.route'
    args=[*common,'--batch',b/'candidate','--native-cases',b/'request.txt','--expected-loaded-source-route',loaded]
    if a.domain_mode=='retained':args+=['--crossing-domain',b/'domain.txt']
    if a.failure_release:args+=['--domain-feedback']
    invoke('run_native_transaction_worker.py',args,'native_transaction')
    actual=read(b/'candidate/endpoint_vector.json')
    for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']:assert actual[k]==source['vector'][k],'Source changed during worker load'
    invoke('audit_native_feedback_objective_cached.py',['--batch',b,'--role','candidate','--cache',reg['audit_cache'],'--output',b/'candidate_audit'],'scope_audit')
    invoke('audit_failure_release_domain.py' if a.failure_release else 'audit_retained_crossing_domain.py',['--batch',b,'--role','candidate'],'domain_audit')
    audit=read(b/'candidate_audit/analysis.json');candidate=audit.get('candidate_route');decision=None;selected=source['state']
    if candidate:
        invoke('materialize_crossing_source_candidate_v1.py',['--worker',b/'candidate','--output',b/'evaluation','--full-graph-cache',reg['full_graph_cache'],'--audited-route',candidate],'candidate_materialization')
        after=state_view(b/'evaluation');assert after['physical']==source['physical']
        role=reg['roles']['candidate']
        decision=decide('resources_under_timing',source['vector'],after['vector'],source['axes'],after['axes'],
            cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],
            native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
        if decision['accepted']:selected=after['state']
    assert all(sha(f)==h for f,h in reg['source_sha256'].items()),'Original input changed'
    write(b/'completion.json',dict(passed=True,transaction_feasible=bool(candidate),accepted=bool(decision and decision['accepted']),
        selected_state=str(selected),source_state=str(source['state']),root_state=reg['root_state'],decision=decision,
        native_worker_calls=2,new_independent_inputs=0,complete_transaction_seconds=time.monotonic()-start,
        complete_single_configuration_seconds=None,source_sha256=reg['source_sha256'],
        qualification='Explicit-input whole transaction; original-source serialization control, actual candidate/restored native FULL/STA, unchanged scope/domain/capacity gates, complete fixed-root resource acceptance. Cost is one imported transaction, not complete algorithm cost. No automatic retry or complete controller claim.'))

if __name__=='__main__':main()
