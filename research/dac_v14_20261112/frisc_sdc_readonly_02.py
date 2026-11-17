"""Exact missing-SDC-report-field reconciliation; reuse frozen checks and raw gates."""
import argparse
import ast
import collections
import fcntl
import hashlib
import inspect
import json
import os
import sys
import textwrap
import time
import traceback
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D/'FRISC_sdc_readonly_02'
COHORT=D/'cp1r5_frisc_pair_01'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')


def transform(source):
    tree=ast.parse(source);asserts=sum(isinstance(n,ast.Assert) for n in ast.walk(tree))
    class Rewrite(ast.NodeTransformer):
        def __init__(self):self.paths=collections.Counter();self.specs=0
        def visit_BinOp(self,node):
            if isinstance(node.op,ast.Div) and isinstance(node.left,ast.Name) and node.left.id=='root' and isinstance(node.right,ast.Constant) and node.right.value in ['metadata_consumers.json','completion.json','queue/completion.json','queue/status.json']:
                self.paths[node.right.value]+=1;node.left=ast.Name(id='__audit_output',ctx=ast.Load())
            return self.generic_visit(node)
        def visit_Subscript(self,node):
            if isinstance(node.value,ast.Name) and node.value.id=='config' and isinstance(node.slice,ast.Constant) and node.slice.value=='explicit_sdc_spec':
                self.specs+=1;return ast.copy_location(ast.Name(id='__bound_sdc_spec',ctx=ast.Load()),node)
            return self.generic_visit(node)
    change=Rewrite();tree=change.visit(tree);ast.fix_missing_locations(tree)
    assert change.specs==1 and dict(change.paths)=={'metadata_consumers.json':2,'completion.json':3,'queue/completion.json':1,'queue/status.json':1}
    assert sum(isinstance(n,ast.Assert) for n in ast.walk(tree))==asserts
    assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='write' for n in ast.walk(tree))==4
    return tree,dict(all_original_assertions_retained=asserts,report_metadata_lookups_replaced=1,output_paths_redirected=dict(change.paths),scientific_gates_modified=0)


