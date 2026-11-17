"""Isolated read-only replay of frozen checks with an explicit seal audit.

Register before further cohort outcomes. Execution is manual, only after the
original cohort terminates and a nonblocking acquisition of its shared slot.
There is no new queue owner and no native/STA call. Original failure receipts
remain authoritative historical results; supplemental outputs stay separate.
"""
import argparse
import ast
import collections
import fcntl
import hashlib
import json
import resource
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from owner_registration_transition_v1 import verify_transition

D=Path(__file__).resolve().parent
OUT=D/'CP1r3_supplemental_verifier_01'
COHORT=D/'cp1r3_distinct_input_cohort_01'
FROZEN_SHA='6cb7aba8fa27e4f994e8561ee6294382e9673c9cd523eae6f6dee56c6132e7b0'
SEAL="prep['passed'] and prep['transaction_registered'] and prep['registration_sha256'] == sha(tx / 'registration.json')"
OUTPUT_COUNTS={'metadata_consumers.json':2,'completion.json':3,'queue/completion.json':1,'queue/status.json':1}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def transformed_verifier(source):
    """Keep all other frozen checks; move only its four output destinations."""
    tree=ast.parse(source);old_assertions=sum(isinstance(n,ast.Assert) for n in ast.walk(tree))
    class Transform(ast.NodeTransformer):
        def __init__(self):self.seals=0;self.outputs=collections.Counter()
        def visit_Assert(self,node):
            if ast.dump(node.test)==ast.dump(ast.parse(SEAL,mode='eval').body):
                self.seals+=1
                node.test=ast.parse('__audit_owner_binding(preg,prep,tx,rreg,initial,root)',mode='eval').body
                return node
            return self.generic_visit(node)
        def visit_BinOp(self,node):
            if (isinstance(node.op,ast.Div) and isinstance(node.left,ast.Name) and node.left.id=='root'
                and isinstance(node.right,ast.Constant) and node.right.value in OUTPUT_COUNTS):
                self.outputs[node.right.value]+=1
                node.left=ast.Name(id='__audit_output',ctx=ast.Load())
            return self.generic_visit(node)
    change=Transform();tree=change.visit(tree)
    assert change.seals==1 and dict(change.outputs)==OUTPUT_COUNTS, 'Frozen verifier shape changed'
    assert sum(isinstance(n,ast.Assert) for n in ast.walk(tree))==old_assertions
    assert len([n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='write'])==4
    ast.fix_missing_locations(tree)
    return tree,dict(seal_checks_replaced=1,assertions_retained=old_assertions,
                     output_path_occurrences_redirected=dict(change.outputs),write_calls=4)


def register():
    assert not OUT.exists()
    plan=read(COHORT/'plan.json');release=Path(plan['release']);verifier=release/'runtime/verify_complete_unified_method_v1.py'
    assert sha(verifier)==FROZEN_SHA
    tree,shape=transformed_verifier(verifier.read_text());compile(tree,str(verifier),'exec')
    targets=[dict(input=item['id'],arm=arm,case=str(Path(item['workspace'])/arm),
                  config=item['configs'][arm],config_sha256=sha(item['configs'][arm]))
             for item in plan['inputs'] for arm in plan['fixed_arm_order']]
    assert len(targets)==6
    validation=D/'CP1r3_supplemental_verifier_validation_01/validation.json'
    assert read(validation)['passed'] and not read(validation)['actual_full_reverification_performed']
    sources=[Path(__file__).resolve(),D/'owner_registration_transition_v1.py',COHORT/'plan.json',validation,
             verifier,D/'CP1r3_lstm_native_binding_failure_audit_01/completion.json']
    OUT.mkdir()
    write(OUT/'plan.json',dict(registered_at=datetime.now(timezone.utc).isoformat(),
        status='registered_supplemental_audit_not_queued',targets=targets,release=str(release),
        release_manifest_sha256=plan['release_manifest_sha256'],
        known_result_at_registration='LSTM/native command return0 with original frozen verifier seal failure; other five original roles not completed',
        transformation=shape,source_sha256={str(p):sha(p) for p in sources},
        execution_requires_original_cohort_terminal=True,execution_requires_nonblocking_shared_lock=True,
        new_queue_owner=False,new_native_or_STA_calls=0,
        original_history_may_be_rewritten=False,full_confirmation_or_paper_benefit_not_inferred=True,
        qualification='The single changed assertion is replaced by a stronger explicit preparation/runtime/actual-execution provenance chain. Every other original frozen check remains. All writes go to a new audit namespace. This is not the original verifier passing; supplementary output alone does not replace any outstanding full-request/raw-STA/physical audit, authorize an adapter, or establish a paired benefit. Original phase, command and failed verification costs remain separate.'))
    print(dict(registered=True,targets=6,queued=False,executed=False,**shape))


