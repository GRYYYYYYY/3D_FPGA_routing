"""Consume audited stages of the same interrupted transaction, without replay.

This development adapter writes only a new recovery namespace. It requires a
subsequently sealed serial audit; metadata inventory is never sufficient.
"""
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from recovery_prefix_v1 import Evidence,compatible_roles,live_identity

def audit_record_gate(plan,summary,case,transaction):
    assert case['passed'] and case in summary['rows'],'Selected case not audited successfully'
    assert (case['pair'],case['arm'])==(plan['pair'],plan['arm'])
    assert Path(transaction).resolve()==Path(plan['original_transaction']).resolve()
    assert not case['full_method_complete'] and not case['adoption_implemented']
    stage=case['stages']['native_source_control']
    assert stage['verified_existing_execution'] and stage['exact_observation']['passed']
    assert all(stage['exact_observation']['checks'].values())
    assert stage['receipt_kind'] in ['sealed_worker','raw_success_unsealed_manifest']
    assert stage['original_manifest_unchanged'] and stage['new_native_calls']==0
    assert not case['stages']['candidate_STA']['completed']
    assert not case['stages']['candidate_STA']['persisted_payload_present']
    return stage

def partial_STA_guard(path):
    path=Path(path)
    assert not path.exists() or (path.is_dir() and not any(path.iterdir())),\
        'Existing candidate STA payload requires reconciliation; never replay it'

