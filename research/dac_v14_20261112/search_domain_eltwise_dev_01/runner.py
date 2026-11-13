#!/usr/bin/env python3
"""Registered trace-off reproduction then trace-on native equivalence pair."""
import fcntl,os,shutil,socket,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body,normalized_command,require_formal_terminal
from bounded_critical_records import records
from routing_log_metrics import ROW
ROOT=D.parents[1];OLD=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0]=[str(OLD/'execution_scripts'),str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from audit_final_guides import audit as guide_audit

def original(lines):return records([l for l in lines if not l.startswith('H3D_SEARCH_DOMAIN')])
def check(rd,ref):
    a,b=read(rd/'manifest.json'),read(ref/'manifest.json');x,y=(rd/'stdout.log').read_text().splitlines(),(ref/'stdout.log').read_text().splitlines()
    checks=dict(status=a['status']==b['status']=='completed',metrics=all(a['metrics'].get(k)==b['metrics'].get(k) for k in ['critical_path_ns','iterations','wirelength','routing_success_reported','native_full_check_passed']),route=route_body(rd/'routed.route')==route_body(ref/'routed.route'),guide=sha(rd/'h3d_final_guides.csv')==sha(ref/'h3d_final_guides.csv'),records=original(x)==original(y),prefix=[l for l in x if l.startswith('H3D_PREFIX_')]==[l for l in y if l.startswith('H3D_PREFIX_')],rows=[l.split()[:1]+l.split()[2:] for l in x if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in y if ROW.match(l)],actual_influence=[l for l in x if l.startswith('H3D_GUIDE_INFLUENCE_')]==[l for l in y if l.startswith('H3D_GUIDE_INFLUENCE_')])
    return dict(passed=all(checks.values()),checks=checks,reference=str(ref),qualification='Known measured elapsed fields excluded; original cost/query/table/heap/prefix, numeric iteration rows, influence and full physical route/guide exact.')

def main():
    require_formal_terminal();lock=(D/'critical_scope_runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stage=D/'search_domain_stage_02';v=read(stage/'binding.json');assert sha(stage/'bin/vpr')==v['binary_sha256'] and all(sha(stage/'src'/p)==h for p,h in v['source_sha256'].items())
    ref=D/'bounded_cap_eltwise_dev_01/runs/eltwise_layer_C';assert read(ref.parent.parent/'input_seal.json')['passed'];pm=read(ref/'manifest.json');assert pm['status']=='completed'
    b=D/'search_domain_eltwise_dev_01';b.mkdir(exist_ok=False);(b/'bin').mkdir();shutil.copy2(stage/'bin/vpr',b/'bin/vpr');shutil.copytree(stage/'src',b/'source');shutil.copy2(stage/'binding.json',b/'candidate_binding.json');shutil.copy2(__file__,b/'runner.py');shutil.copy2(OLD/'runtime_dependency_binding.json',b/'runtime_dependency_binding.json')
    reg=dict(protocol=read(D/'search_domain_experiment_01.json'),reference=str(ref),binary_sha256=v['binary_sha256'],source_sha256=v['source_sha256'],runner_sha256=sha(__file__),support_scripts_sha256={m.__file__:sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.endswith('.py') and str(ROOT) in m.__file__},arms=['C','T'],pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],host=socket.gethostname(),timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)
    write(b/'registration.json',reg);io.BASE=b;io.ADDRESS_SPACE_BYTES=reg['memory_bytes'];ctx=study.context('eltwise_layer','hybrid_o',11,100)
    for p in [Path(__file__),stage/'binding.json',D/'search_domain_experiment_01.json',ref.parent.parent/'input_seal.json',ref/'manifest.json',ref/'independent_audit.json',ref/'final_guide_audit.json']:io.frozen_hash(p,sha(p))
    for p,h in reg['support_scripts_sha256'].items():io.frozen_hash(p,h)
    for p,h in pm['shared_inputs'].items():io.frozen_hash(p,h['sha256'])
    for n,h in pm['outputs'].items():io.frozen_hash(ref/n,h['sha256'])
    io.frozen_hash(ref/'h3d_final_guides.csv',read(ref/'final_guide_audit.json')['trace_sha256'])
    receipts=[];gates={}
    for a in reg['arms']:
        assert shutil.disk_usage(D).free>=reg['disk_reserve_bytes'];rd=b/'runs'/('eltwise_layer_'+a);rd.mkdir(parents=True)
        for n in ['packed.net','placed.place']:shutil.copy2(ref/n,rd/n)
        cmd=list(pm['command']);cmd[0]=str(b/'bin/vpr')
        for opt,n in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/n)
        assert normalized_command(cmd)==normalized_command(pm['command'])
        env=dict(pm['environment'],VPR_H3D_TRACE_SEARCH_DOMAIN='0' if a=='C' else '1')
        assert 'VPR_H3D_BOUNDED_CRITICAL_GUIDE' not in env
        m=io.run(rd.name,cmd,environment=env,timeout=reg['timeout'],frozen=[cmd[0],cmd[1],cmd[2],cmd[cmd.index('--read_rr_graph')+1],b/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],tags=dict(circuit='eltwise_layer',arm=a,phase='development',hypothesis='actual_native_source_and_bb_diagnostic'))
        receipts.append(m);write(rd/'pair_check.json',dict(passed=all(sha(rd/n)==sha(ref/n) for n in ['packed.net','placed.place'])))
        comparison=check(rd,ref if a=='C' else b/'runs/eltwise_layer_C') if m['status']=='completed' else dict(passed=False,status=m['status'])
        gates[a]=comparison;write(rd/'trace_reproduction.json',comparison)
        if not comparison['passed']:break
    study.BASE=b;study.audit_batch(ctx,receipts,b/'independent_search_domain_native_audit.json')
    for m in receipts:
        if m['status']=='completed' and m['metrics'].get('native_full_check_passed'):guide_audit(b/'runs'/m['name'])
    io.seal_inputs(b/'input_seal.json');write(b/'completion.json',dict(status='search_domain_pair_terminal_not_research_complete',gate_passed=all(x['passed'] for x in gates.values()),disabled_gate_passed=gates.get('C',{}).get('passed',False),gates=gates,missing_arms=[a for a in reg['arms'] if a not in [m['tags']['arm'] for m in receipts]]));print('pair gates',gates,flush=True)
if __name__=='__main__':main()
