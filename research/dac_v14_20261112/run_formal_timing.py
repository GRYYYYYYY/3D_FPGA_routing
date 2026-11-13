#!/usr/bin/env python3
"""Immutable rotated A0/R1/U-view timing; no retries or historical speedup ratios."""
import argparse, fcntl, hashlib, json, os, re, shutil, socket, sys, time
from pathlib import Path
D = Path(__file__).resolve().parent
ROOT = D.parents[1]
OLD = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
sys.path[:0] = [str(OLD/'execution_scripts'), str(ROOT/'scripts')]
import flatland_timing_io_candidate as io
import flatland_benchmark as study
from lazagna_common import sha256, utc, write_json

CASES = [('spmv','feedback_dev_01','U'), ('softmax','feedback_dev_01','U'),
         ('eltwise_layer','closure_view_dev_01','V'), ('bnn','view_confirmation_dev_01','V'),
         ('gemm_layer','view_gemm_dev_01','V')]
ORDERS = [['A0','R1','U'], ['R1','U','A0'], ['U','A0','R1']]

def read(p): return json.loads(Path(p).read_text())
def ticks(pid): return Path(f'/proc/{pid}/stat').read_text().split()[21]
def body_hash(p):
    # Streaming: route headers differ, complete net records must match exactly.
    digest = hashlib.sha256(); started = False
    with Path(p).open('rb') as f:
        for line in f:
            if line.startswith(b'Net '): started = True
            if started: digest.update(line)
    assert started, p
    return digest.hexdigest()

def normalized(command):
    result = list(command[1:])
    for opt in ['--net_file','--place_file','--route_file']:
        result[result.index(opt)+1] = '<paired-private-file>'
    return result

