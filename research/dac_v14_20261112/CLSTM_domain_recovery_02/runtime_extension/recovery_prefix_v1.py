"""Explicit development-prefix recovery; no reset root or borrowed creation cost.

The original actor and all its outputs remain read-only. A completed native
worker may be adopted only after its actual source/options/requests, seals and
restored full timing identity pass again. Candidate audit/FULL/STA stay required.
"""
import copy,hashlib,json,time
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from run_native_scope_policy_v4 import run_dir,native_config
from endpoint_timing_policy_streaming_v2 import load
from observation_timing_identity_v2 import check as exact_observation
from state_resource_assurance import require_publication_proof

def live_identity(pid,ticks):
    try:s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
    except (FileNotFoundError,ProcessLookupError):return False
    return s[0]!='Z' and s[19]==str(ticks)

def compatible_roles(old,new):
    """Compare operational fields and exact request/domain bytes, not filenames."""
    paths={'request','crossing_domain','source_sha256'}
    assert set(old)==set(new),('role fields changed',set(old)^set(new))
    assert {k:v for k,v in old.items() if k not in paths}=={k:v for k,v in new.items() if k not in paths},'Operational role changed'
    for name in ['request','crossing_domain']:
        if name in old:assert Path(old[name]).read_bytes()==Path(new[name]).read_bytes(),name

def original_envelope(reg,checkpoint,initial,anchor,limits,args):
    assert Path(initial).resolve()==Path(reg['initial_state']).resolve()
    assert checkpoint['anchor']==reg['anchor']==anchor
    assert checkpoint['resource_limits']==reg['resource_limits']==limits
    assert reg['owner_domain_mode']=='unrestricted_in_both_arms'
    for name in ['bundle_size','domain_mode','seed_order','domain_feedback','owner_rank_windows']:
        assert getattr(args,name)==reg[name],name
    assert (not args.disable_owner_escalation)==reg['owner_escalation']

def completed_observation_gate(completion,manifest,seal):
    assert {'completed','native_FULL','inputs_unchanged','route_loaded','physical_audit','native_control_complete','CPD_matches_original','inputs_sealed'}<=set(completion['checks'])
    assert manifest['status']=='completed' and manifest['returncode']==0 and manifest['metrics']['native_full_check_passed']
    assert completion['observation_only'] and completion['process_status']=='completed'
    assert all(value for key,value in completion['checks'].items() if key!='CPD_matches_original')
    assert seal['passed']

class Evidence:
    def __init__(self):self.bound={};self.stats={}
    @staticmethod
    def stat(p):
        s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
    def bind(self,p,expected=None):
        p=str(Path(p).resolve())
        if p in self.bound:
            assert self.stat(p)==self.stats[p],('Prefix changed',p)
            if expected is not None:assert self.bound[p]==expected,p
        else:
            before=self.stat(p);digest=sha(p);assert before==self.stat(p),p
            if expected is not None:assert digest==expected,p
            self.bound[p]=digest;self.stats[p]=before
        return self.bound[p]
    def verify(self,mapping):
        for p,h in mapping.items():self.bind(p,h)
    def unchanged(self):
        assert all(self.stat(p)==s for p,s in self.stats.items()),'Consumed prefix changed'

