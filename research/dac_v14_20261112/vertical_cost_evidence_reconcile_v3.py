"""Independent read-only gates for the preregistered search-cost contrast.

Heavy byte/vector/tree work must run under critical_scope_runner.lock.
Importing this module never reads experiment payloads or launches native/STA.
"""
import argparse
import collections
import fcntl
import math
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from recovery_prefix_v1 import Evidence, live_identity
from cp1r3_raw_admission_v1 import Audit, parse_request, parse_native, vector_digest
from endpoint_timing_policy_streaming_v2 import load
from run_native_scope_policy_v4 import native_config

ROOT = D/'vertical_cost_baseline_dev_01'
REFERENCE = D/'robot_union_mechanism_02/transaction'
RELEASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3')


def semantic_native(text):
    """Keep all decision/tree fields; exclude only measured elapsed seconds."""
    result=[]
    for line in text.splitlines():
        f=line.split(); assert f
        if f[0]=='QUERY':
            assert len(f)==8 and math.isfinite(float(f[-1])) and float(f[-1])>=0
            f=f[:-1]
        elif f[0]=='COMPLETE':
            assert len(f)==6 and f[-1]=='occupancy_restored'
            assert math.isfinite(float(f[4])) and float(f[4])>=0
            f=f[:4]+f[5:]
        result.append(f)
    return result


def assert_zero_identity(old, new):
    required={'source','config','request','native_decisions','restored_vector',
              'restored_tree','candidate_tree','candidate_vector','resources','policies'}
    assert set(old)==set(new)==required, 'Incomplete zero-equivalence evidence'
    for key in sorted(required):
        assert old[key]==new[key], ('Zero-weight mismatch',key)