def live_heavy():
    rows = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid(): continue
        try:
            comm = (p/'comm').read_text().strip()
            cmd = (p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if comm == 'vpr' or (str(ROOT) in cmd and any(s in cmd for s in ['audit_', 'run_layer_bbox.py', 'make -j', 'cc1plus', 'lto1'])):
                rows.append(dict(pid=int(p.name),comm=comm,start_ticks=ticks(int(p.name))))
        except (OSError, IndexError): pass
    return rows

def prepare(out):
    out.mkdir(exist_ok=False); (out/'bin').mkdir(); (out/'references').mkdir()
    shutil.copy2(__file__,out/'runner.py')
    shutil.copy2(D/'FORMAL_TIMING_PROTOCOL.md',out/'protocol.md')
    shutil.copy2(OLD/'runtime_dependency_binding.json',out/'runtime_dependency_binding.json')
    validation = read(OLD/'seccomp_full_workload_validation.json')
    assert validation['status'] == 'passed'
    assert sha256(io.__file__) == validation['timing_runner_sha256']
    assert sha256(io.GUARD) == validation['guard_sha256']
    # Bind existing workload-level qualification, not just its earlier unit label.
    for p, expected in validation['evidence_sha256'].items(): io.frozen_hash(p,expected)
    io.frozen_hash(OLD/'seccomp_full_workload_validation.json')
    selected = read(OLD/'selected_configs.json')['selections']['hybrid_o']['R1']['environment']
    stage = D/'closure_view_candidate_01'
    shutil.copy2(stage/'binding.json',out/'candidate_binding.json')
    shutil.copy2(stage/'CMakeCache.txt',out/'CMakeCache.txt')
    shutil.copytree(stage/'src',out/'source')
    specs = {}
    for circuit,batch,arm in CASES:
        ctx = study.context(circuit,'hybrid_o',11,100)
        stem = f'training_{circuit}_s11_hybrid_o_n{ctx["size"]}_w100_p0'
        paths = {'A0':OLD/'runs'/f'{stem}_a0','R1':OLD/'runs'/f'{stem}_delay_critical_c6',
                 'U':D/batch/'runs'/f'{circuit}_{arm}'}
        assert read(D/batch/'input_seal.json')['passed']
        manifests = {a:read(p/'manifest.json') for a,p in paths.items()}
        base = manifests['R1']; refs = {}; commands = {}; environments = {}
        for a,rd in paths.items():
            m = manifests[a]; audit = read(rd/'independent_audit.json')
            assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit['audit']['passed']
            assert normalized(m['command']) == normalized(base['command'])
            assert all(sha256(rd/f)==sha256(paths['R1']/f) for f in ['packed.net','placed.place'])
            inputs = [m['command'][1],m['command'][2],m['command'][m['command'].index('--read_rr_graph')+1]]
            for path in inputs: io.frozen_hash(path,m['shared_inputs'][path]['sha256'])
            for name in ['manifest.json','routed.route','packed.net','placed.place','independent_audit.json']:
                io.frozen_hash(rd/name)
            assert sha256(rd/'routed.route') == m['outputs']['routed.route']['sha256']
            if a=='U':
                assert read(rd/'final_guide_audit.json')['passed']
                source_binary = stage/'bin/vpr'
            else:
                source_binary = Path(m['command'][0]); io.frozen_hash(source_binary,m['shared_inputs'][str(source_binary)]['sha256'])
            target_binary = out/'bin'/f'vpr_{a}'
            if not target_binary.exists(): shutil.copy2(source_binary,target_binary)
            assert sha256(target_binary)==sha256(source_binary)
            commands[a] = list(base['command']); commands[a][0]=str(target_binary)
            env = {} if a=='A0' else dict(selected)
            if a=='U': env.update(VPR_H3D_FEEDBACK='1',VPR_H3D_GENERATION_CLOSURE='1',VPR_H3D_SHARED_CLOSURE='1',VPR_H3D_COMPACT_CLOSURE='1',VPR_H3D_CLOSURE_VIEW='1')
            assert not any(k in env for k in ['VPR_H3D_TRACE_TABLE','VPR_H3D_FINAL_TRACE','VPR_H3D_PLAN_PROFILE','VPR_H3D_ALL_LAYER_BB'])
            environments[a]=env
            refs[a]=dict(path=str(rd),manifest_sha256=sha256(rd/'manifest.json'),route_body_sha256=body_hash(rd/'routed.route'),
                         independent_audit_sha256=sha256(rd/'independent_audit.json'),metrics=m['metrics'],physical_metrics=audit['physical_metrics'])
        inp=out/'references'/circuit;inp.mkdir()
        for name in ['packed.net','placed.place']:shutil.copy2(paths['R1']/name,inp/name)
        specs[circuit]=dict(commands=commands,environments=environments,references=refs,private_input=str(inp),
            physical_inputs={p:io.frozen_hash(p)['sha256'] for p in inputs},private_hashes={f:sha256(inp/f) for f in ['packed.net','placed.place']})
    cpu=min(os.sched_getaffinity(0))
    reg=dict(utc=utc(),status='prepared_not_started',hypothesis='Same-environment end-to-end cost of full feedback plus exact closure views versus frozen A0/R1; legacy layer scope, separate from new search-scope branch.',
             circuits=[c for c,_,_ in CASES],arms=['A0','R1','U'],orders=ORDERS,specs=specs,cpu=cpu,
             allowed_cpus=sorted(os.sched_getaffinity(0)),host=socket.gethostname(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             cpu_model=[s for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')][:1],
             cgroup={p:Path(p).read_text().strip() for p in ['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/memory.max'] if Path(p).exists()},
             binary_sha256={a:sha256(out/'bin'/f'vpr_{a}') for a in ['A0','R1','U']},runner_sha256=sha256(__file__),
             support_sha256={str(Path(m.__file__).resolve()):sha256(m.__file__) for m in [io,study]},
             guard_qualification=validation['status'],guard_validation_sha256=sha256(OLD/'seccomp_full_workload_validation.json'),
             timeout=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,
             timing_scope='Whole process through existing time/prlimit/seccomp/observer wrapper; includes read/init/plan/route/STA; prewarm excluded. Fixed CPU includes observer overhead, same on every arm. Shared-host contention cannot be excluded; load recorded. No ratio to historical times.',
             population='Five previously seen mutually legal development circuits, not blind success-rate population; attention remains failed in sixcase quality aggregate.45roles are this design, not research stop condition.')
    write_json(out/'registration.json',reg)
    io.seal_inputs(out/'admission_input_seal.json')
    print('prepared',out,flush=True)

def run(out):
    reg=read(out/'registration.json');assert reg['runner_sha256']==sha256(__file__)
    assert reg['host']==socket.gethostname()
    assert reg['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    lock=(D/'formal_timing.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (out/'started.json').exists(),'No automatic duplicate or interrupted-batch restart'
    assert not live_heavy(), 'Development workloads still active'
    for p,x in read(out/'admission_input_seal.json')['inputs'].items():io.frozen_hash(p,x['sha256'])
    for p,digest in reg['support_sha256'].items():assert sha256(p)==digest
    io.BASE=out;io.ADDRESS_SPACE_BYTES=reg['memory_bytes']
    os.sched_setaffinity(0,{reg['cpu']})
    identity=dict(pid=os.getpid(),start_ticks=ticks(os.getpid()),host=socket.gethostname(),out=str(out),utc=utc(),cpu=reg['cpu'])
    write_json(out/'started.json',identity);write_json(D/'formal_timing_active.json',dict(status='active',**identity))
    rows=[];mismatches=[];gated=set()
    try:
        for circuit in reg['circuits']:
            spec=reg['specs'][circuit]
            for repeat,order in enumerate(reg['orders']):
                for position,arm in enumerate(order):
                    name=f'{circuit}_r{repeat}_{arm}'
                    if circuit in gated:
                        rows.append(dict(circuit=circuit,repeat=repeat,arm=arm,status='missing_case_quality_gate',name=name));continue
                    if live_heavy():raise RuntimeError('Concurrent development workload; preserve measured trials, require diagnosis')
                    assert shutil.disk_usage(out).free >= reg['disk_reserve_bytes']
                    rd=out/'runs'/name;rd.mkdir(parents=True)
                    for f,digest in spec['private_hashes'].items():
                        shutil.copy2(Path(spec['private_input'])/f,rd/f);assert sha256(rd/f)==digest
                    cmd=list(spec['commands'][arm]);assert sha256(cmd[0])==reg['binary_sha256'][arm]
                    for opt,f in [('--net_file','packed.net'),('--place_file','placed.place'),('--route_file','routed.route')]:cmd[cmd.index(opt)+1]=str(rd/f)
                    warm_start=time.monotonic();warm_bytes=0
                    for p in list(spec['physical_inputs'])+[str(rd/'packed.net'),str(rd/'placed.place')]:
                        if p in spec['physical_inputs']:io.frozen_hash(p,spec['physical_inputs'][p])
                        with open(p,'rb') as f:
                            while block:=f.read(8*1024**2):warm_bytes+=len(block)
                    write_json(rd/'environment.json',dict(utc=utc(),affinity=sorted(os.sched_getaffinity(0)),load=os.getloadavg(),
                        prewarm_bytes=warm_bytes,prewarm_seconds=time.monotonic()-warm_start,cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text()))
                    m=io.run(name,cmd,environment=spec['environments'][arm],timeout=reg['timeout'],
                        frozen=[cmd[0],*spec['physical_inputs'],out/'registration.json'],private_inputs=[rd/'packed.net',rd/'placed.place'],
                        tags=dict(circuit=circuit,arm=arm,repeat=repeat,position=position,phase='formal_rotated_timing'))
                    ref=spec['references'][arm];old=Path(ref['path'])
                    checks=dict(native_full=m['status']=='completed' and m['metrics'].get('native_full_check_passed',False),
                        packed=sha256(rd/'packed.net')==spec['private_hashes']['packed.net'],placed=sha256(rd/'placed.place')==spec['private_hashes']['placed.place'],
                        metrics=all(m['metrics'].get(k)==ref['metrics'].get(k) for k in ['critical_path_ns','wirelength','iterations']),
                        route_body=(rd/'routed.route').exists() and body_hash(rd/'routed.route')==ref['route_body_sha256'],
                        reference_audit=sha256(old/'independent_audit.json')==ref['independent_audit_sha256'])
                    passed=all(checks.values());status='legal' if passed else m['status'] if m['status']!='completed' else 'quality_mismatch_pending_audit'
                    write_json(rd/'quality_reuse.json',dict(passed=passed,checks=checks,scope='REUSED independent graph audit only when complete physical inputs, packed/place, native FULL, route body and metrics match. No new graph traversal claimed.',reference=ref,physical_inputs=spec['physical_inputs']))
                    if not passed:
                        gated.add(circuit);mismatches.append((circuit,m))
                    log=(rd/'stdout.log').read_text();plan=re.findall(r'^H3D_PLAN .*?planning_seconds=([\d.]+)',log,re.M)
                    rows.append(dict(circuit=circuit,repeat=repeat,position=position,arm=arm,name=name,status=status,path=str(rd),metrics=m['metrics'],
                        planning_seconds=float(plan[-1]) if plan else 0. if arm=='A0' else None,process_seconds=m['wall_seconds'],physical_metrics=ref['physical_metrics'] if passed else None))
                    write_json(out/'observations.json',rows)
        # Expensive new graph audit only after all timing trials, if reproduction failed.
        for circuit,m in mismatches:
            if m['status']=='completed':
                study.BASE=out;study.audit_batch(study.context(circuit,'hybrid_o',11,100),[m],out/f'{m["name"]}_mismatch_audit.json')
        io.seal_inputs(out/'input_seal.json')
        write_json(out/'observations.json',rows)
        write_json(out/'completion.json',dict(utc=utc(),status='timing_batch_terminal_not_research_complete',roles=len(rows),gated_cases=sorted(gated)))
    finally:
        write_json(D/'formal_timing_active.json',dict(status='terminal' if (out/'completion.json').exists() else 'interrupted_requires_diagnosis',**identity))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--prepare',action='store_true');args=ap.parse_args()
    out=D/args.out
    if args.prepare:prepare(out)
    else:run(out)