def execute_case(input_name,arm):
    plan_path=OUT/'plan.json';plan=read(plan_path)
    assert all(sha(p)==h for p,h in plan['source_sha256'].items())
    terminal=COHORT/'queue_priority_02/completion.json'
    assert terminal.exists(), 'Original fixed six-role cohort has not terminated'
    target=next(t for t in plan['targets'] if t['input']==input_name and t['arm']==arm)
    serial=(D/'critical_scope_runner.lock').open('r')
    fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
    case=Path(target['case']);original_result=read(COHORT/(input_name+'_results.json'))[arm]
    assert original_result['command_returncode']==0 and read(case/'flow/completion.json')['passed']
    assert sha(target['config'])==target['config_sha256']
    measurement=read(case/'measurement/completion.json')
    assert measurement['passed'] and not measurement['live_descendants_after_command_exit']
    def live(pid,ticks):
        try:parts=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        except (FileNotFoundError,ProcessLookupError):return False
        return parts[0]!='Z' and parts[19]==str(ticks)
    assert not any(live(pid,ticks) for pid,ticks in measurement['process_identities'].items())
    audit=OUT/'cases'/input_name/arm;assert not audit.exists();audit.mkdir(parents=True)
    output=audit/'replayed_verifier';output.mkdir();rows=[]
    sensitive=[COHORT/(input_name+'_results.json'),case/'config.json',case/'verification.log',
               *[p for p in case.glob('queue/*.json')]]
    sensitive += [p for pattern in ['**/preparation.json','**/execution_registration.json'] for p in case.glob(pattern)]
    originals={str(p):sha(p) for p in sensitive if p.exists()}
    write(audit/'execution_registration.json',dict(plan_sha256=sha(plan_path),
        started_at=datetime.now(timezone.utc).isoformat(),original_result=original_result,
        original_sensitive_sha256=originals,new_native_or_STA_calls=0))
    release=Path(plan['release']);verifier=release/'runtime/verify_complete_unified_method_v1.py'
    assert sha(verifier)==FROZEN_SHA
    tree,shape=transformed_verifier(verifier.read_text())
    def owner_binding(preg,prep,tx,parent,initial,root):
        runtime=root/'flow/resource_flow/phase_runtime.json'
        assert preg==read(tx/'registration.json')
        row=verify_transition((tx/'registration.json').read_bytes(),prep,
                              read(tx/'execution_registration.json'),parent,runtime,runtime.read_bytes())
        rows.append(dict(transaction=str(tx),**row));return True
    started=time.monotonic();before=resource.getrusage(resource.RUSAGE_SELF)
    error=None;passed=False
    original_argv=list(sys.argv);original_path=list(sys.path)
    try:
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(release/'runtime'));sys.argv=[str(verifier),'--root',str(case)]
        namespace={'__name__':'__supplemental_frozen_verifier__','__file__':str(verifier),
                   '__audit_owner_binding':owner_binding,'__audit_output':output}
        exec(compile(tree,str(verifier),'exec'),namespace)
        passed=read(output/'completion.json')['passed'] is True
    except Exception:
        error=traceback.format_exc();(audit/'failure.log').write_text(error)
    finally:
        sys.argv=original_argv;sys.path[:]=original_path
    after=resource.getrusage(resource.RUSAGE_SELF)
    unchanged=all(sha(p)==h for p,h in originals.items())
    write(audit/'completion.json',dict(passed=bool(passed and unchanged),kind='supplemental_original_checks_replay',
        original_frozen_verifier_status=original_result['status'],original_frozen_result_unchanged=unchanged,
        original_frozen_verifier_relabelled=False,complete_confirmation_passed=False,
        paper_benefit_claims_authorized=False,adoption_authorized=False,
        complete_reverification_seconds=time.monotonic()-started,
        process_CPU_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        process_max_RSS_kib=after.ru_maxrss,original_algorithm_seconds=original_result['complete_seconds'],
        original_failed_or_successful_verification_seconds=original_result['independent_research_verification_seconds'],
        owner_seal_checks=rows,transformation=shape,error=error,new_native_or_STA_calls=0,
        new_queue_owner=False,source_sha256={str(plan_path):sha(plan_path),**originals},
        qualification='All unmodified frozen verifier assertions plus the explicit owner-seal transition were replayed in a separate namespace. This does not fabricate historical completion or by itself complete additional raw-request/STA/physical admission. Reverification cost is additional research cost, not an appended or reconstructed complete algorithm time.'))
    assert passed and unchanged,error


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--register',action='store_true')
    parser.add_argument('--execute-case',nargs=2,metavar=('INPUT','ARM'));args=parser.parse_args()
    assert bool(args.register)!=bool(args.execute_case)
    if args.register:register()
    else:execute_case(*args.execute_case)