def replay(arm):
    plan=read(ROOT/'plan.json');assert all(sha(p)==h for p,h in plan['source_sha256'].items())
    case=Path(plan['targets'][arm]['case']);audit=ROOT/'supplement/cases/frisc'/arm;audit.mkdir(parents=True)
    output=audit/'replayed_verifier';output.mkdir();(output/'queue').mkdir()
    original=read(COHORT/'frisc_results.json')[arm]
    assert original['command_returncode']==0 and original['status']=='execution_or_verification_failed'
    assert "KeyError: 'explicit_sdc_spec'" in (case/'verification.log').read_text()
    config=read(case/'config.json');assert 'explicit_sdc_spec' not in config
    sdc=Path(config['route_command'][config['route_command'].index('--sdc_file')+1])
    upstream=D/'VTR_frisc_input_01';registration=read(upstream/'registration.json')
    assert sha(sdc)==sha(upstream/'inputs/frisc.sdc')==registration['source_sha256'][str(upstream/'inputs/frisc.sdc')]
    lines=[x.strip() for x in sdc.read_text().splitlines() if x.strip() and not x.lstrip().startswith('#')]
    assert lines==['create_clock -period 20 [get_ports {pclk}]'] and registration['clock_period_ns']==20
    spec=dict(source='actual preregistered SDC bytes',clock_port='pclk',clock_period_ns=20,
        explicit_input_delay=None,explicit_output_delay=None,IO_qualification='No I/O delay command supplied; report native observed vectors without inventing a delay constraint.',
        application_requirement=False,sdc_sha256=sha(sdc))
    write(audit/'SDC_report_declaration.json',spec)
    sensitive=[COHORT/'frisc_results.json',case/'config.json',case/'verification.log',case/'metadata_consumers.json',
        *case.glob('queue/*.json'),upstream/'registration.json',upstream/'inputs/frisc.sdc',sdc]
    originals={str(p):sha(p) for p in sensitive if p.exists()}
    release=Path(plan['release']);verifier=release/'runtime/verify_complete_unified_method_v1.py'
    tree,shape=transform(verifier.read_text());assert shape==plan['transformation']
    start=time.monotonic();sys.dont_write_bytecode=True;sys.path.insert(0,str(release/'runtime'))
    sys.argv=[str(verifier),'--root',str(case)]
    # A replay may write only its four redirected output files. No solver process is allowed.
    def guard(event,args):
        if event in ['subprocess.Popen','os.system','os.exec','os.posix_spawn']:raise RuntimeError('Readonly replay cannot launch processes')
        if event=='open':
            path,mode,flags=args
            if isinstance(path,(str,bytes,os.PathLike)) and ((isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):
                assert Path(path).resolve().is_relative_to(audit),'Write outside isolated replay'
    sys.addaudithook(guard)
    error=None;passed=False
    try:
        exec(compile(tree,str(verifier),'exec'),dict(__name__='__readonly_replay__',__file__=str(verifier),__audit_output=output,__bound_sdc_spec=spec))
        passed=read(output/'completion.json')['passed']
    except Exception:error=traceback.format_exc();(audit/'failure.log').write_text(error)
    unchanged=all(sha(p)==h for p,h in originals.items());assert unchanged
    write(audit/'completion.json',dict(passed=bool(passed and unchanged),original_frozen_result_unchanged=unchanged,
        original_verification_status=original['status'],original_frozen_verifier_relabelled=False,
        transformation=shape,error=error,new_native_or_STA_calls=0,complete_replay_seconds=time.monotonic()-start,
        source_sha256={**originals,str(ROOT/'plan.json'):sha(ROOT/'plan.json'),str(verifier):sha(verifier),str(audit/'SDC_report_declaration.json'):sha(audit/'SDC_report_declaration.json')},
        qualification='All original frozen checks retained; only a missing report-only declaration is supplied from original preregistered SDC bytes. Outputs isolated. Original failed checker remains failed; raw request/STA/physical/pair admission is separately required.'))
    assert passed,error


def raw_role(arm):
    import admit_cp1r5_frisc_pair_01 as timing
    import admit_cp1r5_frisc_base_01 as base
    from recovery_prefix_v1 import Evidence
    base.ROOT=ROOT
    e=Evidence();plan=base.prerequisites(e);target=plan['targets'][arm]
    out=ROOT/arm;out.mkdir();start=time.monotonic()
    try:
        original_path=COHORT/'frisc_results.json';e.bind(original_path);original=read(original_path)[arm]
        source=textwrap.dedent(inspect.getsource(base.raw.Audit.case))
        namespace={**base.raw.__dict__,'ROOT':COHORT,'SUPPLEMENT':ROOT/'supplement'}
        exec(compile(source,str(Path(__file__).resolve())+'::unchanged_raw_case','exec'),namespace)
        parent=timing.audit_class()
        class SupplementAudit(parent):pass
        SupplementAudit.case=namespace['case']
        audit=SupplementAudit(plan['release'],e);result=audit.case(target,original,out)
        result['state_chain']=base.state_chain(audit,Path(target['case']));e.unchanged()
    except Exception:
        error=traceback.format_exc();(out/'failure.log').write_text(error)
        result=dict(passed=False,quality_admitted=False,quality=None,status='supplementary_raw_requires_reconciliation',error=error)
    result.update(arm=arm,complete_readonly_seconds=time.monotonic()-start,source_sha256=e.bound,new_native_or_STA_calls=0,historical_receipts_rewritten=False)
    write(out/'completion.json',result)


def run():
    from seed_census_analysis_pool_v2 import process_identity
    from recovery_prefix_v1 import live_identity
    from measure_process_tree_v1 import measure
    q=ROOT/'queue';q.mkdir();write(q/'registration.json',dict(**process_identity(os.getpid()),plan_sha256=sha(ROOT/'plan.json')))
    start=time.monotonic();rows=[]
    for predecessor in [COHORT/'queue',D/'FRISC_complete_admission_01/queue']:
        r=read(predecessor/'registration.json');assert not live_identity(r['pid'],r['start_ticks']) and (predecessor/'completion.json').exists()
    try:
        for phase,arm in [('replay','native'),('replay','domain'),('raw','native'),('raw','domain'),('pair','pair')]:
            name=phase+'_'+arm;write(q/'status.json',dict(status='running_registered_readonly_stage',phase=name))
            command=[sys.executable,'-B',str(Path(__file__).resolve()),'--phase',phase,'--arm',arm]
            m=measure(command,ROOT/(name+'_measurement'))
            p=(ROOT/'supplement/cases/frisc'/arm/'completion.json') if phase=='replay' else ROOT/arm/'completion.json'
            r=read(p) if p.exists() else {};rows.append(dict(stage=name,returncode=m['returncode'],passed=bool(m['passed'] and r.get('passed')),complete_command_seconds=m['complete_command_wall_seconds'],result=str(p),new_native_or_STA_calls=0));write(ROOT/'stages.json',rows)
            assert not m['live_descendants_after_command_exit']
            if phase=='replay':assert rows[-1]['passed'],'Preserve exact replay failure; do not run dependent raw audit'
        write(q/'completion.json',dict(passed=all(x['passed'] for x in rows),stages=rows,complete_queue_seconds=time.monotonic()-start,new_native_or_STA_calls=0,matched_complete_quality_pair=read(ROOT/'pair/completion.json').get('matched_complete_quality_pair',False)))
        write(q/'status.json',dict(status='terminal'))
    except BaseException as e:
        write(q/'completion.json',dict(passed=False,error=repr(e),stages=rows,complete_queue_seconds=time.monotonic()-start,automatic_retry=False));write(q/'status.json',dict(status='terminal_reconciliation_required'));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['run','replay','raw','pair'],required=True);p.add_argument('--arm',choices=['native','domain','pair']);a=p.parse_args()
    if a.phase=='run':run()
    else:
        with (D/'critical_scope_runner.lock').open() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if a.phase=='replay':replay(a.arm)
            elif a.phase=='raw':raw_role(a.arm)
            else:
                import admit_cp1r5_frisc_base_01 as base
                base.ROOT=ROOT;base.pair()
