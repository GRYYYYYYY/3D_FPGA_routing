"""Explicit-input native FULL/STA observation; candidate acceptance remains separate."""
import argparse,fcntl,json,os,resource,shutil,time
from pathlib import Path
import runtime_io as io
import runtime_audit as study
from retained_prefix_workflow import read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import load
from full_route_graph_cache import FullRouteGraphCache

PACKAGE=Path(__file__).resolve().parent
REQUIRED={'binary','architecture','circuit','graph','packed','placement','route'}
PATH_OPTIONS={'--read_rr_graph':'graph','--net_file':'packed','--place_file':'placement','--route_file':'route','--sdc_file':'sdc'}
FIXED={'--num_workers':'1','--clock_modeling':'ideal','--check_route':'full','--verify_file_digests':'off','--verify_route_file_switch_id':'on','--timing_report_npaths':'10'}
OPTIONAL_FIXED={'--routing_failure_predictor':'off','--merge_constant_generators':'off'}
OTHER={'--device','--route_chan_width','--seed','--max_router_iterations','--router_max_convergence_count','--router_reconvergence_cpd_threshold'}

def inputs(config_path,output):
    config_path=Path(config_path).resolve();c=read(config_path)
    assert c['format']=='standalone_native_observation_input_v1'
    package=read(PACKAGE/'artifact_manifest.json')
    for name,digest in package['sha256'].items():assert sha(PACKAGE/name)==digest,name
    assert REQUIRED<=c['files'].keys() and c['files'].keys()<=REQUIRED|{'sdc'}
    paths={}
    for key,row in c['files'].items():
        p=(config_path.parent/row['path']).resolve();assert p.is_file() and sha(p)==row['sha256'],key;paths[key]=p
    assert os.access(paths['binary'],os.X_OK)
    arguments=c['analysis_arguments'];assert arguments and all(isinstance(x,str) for x in arguments)
    options={};i=0
    while i<len(arguments):
        key=arguments[i];assert key not in options and key.startswith('--'),key
        if key=='--analysis':options[key]=None;i+=1;continue
        assert key in FIXED.keys()|OPTIONAL_FIXED.keys()|OTHER|PATH_OPTIONS.keys(),key
        assert i+1<len(arguments);options[key]=arguments[i+1];i+=2
    assert '--analysis' in options and all(options.get(k)==v for k,v in FIXED.items())
    assert all(options[k]==v for k,v in OPTIONAL_FIXED.items() if k in options), 'Optional fixed routing controls changed'
    assert {'--device','--route_chan_width','--seed'}<=options.keys()
    for key in ['--route_chan_width','--seed']:assert int(options[key])>0
    for option,key in PATH_OPTIONS.items():
        if key=='sdc' and key not in paths:assert option not in options;continue
        assert options.get(option)=='{'+key+'}',option
    cache=(config_path.parent/c['full_graph_cache']['path']).resolve()
    assert sha(cache/'completion.json')==c['full_graph_cache']['completion_sha256']
    graph_cache=FullRouteGraphCache(paths['graph'],cache)
    private=Path(output).resolve()/'runs/state';resolved=dict(paths,packed=private/'packed.net',placement=private/'placed.place',route=private/'routed.route')
    command=[str(paths[k]) for k in ['binary','architecture','circuit']]
    for token in arguments:
        command.append(str(resolved[token[1:-1]]) if token.startswith('{') and token.endswith('}') else token)
    assert '--route' not in command
    return c,paths,graph_cache,command

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--preflight',action='store_true');p.add_argument('--timing-echo',action='store_true');a=p.parse_args()
    start=time.monotonic();b=a.output.resolve();assert not b.exists()
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(b.parent).free>=80*1024**3
    lock=(b.parent/(b.name+'.lock')).open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    c,paths,cache,command=inputs(a.inputs,b)
    package_files=[PACKAGE/name for name in read(PACKAGE/'artifact_manifest.json')['sha256']]
    cache_files=[cache.directory/'completion.json',cache.g.directory/'completion.json']
    for directory in [cache.directory,cache.g.directory]:
        cache_files.extend(directory/name for name in read(directory/'completion.json')['payload_sha256'])
    sources={str(f):sha(f) for f in [a.inputs.resolve(),PACKAGE/'artifact_manifest.json',*package_files,*paths.values(),*cache_files]}
    if a.preflight:
        b.mkdir();write(b/'completion.json',dict(passed=True,preflight_only=True,native_calls=0,command=command,
            source_sha256=sources,cache_receipt=cache.receipt,accepted=None,qualification='Explicit hashes, fixed analysis command and physical cache checked; no native process or quality result.'));return
    for key in list(os.environ):
        if key.startswith('VPR_'):del os.environ[key]
    io.configure(b,paths['binary'])
    for f,h in sources.items():io.frozen_hash(f,h)
    registration=dict(status='registered_before_native',input_config=str(a.inputs.resolve()),input_sha256=sha(a.inputs),
        source_sha256=sources,native_analysis_calls_planned=1,route_search_calls=0,acceptance='separate whole-transaction policy',
        limits=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3))
    write(b/'registration.json',registration)
    rd=b/'runs/state';rd.mkdir(parents=True)
    for key,name in [('packed','packed.net'),('placement','placed.place'),('route','routed.route')]:shutil.copy2(paths[key],rd/name)
    before={name:sha(rd/name) for name in ['packed.net','placed.place','routed.route']}
    write(rd/'pair_check.json',dict(passed=True,checks={key:sha(rd/name)==sha(paths[key]) for key,name in [('packed','packed.net'),('placement','placed.place')]},scope='Exact declared packing and placement, route bound before native analysis.'))
    env=dict(VPR_H3D_MODE='off',VPR_H3D_FINAL_STA_TRACE=str(rd/'native_sta_frontier.jsonl'),
        VPR_H3D_FINAL_TIMING_ECHO=str(rd/'timing_graph.full_precision.echo') if a.timing_echo else '')
    result=io.run('state',command,frozen=[*paths.values(),b/'registration.json'],private_inputs=[rd/name for name in before],environment=env,timeout=1800,tags=dict(phase='standalone_native_endpoint_observation',route_search_calls=0))
    log=(rd/'stdout.log').read_text();checks=dict(completed=result['status']=='completed' and result['returncode']==0,
        native_FULL=result['metrics'].get('native_full_check_passed',False),routing_success=result['metrics'].get('routing_success_reported',False),
        route_loaded='Finished loading route file' in log,inputs_unchanged=all(sha(rd/name)==h for name,h in before.items()))
    study.BASE=b;original=study.cr.read_graph_evidence;study.cr.read_graph_evidence=cache.evidence
    try:audit=study.audit_batch({'fixture':{'original_graph':str(paths['graph'])}},[result],b/'physical_audit.json')
    finally:study.cr.read_graph_evidence=original
    checks['physical_audit']=audit['passed'] and audit['legal_count']==1 and audit['failed_count']==0
    write(b/'full_graph_cache_receipt.json',cache.receipt)
    checks['timing_echo']=(rd/'timing_graph.full_precision.echo').is_file() and 'H3D_FINAL_TIMING_ECHO path=' in log if a.timing_echo else not (rd/'timing_graph.full_precision.echo').exists()
    vector=None
    if all(checks.values()):
        vector=load(rd/'native_sta_frontier.jsonl');checks['full_precision_CPD_matches_report']=float(format(vector['cpd_s']*1e9,'.6g'))==result['metrics']['critical_path_ns']
        write(b/'endpoint_vector.json',vector)
    io.seal_inputs(b/'input_seal.json');checks['inputs_sealed']=read(b/'input_seal.json')['passed']
    write(rd/'analysis_gate.json',dict(passed=all(checks.values()),checks=checks))
    write(b/'completion.json',dict(passed=all(checks.values()),status='native_analysis_terminal',run=str(rd),accepted=None,
        native_analysis_calls=1,route_search_calls=0,checks=checks,cpd_ns=result['metrics'].get('critical_path_ns'),
        full_precision_cpd_s=None if vector is None else vector['cpd_s'],endpoints=None if vector is None else len(vector['endpoint_ids']),
        route_body_sha256=route_body(rd/'routed.route'),complete_evaluation_seconds=time.monotonic()-start,
        qualification='One explicit supplied-route FULL/STA and fresh cached physical audit. No historical terminal state/proof aliases. Candidate acceptance and full-method confirmation are separate; this development interface has its own measured cost.'))
    assert all(checks.values()),'Preserve failed observation; do not repeat an already completed native process'

if __name__=='__main__':main()