class Prefix:
    def __init__(self,plan_path,output):
        self.plan_path=Path(plan_path).resolve();self.plan=read(self.plan_path)
        self.old=Path(self.plan['original_actor']).resolve();self.output=Path(output).resolve()
        assert not self.output.is_relative_to(self.old) and not self.old.is_relative_to(self.output)
        self.evidence=Evidence();self.evidence.bind(self.plan_path);self.evidence.verify(self.plan['prefix_sha256'])
        self.reg=read(self.old/'registration.json');self.steps=read(self.old/'steps.json');self.attempts=read(self.old/'attempts.json')
        self.current=read(self.old/'current_state.json');self.initial=Path(self.reg['initial_state']).resolve()
        assert not live_identity(self.reg['pid'],self.reg['start_ticks']),'Original actor still live'
        self.evidence.verify(self.reg['source_sha256'])
        audit=read(self.plan['existing_trace_audit']);assert audit['passed'] and audit['existing_reload_exact_identity']['passed']
        self.evidence.verify(audit['source_sha256'])
        assert self.current['anchor']==self.reg['anchor'] and self.current['resource_limits']==self.reg['resource_limits']
        assert self.current['accepted_steps']==len(self.steps)
        expected=self.initial;self.archive={str(self.initial)};self.require_state(self.initial)
        for i,row in enumerate(self.steps):
            assert row['round']==i and Path(row['current_state']).resolve()==expected
            tx=Path(row['transaction']);tr=read(tx/'registration.json');role=row['accepted_role']
            assert read(tx/'completion.json')['passed']
            self.evidence.bind(tx/'completion.json');self.evidence.bind(tx/'registration.json')
            self.evidence.verify(tr['source_sha256'])
            assert tr['roles'][role]['original_budget']==self.reg['anchor']
            assert tr['roles'][role]['fixed_resource_limits']==self.reg['resource_limits']
            decisions=read(tx/(role+'_decisions.json'));assert decisions['resources_under_timing']['accepted']
            self.evidence.bind(tx/(role+'_decisions.json'))
            expected=Path(row['committed_evaluation']).resolve();self.require_state(expected)
        assert str(expected)==self.current['state']
        # Keep legal rejected candidates as well as accepted states for terminal choice.
        for row in self.attempts:
            tx=Path(row['transaction']);progress=tx/'progress.json'
            if not progress.exists():continue
            self.evidence.bind(progress)
            for result in read(progress).values():
                if result.get('status')=='legal_evaluated':self.require_state(Path(result['evaluation']))
        self.reused_selection=False
    def require_state(self,state):
        state=Path(state).resolve();done=read(state/'completion.json');assert done['passed']
        require_publication_proof(state)
        self.evidence.bind(state/'completion.json');self.evidence.bind(state/'endpoint_vector.json')
        rd=run_dir(state);m=read(rd/'manifest.json');assert m['status']=='completed' and m['metrics']['native_full_check_passed']
        assert read(rd/'independent_audit.json')['audit']['passed']
        self.evidence.bind(rd/'manifest.json');self.evidence.bind(rd/'independent_audit.json')
        for name in ['packed.net','placed.place','routed.route']:self.evidence.bind(rd/name,m['outputs'][name]['sha256'])
        self.archive.add(str(state))
    def initialize_controller(self,b,initial,anchor,limits,args):
        original_envelope(self.reg,self.current,initial,anchor,limits,args)
        reg=read(b/'registration.json');reg.update(recovery_prefix=str(self.old),initial_route_imported=True,
            cost_scope='new_recovery_suffix_only',source_sha256={**reg['source_sha256'],str(self.plan_path):sha(self.plan_path)},
            qualification='Explicit development recovery; original root/budgets, accepted prefix and rejected legal archive retained. No fresh full-cost or confirmation claim.')
        write(b/'registration.json',reg)
        write(b/'recovered_prefix.json',dict(passed=True,original_actor=str(self.old),accepted_steps=len(self.steps),
            original_attempts=len(self.attempts),original_costs=read(self.old/'process_costs.json'),
            original_legal_archive=sorted(self.archive),anchor=anchor,resource_limits=limits,
            historical_cost_borrowed=False,new_native_calls=0,source_sha256=self.evidence.bound))
        return Path(self.current['state']),copy.deepcopy(self.steps),copy.deepcopy(self.attempts)
    def selection(self,current,cache,out,fresh_select):
        old=self.old/out.parent.name/'selection';self.reused_selection=False
        if old.exists():
            r=read(old/'completion.json');assert r['passed'] and Path(r['source_state']).resolve()==Path(current).resolve()
            self.evidence.bind(old/'completion.json');self.evidence.verify(r['source_sha256'])
            out.symlink_to(old,target_is_directory=True);self.reused_selection=True
            return read(old/'candidates.json')
        return fresh_select(current,cache,out)
    def finish(self,b):
        self.evidence.unchanged();done=read(b/'completion.json')
        done.update(recovered_from_actor=str(self.old),prefix_accepted_steps=len(self.steps),
            cost_scope='new_recovery_suffix_only',fresh_complete_algorithm_seconds=None,
            qualification='Recovered development trajectory with original fixed root and complete legal archive. Prefix creation costs/failures remain original; current duration covers recovery suffix only. Not fresh full-flow cost, independent input or frozen confirmation.')
        write(b/'completion.json',done)
        write(b/'prefix_consumption_seal.json',dict(passed=True,source_sha256=self.evidence.bound,original_receipts_changed=False,new_native_calls=0))