class StageReuse:
    def __init__(self,plan_path,transaction):
        self.plan_path=Path(plan_path).resolve();self.plan=read(self.plan_path)
        self.tx=Path(transaction).resolve();actor=Path(self.plan['recovery_actor']).resolve()
        relative=self.tx.relative_to(actor)
        self.old=(Path(self.plan['original_actor'])/relative).resolve()
        assert not self.tx.is_relative_to(Path(self.plan['original_actor']).resolve())
        self.proof=None;self.evidence=Evidence();self.records=[]

    def _proof(self):
        if self.proof is not None:return self.proof
        p=self.plan
        summary_path=Path(p['stage_audit_summary']);case_path=Path(p['stage_audit'])
        # These actual terminal audit hashes must be sealed by admission after
        # audit execution. No placeholder or self-asserted passed flag suffices.
        self.evidence.bind(self.plan_path)
        self.evidence.bind(summary_path,p['stage_audit_summary_sha256'])
        self.evidence.bind(case_path,p['stage_audit_sha256'])
        summary=read(summary_path);case=read(case_path)
        audit_record_gate(p,summary,case,self.old)
        self.audited=summary['source_sha256']
        self.bind(self.old/'registration.json')
        self.proof=case
        return case

    def bind(self,path,expected=None):
        path=str(Path(path).resolve())
        assert path in self.audited,('Not covered by serial audit',path)
        if expected is not None:assert self.audited[path]==expected,('Recorded input mismatch',path)
        return self.evidence.bind(path,self.audited[path])

    def role(self,name):
        case=self._proof();old=read(self.old/'registration.json')['roles'][name]
        new=read(self.tx/'registration.json')['roles'][name]
        assert Path(old['state']).resolve()==Path(case['source_state']).resolve()
        assert old['original_budget']==case['fixed_original_budget']
        compatible_roles(old,new)
        for path,digest in old['source_sha256'].items():self.bind(path,digest)
        # New registration and request are freshly sealed by the unchanged
        # controller; matching old bytes never substitutes for that seal.
        assert all(sha(path)==digest for path,digest in new['source_sha256'].items())
        worker=self.old/name;registration=read(worker/'registration.json')
        self.bind(worker/'registration.json')
        assert not live_identity(registration['pid'],registration['start_ticks'])
        for path in self.old.glob('*supervision*.json'):
            self.bind(path)
            for identity in read(path).values():
                if isinstance(identity,dict) and 'pid' in identity and 'start_ticks' in identity:
                    assert not live_identity(identity['pid'],identity['start_ticks'])
        return old,new

    def receipt(self,tag,stage,details):
        self.evidence.unchanged()
        value=dict(passed=True,stage=stage,original_transaction=str(self.old),
            new_transaction=str(self.tx),new_native_calls=0,creation_cost_borrowed=False,
            source_sha256=self.evidence.bound,**details)
        write(self.tx/(tag+'_stage_reuse.json'),value)
        self.records.append(dict(tag=tag,stage=stage,new_native_calls=0))
        write(self.tx/'stage_reuse_index.json',dict(records=self.records,new_native_calls_from_reuse=0))
        return True

    def consume(self,script,args,tag):
        if not (self.old/'registration.json').exists():return False
        stages=[('_FULL_STA','candidate_STA'),('_domain_audit','domain_audit'),('_audit','candidate_physical_audit'),('_native','native_source_control')]
        match=next(((suffix,stage) for suffix,stage in stages if tag.endswith(suffix)),None)
        if match is None:return False
        suffix,stage=match;name=tag[:-len(suffix)]
        oldroles=read(self.old/'registration.json')['roles']
        if name not in oldroles:
            assert name not in read(self.tx/'registration.json')['roles'],'Role unexpectedly added to an existing old transaction'
            return False
        worker=self.old/name
        if not worker.exists():
            partial_STA_guard(self.old/(name+'_evaluation'))
            assert not (self.old/(name+'_audit')).exists()
            assert not (self.old/(name+'_domain_audit.json')).exists()
            return False
        if stage=='candidate_physical_audit' and not (self.old/(name+'_audit')).exists():return False
        if stage=='domain_audit' and not (self.old/(name+'_domain_audit.json')).exists():return False
        # This gate also protects an empty candidate STA placeholder from being
        # reused if the original process is still alive or evidence changed.
        assert name==self.plan['original_role'],'Existing role outside the selected stage audit'
        old,new=self.role(name);case=self._proof()
        if stage=='candidate_STA':
            partial_STA_guard(self.old/(name+'_evaluation'))
            return False
        if stage=='native_source_control':
            assert script in ['run_serial_seed_resource_state_analysis_stream_v1.py','run_independent_resource_state_analysis_stream_v1.py']
            run=worker/'runs/state';m=read(run/'manifest.json');self.bind(run/'manifest.json')
            for path,item in m['shared_inputs'].items():self.bind(path,item['sha256'])
            for path,digest in m['private_input_sha256'].items():self.bind(path,digest)
            for path,digest in read(worker/'registration.json')['source_sha256'].items():self.bind(path,digest)
            for name_in_run in ['native_sta_frontier.jsonl','joint_native.log','stdout.log','time.txt']:
                self.bind(run/name_in_run)
            proof=case['stages'][stage]
            if proof['receipt_kind']=='sealed_worker':
                self.bind(worker/'completion.json');self.bind(worker/'input_seal.json')
                assert m['status']=='completed' and m['returncode']==0
            else:
                assert m['status']=='running' and not (worker/'completion.json').exists()
            output=Path(args[args.index('--batch')+1]);assert output.resolve()==self.tx/name
            assert not output.exists();output.mkdir()
            vector=Path(old['state'])/'endpoint_vector.json';self.bind(vector)
            # The serial audit compared the actual raw STA against this vector
            # exactly. Copy its canonical JSON; do not rerun or reparse STA.
            (output/'endpoint_vector.json').write_bytes(vector.read_bytes())
            write(output/'completion.json',dict(passed=True,status='audited_same_actor_source_observation_reused',
                run=str(run),observation_only=True,process_status='verified_existing_command_complete',
                original_worker=str(worker),original_manifest_status=m['status'],original_manifest_rewritten=False,
                original_receipt_kind=proof['receipt_kind'],exact_observation=proof['exact_observation'],
                native_analysis_calls_new=0,native_queries_new=0,historical_queries=proof['query_count'],
                full_precision_cpd_s=read(vector)['cpd_s'],
                qualification='New readonly adoption receipt for an audited old command. Original manifest/completion and historical cost remain unchanged; candidate audit/FULL/STA and acceptance are separate. No fresh native execution or complete-method result.'))
            return self.receipt(tag,stage,dict(original_worker=str(worker),original_manifest_rewritten=False))
        if stage=='candidate_physical_audit':
            assert script in ['audit_native_feedback_objective_cached.py','audit_native_objective_cached.py']
            olddir=self.old/(name+'_audit');analysis=read(olddir/'analysis.json')
            assert case['stages'][stage]['existing_passed_receipt'] and analysis['passed']
            self.bind(olddir/'analysis.json')
            # The recorded audit binds its own old worker, source, graph and
            # algorithm. Recheck that closure even where the stage audit did
            # not need to re-run its computation.
            for path,digest in analysis.get('source_sha256',{}).items():
                self.evidence.bind(path,digest)
            if analysis.get('candidate_route'):
                self.bind(analysis['candidate_route'])
                assert sha(analysis['candidate_route'])==analysis['candidate_sha256']
            output=Path(args[args.index('--output')+1]);assert output.resolve()==self.tx/(name+'_audit')
            assert not output.exists();output.symlink_to(olddir,target_is_directory=True)
            return self.receipt(tag,stage,dict(original_audit=str(olddir/'analysis.json')))
        assert stage=='domain_audit'
        expected='audit_failure_release_domain.py' if new.get('domain_failure_release') else 'audit_retained_crossing_domain.py'
        assert script==expected
        original=self.old/(name+'_domain_audit.json');result=read(original)
        assert case['stages'][stage]['existing_passed_receipt'] and result['passed']
        self.bind(original)
        for path,digest in result.get('source_sha256',{}).items():self.evidence.bind(path,digest)
        output=self.tx/(name+'_domain_audit.json');assert not output.exists();output.symlink_to(original)
        return self.receipt(tag,stage,dict(original_audit=str(original)))

    def finish(self):
        self.evidence.unchanged()
        if self.records:
            write(self.tx/'stage_reuse_seal.json',dict(passed=True,records=self.records,
                original_receipts_changed=False,source_sha256=self.evidence.bound,
                cost_scope='new_recovery_suffix_only',creation_cost_borrowed=False))
