"""Revalidate interrupted private states without forging the old pool's final seal.

Completed native searches are consumed from their original immutable receipts.
Candidate LOAD/FULL/STA and physical checks are run in the new pool; original
search time is never counted as new work. This adapter supports native-only
checkpoints, with the original root anchor and deterministic ranking unchanged.
"""
import fcntl
from pathlib import Path
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import load, decide as timing_decide
from multiobjective_acceptance_v2 import decide
from actual_route_tree_identity import same_actual_trees

VECTOR_KEYS = ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']

def resources(state):
    x=read(run_dir(state)/'independent_audit.json')['physical_metrics']
    return dict(wirelength=x['planar_wirelength_excluding_sb_half_nodes'],
                SB_pairs=x['sb_pairs_used'],CB_sources=x['cb_crossing_output_sources_used'])

def verify_hashes(mapping):
    for p,h in mapping.items():
        assert sha(p)==h, ('Changed recovery evidence',p)

class Recovery:
    def __init__(self, directory, args, output):
        self.directory=Path(directory).resolve();self.output=Path(output)
        self.registration=read(self.directory/'registration.json')
        self.checkpoint=read(self.directory/'current_state.json')
        self.state=Path(self.checkpoint['state']);self.steps=read(self.directory/'steps.json')
        self.attempts=read(self.directory/'attempts.json');self.consumed=[];self.consumed_bindings={}
        reg=self.registration
        assert reg['domain_mode']==args.domain_mode=='unrestricted'
        assert not reg['domain_failure_release'] and not args.domain_feedback
        assert reg['initial_state']==str(args.initial_state.resolve())
        assert reg['bundle_size']==args.bundle_size and reg['seed_order']==args.seed_order
        assert reg['graph_echo']==args.graph_echo
        assert reg['local_probe']==dict(accepted_steps=args.accepted_steps,ranked_candidates_per_state=args.rank_windows)
        assert self.checkpoint['fixed_anchor']==reg['anchor']
        assert len(self.steps)==self.checkpoint['accepted_steps']
        assert self.steps[-1]['committed_evaluation']==str(self.state)
        handles=[reg]
        for p in [self.directory/'active_child.json',self.directory/'pool/registration.json']:
            if p.exists(): handles.append(read(p))
        handles+=read(self.directory/'pool/epochs.json')
        for item in handles:
            if 'pid' not in item:continue
            actual=process_identity(item['pid'])
            assert not actual or actual['state']=='Z' or actual['start_ticks']!=item['start_ticks'],actual
        self.locks=[]
        for name in ['owner.lock','pool/owner.lock']:
            f=(self.directory/name).open('r');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);self.locks.append(f)
        verify_hashes(reg['source_sha256'])
        oldpool=read(self.directory/'pool/registration.json')
        verify_hashes(oldpool['static_input_sha256'])
        verify_hashes(read(self.directory/'evaluation_context/registration.json')['cache_payload_sha256'])
        assert read(self.state/'completion.json')['passed']
        manifest=read(run_dir(self.state)/'manifest.json')
        for n in ['packed.net','placed.place','routed.route']:
            assert sha(run_dir(self.state)/n)==manifest['outputs'][n]['sha256']
        assert read(run_dir(self.state)/'independent_audit.json')['audit']['passed']
        self.bound_paths=[self.directory/n for n in ['registration.json','current_state.json','steps.json','attempts.json','pool/registration.json']]
        self.bindings={str(p):sha(p) for p in self.bound_paths}
        write(self.output/'recovery_registration.json',dict(passed=True,original=str(self.directory),
            original_pool_final_seal_present=(self.directory/'pool/completion.json').exists(),
            original_pool_seal_fabricated=False,original_anchor=reg['anchor'],accepted_checkpoint_steps=len(self.steps),
            source_sha256=self.bindings,qualification='Historical steps remain private provenance; fresh checkpoint and consumed candidates require the NEW pool final seal. Recovery wall time cannot reconstruct interrupted whole-workflow time.'))

    def completed_revalidation(self,state):
        failed=D/'native_checkpoint_recovery_01'/self.directory.name
        assert state.is_relative_to(failed) and read(state/'completion.json')['passed']
        reg=read(failed/'registration.json')
        verify_hashes(reg['source_sha256'])
        for rel in ['pool/completion.json','evaluation_context/input_seal.json','evaluation_context/completion.json']:
            proof=read(failed/rel);assert proof['passed'];verify_hashes(proof['source_sha256'])
            self.consumed_bindings[str(failed/rel)]=sha(failed/rel)
        manifest=read(run_dir(state)/'manifest.json')
        for n in ['packed.net','placed.place','routed.route']:
            assert sha(run_dir(state)/n)==manifest['outputs'][n]['sha256']
        assert read(run_dir(state)/'independent_audit.json')['audit']['passed']
        for p in [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'manifest.json',run_dir(state)/'routed.route',run_dir(state)/'independent_audit.json',failed/'registration.json']:
            self.consumed_bindings[str(p)]=sha(p)
        return state

    def revalidate_checkpoint(self,evaluator,pool,echo):
        oldpool=read(self.directory/'pool/registration.json')
        oldcmd=list(oldpool['command']);newcmd=list(pool.command)
        oldinputs=dict(oldpool['static_input_sha256']);newinputs=dict(pool.inputs)
        assert oldinputs.pop(oldcmd[0])==newinputs.pop(newcmd[0])
        oldcmd[0]=newcmd[0]='<identical copied binary>'
        assert oldcmd==newcmd and oldinputs==newinputs
        assert oldpool['native_seed_order']==pool.seed_order
        assert oldpool['native_resource_census']==pool.native_census
        target=self.completed_revalidation(D/'native_checkpoint_recovery_01'/self.directory.name/'initial')
        before,after=read(self.state/'endpoint_vector.json'),read(target/'endpoint_vector.json')
        assert all(before[k]==after[k] for k in VECTOR_KEYS),'Checkpoint LOAD changed exact native timing'
        assert sha(run_dir(target)/'routed.route')==sha(run_dir(self.state)/'routed.route')
        write(self.output/'checkpoint_revalidation.json',dict(passed=True,state=str(target),original=str(self.state),
            full_vector_exact=True,ordered_route_bytes_exact=True,root_anchor_unchanged=True,
            original_pool_final_seal_fabricated=False,reused_successfully_sealed_actual_checkpoint_LOAD=True,new_native_LOAD_calls=0,requires_final_input_seal=str(evaluator.directory/'input_seal.json')))
        return target

    def consume(self,round_index,rank,name,current,request,domain,evaluator,tx,anchor):
        old=self.directory/f'round_{round_index:03d}'/f'candidate_{rank:02d}'
        if not old.exists():return None
        receipt=old/(name+'_worker_receipt.json')
        if not receipt.exists():
            # An ambiguous submitted job must be reconciled, never blindly rerun.
            raise RuntimeError('Unsealed submitted search needs explicit reconciliation: '+str(old))
        worker=read(receipt);assert worker['passed'] and worker['candidate_full_STA_passed']
        assert worker['native_transaction_succeeded'] and worker['native_seed_order']==self.registration['seed_order']
        assert worker==read(Path(worker['job'])/'completion.json')
        verify_hashes(worker['artifact_sha256'])
        self.consumed_bindings.update(worker['artifact_sha256'])
        self.consumed_bindings[str(receipt)]=sha(receipt)
        role=read(old/'registration.json')['roles'][name]
        verify_hashes(role['source_sha256'])
        assert worker['route_sha256']==sha(run_dir(current)/'routed.route')
        assert sha(request)==sha(old/'request.txt') and sha(domain)==sha(old/'domain.txt')
        assert not role['crossing_reuse_enabled'] and not role['domain_failure_release']
        options=worker['native_options']
        assert options['operation']=='repair_fused' and options['objective']=='weighted_soft'
        assert options['inputs']=={'native_request.txt':sha(request)} and options['pressure_start']==1.
        oldbefore=read(Path(role['state'])/'endpoint_vector.json');before=read(current/'endpoint_vector.json')
        assert all(oldbefore[k]==before[k] for k in VECTOR_KEYS)
        auditpath=old/(name+'_audit/analysis.json');domainpath=old/(name+'_domain_audit.json')
        audit=read(auditpath);domainaudit=read(domainpath)
        assert audit['passed'] and domainaudit['passed'] and not domainaudit['enabled']
        verify_hashes(audit['source_sha256']);verify_hashes(domainaudit['source_sha256'])
        self.consumed_bindings.update(audit['source_sha256']);self.consumed_bindings.update(domainaudit['source_sha256'])
        native=Path(worker['native_directory']);candidate=native/'candidate/routed.route'
        assert (native/'candidate/native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
        assert (native/'candidate_restored/native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
        for n in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
            assert sha(native/n)==sha(native/'candidate_restored'/n)
        assert same_actual_trees(candidate,audit['candidate_route'])
        started=time.monotonic()
        target=self.completed_revalidation(D/'native_checkpoint_recovery_01'/self.directory.name/f'round_{round_index:03d}'/f'candidate_{rank:02d}'/(name+'_evaluation'))
        after=read(target/'endpoint_vector.json');saved=load(native/'candidate/native_sta_frontier.jsonl')
        saved['endpoint_ids']=[list(identity) for identity in saved['endpoint_ids']]
        assert all(after[k]==saved[k] for k in VECTOR_KEYS),'Recovered candidate LOAD changed exact native timing'
        newres=resources(target)
        decision=decide('resources_under_timing',before,after,resources(current),newres,
            cpd_limit_s=anchor['CPD_s'],resource_limits=anchor['resource_limits'],native_valid=True,
            transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
        result=dict(status='legal_evaluated',accepted=decision['accepted'],evaluation=str(target),CPD_s=after['cpd_s'],
            resources=newres,decision=decision,strict_or_endpoint_control={m:timing_decide(m,before,after,True) for m in ['strict','endpoint_vector']},
            completed_search_consumed=True,new_native_search_calls=0,new_native_LOAD_calls=0,reused_completed_revalidation=True,native_core_seconds=None,
            recovery_candidate_revalidation_seconds=time.monotonic()-started,
            original_worker_receipt=str(receipt),historical_creation_seconds_not_borrowed=True)
        previous=old/(name+'_decisions.json')
        if previous.exists():
            oldresult=read(previous)
            assert all(result[k]==oldresult[k] for k in ['accepted','CPD_s','resources','decision','strict_or_endpoint_control'])
        write(tx/(name+'_decisions.json'),result)
        self.consumed.append(dict(original_receipt=str(receipt),original_sha256=sha(receipt),new_state=str(target),new_native_search_calls=0))
        write(self.output/'completed_search_reuse.json',self.consumed)
        return result

    def finish(self):
        verify_hashes(self.bindings)
        verify_hashes(self.consumed_bindings)
        for p,h in self.registration['source_sha256'].items():assert sha(p)==h
