"""One fixed configuration from architecture/netlist/placement through repair.

No initial route, prior candidate result or query cache is imported. Graph-only
indexes are either built within the measured command or explicitly supplied as
reusable preprocessing. Initial routing and repair use the same frozen binary.
"""
import argparse
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy_streaming_v2 import load
from full_route_graph_cache import FullRouteGraphCache

ROOT=D.parents[1]
OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();started=time.monotonic();config=read(args.config)
    b=args.output.resolve();b.mkdir(parents=True,exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    assert shutil.disk_usage(b).free>=80*1024**3
    assert config['cache_mode'] in ['build_inside_flow','reusable_graph_only','joint_build_inside_flow']
    assert config['domain_mode'] in ['unrestricted','paired']
    assert not config['domain_feedback'] or config['domain_mode']=='paired'
    assert config['seed_order'] in ['native','rr_id','delay_rr_id']
    for key in list(os.environ):
        if key.startswith('VPR_'):del os.environ[key]
    files={str(Path(k).resolve()):v for k,v in config['input_sha256'].items()}
    for path,h in files.items():assert sha(path)==h,path
    binary=D/'native_resource_census_stage_01/bin/vpr'
    assert sha(binary)==read(D/'native_resource_census_stage_01/binding.json')['binary_sha256']
    original_command=list(config['route_command']);assert '--route' in original_command and '--analysis' in original_command
    assert Path(original_command[0]).resolve()==binary
    graph=Path(original_command[original_command.index('--read_rr_graph')+1])
    # The route pathname in a template is an output placeholder, never an input.
    assert config['initial_route_imported'] is False
    stages=[]
    write(b/'registration.json',dict(config=str(args.config.resolve()),config_sha256=sha(args.config),
        source_sha256=files,initial_route_imported=False,cache_mode=config['cache_mode'],
        qualification='Fixed configuration; no result reuse. Runtime source hashing, graph loads/builds, candidate evaluation, rejections, rollback and final input gates all stay inside the outer measured command.'))

    def invoke(name,command,timeout=1800):
        begin=time.monotonic()
        with (b/(name+'.log')).open('w') as log:
            child=subprocess.Popen(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            write(b/'active_child.json',dict(pid=child.pid,start_ticks=Path(f'/proc/{child.pid}/stat').read_text().split(') ',1)[1].split()[19],phase=name,command=list(map(str,command))))
            try:code=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGTERM)
                try:code=child.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
                stages.append(dict(phase=name,status='timeout',returncode=code,complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
                raise TimeoutError(name)
        stages.append(dict(phase=name,status='completed' if code==0 else 'failed',returncode=code,complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
        assert code==0,(name,code)

    if config['cache_mode']=='joint_build_inside_flow':
        joint=b/'joint_graph_indexes'
        invoke('joint_graph_index_generation',[sys.executable,D/'build_joint_graph_indexes_v1.py','--graph',graph,'--output',joint])
        generated=read(joint/'completion.json');assert generated['passed'] and generated['XML_traversals']==1
        assert generated['graph_sha256']==sha(graph)
        audit=b/'graph_audit_cache';full=b/'full_graph_cache'
        audit.symlink_to(joint/'audit_cache',target_is_directory=True)
        full.symlink_to(joint/'full_cache',target_is_directory=True)
        assert audit.resolve().is_relative_to(b) and full.resolve().is_relative_to(b)
    elif config['cache_mode']=='build_inside_flow':
        audit=b/'graph_audit_cache';full=b/'full_graph_cache'
        invoke('build_audit_cache',[sys.executable,D/'immutable_rr_audit_cache.py','--graph',graph,'--output',audit])
        invoke('build_full_cache',[sys.executable,D/'full_route_graph_cache.py','--parent',audit,'--output',full])
    else:
        full=Path(config['full_graph_cache']).resolve()
        assert str(full/'completion.json') in files
    io.BASE=b/'initial';io.BASE.mkdir();rd=io.BASE/'runs/state';rd.mkdir(parents=True)
    begin=time.monotonic();command=list(original_command)
    for option,name in [('--net_file','packed.net'),('--place_file','placed.place')]:
        src=Path(command[command.index(option)+1]);assert str(src.resolve()) in files
        shutil.copy2(src,rd/name);command[command.index(option)+1]=str(rd/name)
    command[command.index('--route_file')+1]=str(rd/'routed.route')
    assert not (rd/'routed.route').exists()
    # Resolve this binary's actual libraries instead of copying a historical runtime list.
    runtime={}
    linked=subprocess.run(['ldd',str(binary)],capture_output=True,text=True,check=True).stdout
    assert 'not found' not in linked
    for line in linked.splitlines():
        tokens=line.split('=>')[-1].split()
        if tokens and tokens[0].startswith('/'):
            lib=Path(tokens[0]).resolve();runtime[str(lib)]=sha(lib)
    write(io.BASE/'runtime_dependency_binding.json',dict(missing=[],sha256=runtime,command=['ldd',str(binary)]))
    static=[binary,Path(command[1]),Path(command[2]),graph,args.config.resolve()]
    if '--sdc_file' in command:
        sdc=Path(command[command.index('--sdc_file')+1]).resolve()
        assert str(sdc) in files and sha(sdc)==files[str(sdc)]
        static.append(sdc)
    result=io.run('state',command,frozen=static,private_inputs=[rd/'packed.net',rd/'placed.place'],
        environment={'VPR_H3D_MODE':'off','VPR_H3D_FINAL_STA_TRACE':str(rd/'native_sta_frontier.jsonl')},
        timeout=1800,tags=dict(phase='fresh_initial_route',initial_route_imported=False))
    assert result['status']=='completed' and result['metrics'].get('native_full_check_passed')
    assert result['metrics'].get('routing_success_reported')
    # Fresh route must use precisely the supplied netlist and placement.
    for option,name in [('--net_file','packed.net'),('--place_file','placed.place')]:
        src=Path(original_command[original_command.index(option)+1]);assert sha(rd/name)==files[str(src.resolve())]
    write(rd/'pair_check.json',dict(passed=True,scope='Exact input packing and placement after fresh routing.'))
    vector=load(rd/'native_sta_frontier.jsonl');write(io.BASE/'endpoint_vector.json',vector)
    assert float(format(vector['cpd_s']*1e9,'.6g'))==result['metrics']['critical_path_ns']
    cache=FullRouteGraphCache(graph,full);oldbase=study.BASE;reader=study.cr.read_graph_evidence
    study.BASE=io.BASE;study.cr.read_graph_evidence=cache.evidence
    try:audit_result=study.audit_batch({'fixture':{'original_graph':str(graph)}},[result],io.BASE/'physical_audit.json')
    finally:study.BASE=oldbase;study.cr.read_graph_evidence=reader
    assert audit_result['passed'] and audit_result['legal_count']==1
    io.seal_inputs(io.BASE/'input_seal.json')
    write(io.BASE/'completion.json',dict(passed=True,status='fresh_route_FULL_STA_physical_terminal',run=str(rd),
        initial_route_imported=False,full_precision_cpd_s=vector['cpd_s'],route_body_sha256=route_body(rd/'routed.route'),
        source_sha256={str(p):sha(p) for p in [rd/'manifest.json',rd/'independent_audit.json',io.BASE/'input_seal.json']},
        qualification='Fresh route and final native STA; independent physical audit uses only the bound graph index. Not an imported historical route.'))
    stages.append(dict(phase='fresh_route_and_materialization',status='completed',complete_process_seconds=time.monotonic()-begin));write(b/'stages.json',stages)
    del cache
    repair=b/'repair'
    command=[sys.executable,D/'run_unified_resource_repair_v1.py','--initial-state',io.BASE,'--batch',repair,'--full-graph-cache',full,'--bundle-size','8','--domain-mode',config['domain_mode'],'--seed-order',config['seed_order']]
    if config['domain_feedback']:command.append('--domain-feedback')
    assert type(config['owner_escalation']) is bool
    assert config['owner_domain_mode']=='unrestricted_in_both_arms' and config['owner_rank_windows']==3
    command += ['--owner-rank-windows',str(config['owner_rank_windows'])]
    if not config['owner_escalation']:command.append('--disable-owner-escalation')
    # Each nested native job already has its normal 1800s guard. The complete
    # multi-step algorithm is not truncated by a total runtime/call-count cap.
    invoke('resource_repair',command,timeout=None)
    terminal=read(repair/'completion.json');assert terminal['passed']
    final=Path(terminal['final_state']);assert read(final/'completion.json')['passed']
    for path,h in files.items():assert sha(path)==h,path
    write(b/'completion.json',dict(passed=True,initial_state=str(io.BASE),final_state=str(final),
        config=str(args.config.resolve()),config_sha256=sha(args.config),cache_mode=config['cache_mode'],
        domain_mode=config['domain_mode'],initial_CPD_s=vector['cpd_s'],final_CPD_s=terminal['final_CPD_s'],
        final_resources=terminal['final_resources'],accepted_steps=terminal['accepted_steps'],
        complete_driver_seconds=time.monotonic()-started,complete_outer_measurement='See sibling measurement/completion.json',
        source_sha256={str(p):sha(p) for p in [args.config.resolve(),io.BASE/'completion.json',repair/'completion.json',b/'stages.json']},
        owner_escalation=config['owner_escalation'],owner_commits=terminal['owner_commits'],backend='unified_resource_owner_with_same_run_joint_graph_indexes',seed_order=config['seed_order'],domain_feedback=config['domain_feedback'],qualification='Quality and complete outer wall/memory belong to this exact execution and output. Cold means fresh process state with graph indexes built inside when selected; OS cache is uncontrolled. Packing/placement/architecture generation and one-time source development are explicit upstream inputs, not secretly included.'))
    print(dict(passed=True,final_CPD_s=terminal['final_CPD_s'],resources=terminal['final_resources']),flush=True)


if __name__=='__main__':main()