def consume_completed_worker(plan_path,tx,tag,args):
    """Return False only for genuinely unexecuted work; mismatches always abort."""
    if not tag.endswith('_native'):return False
    plan=read(plan_path);original=Path(plan['original_actor'])/tx.parent.name/tx.name
    role_name=tag[:-len('_native')];old_worker=original/role_name
    if not old_worker.exists():return False
    assert (old_worker/'completion.json').exists(),'Existing incomplete worker requires reconciliation; never rerun'
    old_role=read(original/'registration.json')['roles'][role_name];new_role=read(tx/'registration.json')['roles'][role_name]
    compatible_roles(old_role,new_role)
    v=Evidence();v.verify(plan['prefix_sha256']);v.verify(old_role['source_sha256']);v.verify(new_role['source_sha256'])
    completion=read(old_worker/'completion.json');run=Path(completion['run']);m=read(run/'manifest.json')
    completed_observation_gate(completion,m,read(old_worker/'input_seal.json'))
    registration=read(old_worker/'registration.json');v.verify(registration['source_sha256'])
    assert not live_identity(registration['pid'],registration['start_ticks'])
    for identity in m.get('process_tree_observation',{}).get('processes',[]):
        assert not live_identity(identity['pid'],identity['start_ticks'])
    source=Path(new_role['source']);sm=read(source/'manifest.json')
    assert native_config(run)==native_config(source),'Source-derived command changed'
    for name in ['routed.route','packed.net','placed.place']:assert v.bind(run/name)==v.bind(source/name)
    # Request, seed, objective and restriction flags are actual native environment bindings.
    env=m['environment'];assert sha(env['VPR_JOINT_NATIVE_REQUEST'])==sha(new_role['request'])
    assert env['VPR_JOINT_NATIVE_OBJECTIVE']==new_role['objective']
    assert env['VPR_JOINT_NATIVE_SEED_ORDER']==new_role['seed_order']
    assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']==('1' if new_role['domain_failure_release'] else '0')
    assert float(env['VPR_CURRENT_STA_NATIVE_PRESSURE_START'])==1.
    if new_role['crossing_reuse_enabled']:assert sha(env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])==sha(new_role['crossing_domain'])
    else:assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS']==''
    runtime=read(read(tx/'registration.json')['runtime_config']);expected_binary=runtime['phase_binaries']['resource']['sha256']
    assert v.bind(m['command'][0])==expected_binary
    assert not (original/(role_name+'_audit')).exists(),'Partial downstream audit requires separate stage recovery, not rerun'
    assert not (original/(role_name+'_evaluation')).exists(),'Existing candidate STA must not be rerun'
    v.bind(source.parent.parent/'endpoint_vector.json')
    source_vector=read(source.parent.parent/'endpoint_vector.json');trace=run/'native_sta_frontier.jsonl'
    v.bind(trace);observed=load(trace)
    identity=exact_observation(m['metrics']['critical_path_ns'],sm['metrics']['critical_path_ns'],source_vector,observed)
    assert identity['passed'],identity
    lines=(run/'joint_native.log').read_text().splitlines();assert lines[-1].startswith('COMPLETE ') and lines[-1].endswith('occupancy_restored')
    out=Path(args[args.index('--batch')+1]);assert out==tx/role_name and not out.exists();out.mkdir()
    write(out/'endpoint_vector.json',observed);write(out/'observation_timing_identity.json',identity)
    checks=dict(completion['checks']);checks['CPD_matches_original']=True;checks['observation_full_precision_and_endpoints_exact']=True
    write(out/'completion.json',dict(status='recovered_completed_native_analysis_readonly',passed=True,accepted=None,
        run=str(run),observation_only=True,checks=checks,process_status='completed',native_analysis_calls_new=0,
        native_queries_new=0,historical_queries=sum(x.startswith('QUERY ') for x in lines),
        full_precision_cpd_s=observed['cpd_s'],original_worker=str(old_worker),original_completion_sha256=sha(old_worker/'completion.json'),
        qualification='Actual completed source-control/native-request execution reused; corrected display check plus exact full-vector identity. Candidate audit/FULL/STA and acceptance remain pending. No historical duration is new cost.'))
    for path in [old_worker/'completion.json',old_worker/'input_seal.json',run/'manifest.json',run/'joint_native.log',source.parent.parent/'endpoint_vector.json']:v.bind(path)
    v.unchanged();write(out/'recovery_input_seal.json',dict(passed=True,source_sha256=v.bound,original_receipts_changed=False,new_native_calls=0))
    write(tx/(tag+'_recovery.json'),dict(passed=True,original_worker=str(old_worker),source_sha256=v.bound,new_native_calls=0,complete_readonly_seconds=None))
    return True