class BaselineAudit:
    def __init__(self):
        self.e=Evidence(); self.audit=Audit(RELEASE,self.e)
        self.e.bind(Path(__file__).resolve())
        # Bind implementations used by imported state and physical-proof gates.
        for name in ['cp1r3_raw_admission_v1.py','recovery_prefix_v1.py',
                     'endpoint_timing_policy_streaming_v2.py','coordinated_repair_tree.py',
                     'run_native_scope_policy_v4.py','retained_prefix_workflow.py']:
            self.e.bind(D/name)

    def document(self,path):
        self.e.bind(path);return read(path)

    def tree(self,path):
        from coordinated_repair_tree import from_trace
        from run_crossing_source_seed_analysis_v1 import study
        self.e.bind(path)
        return {n:from_trace(row['trace'],collections.defaultdict(float)) if row['trace'] else None
                for n,row in study.cr.read_trace(path).items()}

    def vector(self,path):
        self.e.bind(path);self.e.bind(str(path)+'.constraints.echo')
        return vector_digest(load(path))

    def callbacks(self,worker,candidate_expected=True):
        done=self.document(worker/'completion.json');assert done['passed'] and all(done['checks'].values())
        reg=self.document(worker/'registration.json');self.e.verify(reg['source_sha256'])
        assert not live_identity(reg['pid'],reg['start_ticks'])
        exports=self.document(worker/'candidate_exports.json');assert exports['passed']
        assert exports['candidate_gate_present']==candidate_expected
        run=worker/'runs/state';stdout=run/'stdout.log';self.e.bind(stdout)
        text=stdout.read_text()
        vectors={};trees={}
        for key,label in [('candidate','candidate'),('restored','restored_source')]:
            p=Path(exports[key]);assert p.resolve().is_relative_to(run.resolve())
            if key=='candidate' and not candidate_expected:
                assert not (p/'native_state_gate.txt').exists()
                assert 'H3D_ACTUAL_STATE_BEGIN candidate\n' not in text
                continue
            gate=p/'native_state_gate.txt';self.e.bind(gate)
            assert gate.read_text()==label+' FULL fresh_STA actual_installed_trees\n'
            begin='H3D_ACTUAL_STATE_BEGIN '+label+'\n';end='H3D_ACTUAL_STATE_COMPLETE '+label+'\n'
            assert text.count(begin)==text.count(end)==1
            assert 'Completed routing consistency check successfully.' in text.split(begin,1)[1].split(end,1)[0]
            vectors[key]=self.vector(p/'native_sta_frontier.jsonl')
            trees[key]=self.tree(p/'routed.route')
        assert vectors['restored']==vector_digest(self.document(worker/'endpoint_vector.json'))
        assert trees['restored']==self.tree(run/'routed.route')
        return vectors,trees,exports

    def source_control(self):
        plan=self.document(ROOT/'plan.json');self.e.verify(plan['source_sha256'])
        import numpy as np
        original=self.document(REFERENCE/'registration.json')
        cache=Path(original['audit_cache']);proof=self.document(cache/'completion.json')
        assert proof['passed'] and proof['kinds']==['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY']
        self.e.verify(proof['source_sha256'])
        self.e.bind(proof['graph'],proof['graph_sha256'])
        for name,h in proof['payload_sha256'].items():self.e.bind(cache/name,h)
        nodes=np.load(cache/'nodes.npy',mmap_mode='r',allow_pickle=False)
        assert nodes.shape==(proof['node_count'],9) and nodes.dtype==np.dtype('int64')
        assert set(np.unique(nodes[:,4]))=={0,1}
        assert np.array_equal(nodes[:,4],nodes[:,7]), 'Reject CHANZ/spanning nodes'
        assert set(np.unique(nodes[:,1]))<=set(range(6))
        state=Path(plan['source_state']);control=REFERENCE/'source_serialization_control'
        source=self.audit.state(state,D.parents[1]);observed=self.audit.state(control,D.parents[1])
        assert all(source[k]==observed[k] for k in ['route_body_sha256','packed_sha256',
            'placed_sha256','vector_semantic_sha256','resources','constraints_sha256'])
        reg=self.document(control/'registration.json');assert Path(reg['source'])==Path(plan['fixed_role']['source'])
        manifest=self.document(control/'runs/state/manifest.json');env=manifest['environment']
        request=Path(env['VPR_JOINT_NATIVE_REQUEST']);self.e.bind(request)
        assert request.read_text().split()==['0','0','0']
        assert env['VPR_JOINT_NATIVE_SEED_ORDER']==plan['fixed_role']['seed_order']
        assert env['VPR_H3D_MODE']=='off' and env['VPR_JOINT_NATIVE_REUSE_CROSSINGS']==''
        assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']=='0'
        log=control/'runs/state/joint_native.log';self.e.bind(log)
        assert parse_native(log.read_text().splitlines(),[])['success']
        vectors,trees,exports=self.callbacks(control)
        assert vectors['candidate']==vectors['restored']==source['vector_semantic_sha256']
        assert trees['candidate']==trees['restored']
        loaded=Path(exports['candidate'])/'routed.route'
        assert route_body(loaded)==route_body(Path(exports['restored'])/'routed.route')
        assert native_config(Path(source['run']))==native_config(Path(observed['run']))
        return dict(source=source,control=observed,loaded_source_route=str(loaded),
                    empty_control_reused=True,new_native_or_STA_calls=0,
                    original_creation_seconds=self.document(control/'completion.json')['timing']['complete_evaluation_seconds'],
                    creation_seconds_charged_as_new=False)

    def repair(self,tx,name,weight,new):
        role=self.document(tx/'registration.json')['roles'][name]
        reference=self.document(ROOT/'reference_role.json')
        # Operational equality includes source, cuts, order, budgets and native objective.
        assert role==reference
        assert not role['crossing_reuse_enabled'] and not role['domain_failure_release']
        worker=tx/name;wr=self.document(worker/'registration.json')
        assert wr['source']==role['source'] and wr['seed_order']==role['seed_order']
        assert wr['candidate_full_STA'] and not wr['trace_off'] and not wr['domain_failure_release']
        state=self.audit.state(worker,D.parents[1]);source=self.audit.state(Path(role['state']),D.parents[1])
        assert all(state[k]==source[k] for k in ['route_body_sha256','packed_sha256','placed_sha256','vector_semantic_sha256'])
        run=worker/'runs/state';m=self.document(run/'manifest.json');env=m['environment']
        assert native_config(run)==native_config(Path(source['run']))
        assert env['VPR_H3D_MODE']=='off'
        assert env['VPR_JOINT_NATIVE_OBJECTIVE']==role['objective']=='weighted_soft'
        assert env['VPR_JOINT_NATIVE_SEED_ORDER']==role['seed_order']=='delay_rr_id'
        assert float(env['VPR_CURRENT_STA_NATIVE_PRESSURE_START'])==1.
        assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS']=='' and env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']=='0'
        assert not env.get('VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS')
        if new:
            assert wr['vertical_cost_weight']==weight
            assert float(env['VPR_JOINT_NATIVE_VERTICAL_COST_WEIGHT'])==weight
            binding=self.document(ROOT/'build/binding.json')
            assert self.e.bind(m['command'][0])==binding['binary_sha256']
        else:
            assert weight==0 and not env.get('VPR_JOINT_NATIVE_VERTICAL_COST_WEIGHT')
        self.e.bind(role['request']);request=parse_request(Path(role['request']).read_text(),role)
        assert self.e.bind(env['VPR_JOINT_NATIVE_REQUEST'])==sha(role['request'])
        log=run/'joint_native.log';self.e.bind(log);text=log.read_text()
        actual=parse_native(text.splitlines(),request)
        audit=self.document(tx/(name+'_audit/analysis.json'));assert audit['passed']
        self.e.verify(audit.get('source_sha256',{}))
        observed=[(q['net'],q['pin']) for q in audit['queries']]
        assert observed==[(n,p) for n,p,c in request][:len(observed)]
        progress=self.document(tx/'progress.json')[name]
        if not actual['success']:
            assert progress['status']=='transaction_failed_rolled_back'
            assert audit['candidate_route'] is None and audit['status']=='native_transaction_failed_no_candidate'
            assert not progress.get('accepted',False)
            vectors,trees,exports=self.callbacks(worker,candidate_expected=False)
            assert vectors['restored']==source['vector_semantic_sha256']
            return dict(status='search_failed_exact_rollback_verified',quality=None,accepted=False,
                request=actual,source=source,restored_vector=vectors['restored'],
                qualification='Verified failed search and source restoration. No candidate quality or infeasibility claim.')
        assert observed==[(n,p) for n,p,c in request]
        assert all(s['terminal_set_unchanged'] and s['other_branch_edges_unchanged'] for s in audit['scope'])
        assert progress['status']=='legal_evaluated'
        evaluated=self.audit.state(Path(progress['evaluation']),D.parents[1])
        vectors,trees,exports=self.callbacks(worker)
        assert vectors['candidate']==evaluated['vector_semantic_sha256']
        assert self.tree(Path(progress['evaluation'])/'runs/state/routed.route')==trees['candidate']
        assert self.tree(Path(audit['candidate_route']))==trees['candidate']
        assert progress['resources']==evaluated['resources']
        policies=self.document(tx/(name+'_decisions.json'))
        from fixed_anchor_acceptance import decisions
        from multiobjective_acceptance_v2 import decide
        before=self.document(Path(role['state'])/'endpoint_vector.json')
        after=self.document(Path(progress['evaluation'])/'endpoint_vector.json')
        expected=decisions(before,after,source['resources'],evaluated['resources'],role['original_budget'])
        for mode in ['timing_under_resources','resources_under_timing']:
            expected[mode]=decide(mode,before,after,source['resources'],evaluated['resources'],
                cpd_limit_s=role['original_budget']['CPD_s'],resource_limits=role['fixed_resource_limits'],
                native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
        assert policies==expected
        # Full trees are compared in memory; receipts contain only their evidence hashes.
        return dict(source=source,config=native_config(run),request=request,native_decisions=semantic_native(text),
            restored_vector=vectors['restored'],restored_tree=trees['restored'],candidate_tree=trees['candidate'],
            candidate_vector=vectors['candidate'],resources=evaluated['resources'],policies=policies)


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-control','zero','weighted'],required=True)
    p.add_argument('--weight',type=float,choices=[.5,1.,2.])
    p.add_argument('--serial-lock-fd',type=int)
    p.add_argument('--transaction',type=Path);p.add_argument('--role',default='weight_0')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists(),'Preserve all attempts'
    if a.serial_lock_fd is None:
        lock=(D/'critical_scope_runner.lock').open('r');fd=lock.fileno()
    else:
        fd=a.serial_lock_fd
        assert Path('/proc/self/fd',str(fd)).resolve()==(D/'critical_scope_runner.lock').resolve()
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    started=time.monotonic();audit=BaselineAudit()
    try:
        control=audit.source_control();summary=dict(mode=a.mode,source_control=control)
        if a.mode=='zero':
            assert a.transaction is not None
            old=audit.repair(REFERENCE,'union_native',0,False)
            new=audit.repair(a.transaction,a.role,0,True);assert_zero_identity(old,new)
            summary.update(zero_equivalence_passed=True,positive_weights_permitted=True)
        elif a.mode=='weighted':
            assert a.transaction is not None and a.weight is not None
            zero=audit.document(a.transaction/'zero_equivalence.json')
            assert zero['passed'] and zero['zero_equivalence_passed']
            from vertical_cost_zero_progress_transition_v1 import reconcile
            audit.e.bind(D/'vertical_cost_zero_progress_transition_v1.py')
            progress=audit.document(a.transaction/'progress.json')
            terminal=audit.document(a.transaction/'completion.json')
            transition=reconcile(zero,progress,terminal,str((a.transaction/'progress.json').resolve()))
            audit.e.verify(transition['immutable_source_sha256'])
            summary['zero_progress_transition']=transition
            actual=audit.repair(a.transaction,a.role,a.weight,True)
            if actual.get('status')=='search_failed_exact_rollback_verified':
                summary.update(weight=a.weight,outcome=actual)
            else:
                summary.update(weight=a.weight,status='legal_evaluated',resources=actual['resources'],policies=actual['policies'],
                               candidate_vector_semantic_sha256=actual['candidate_vector'])
        audit.e.unchanged()
        write(a.output,dict(passed=True,**summary,source_sha256=audit.e.bound,
            readonly_audit_seconds=time.monotonic()-started,new_native_or_STA_calls=0))
    except BaseException as exc:
        write(a.output,dict(passed=False,mode=a.mode,error=repr(exc),positive_weights_permitted=False,
            source_sha256=audit.e.bound,readonly_audit_seconds=time.monotonic()-started,new_native_or_STA_calls=0))
        raise


if __name__=='__main__':main()
