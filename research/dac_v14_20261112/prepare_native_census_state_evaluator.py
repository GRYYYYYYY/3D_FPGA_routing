#!/usr/bin/env python3
"""Prepare an independent native-count consumer; retain the frozen v7 evaluator."""
from retained_prefix_workflow import D,read,write,sha

source=D/'pool_state_evaluator_v7.py';target=D/'pool_state_evaluator_v8.py';assert not target.exists()
t=source.read_text()
def rep(a,b):
    global t
    assert t.count(a)==1,a[:120]
    t=t.replace(a,b)
rep('from run_native_scope_policy_v4 import run_dir',
    'from run_native_scope_policy_v4 import run_dir\nfrom native_resources_from_receipt import bound_native_resources\nfrom state_resource_assurance import resource_assurance')
rep("r=read(pool.directory/'registration.json');assert r['runtime_libraries_resolved_before_start']",
    "r=read(pool.directory/'registration.json');assert r['runtime_libraries_resolved_before_start']\n        assert r.get('native_resource_census') is True, 'This independent evaluator requires actual frozen native census controls'")
rep('def evaluate(self,route,output,*,physical_reference=None,reuse=True,native_observation=None):',
    'def evaluate(self,route,output,*,native_resource_worker,native_resource_kind,physical_reference=None,reuse=True,native_observation=None):')
rep("        write(rd/'manifest.json',manifest);write(rd/'pair_check.json'",
    "        manifest['resource_assurance_policy']='native_per_candidate_final_independent'\n        manifest['publication_requires_final_independent_validation']=True\n        write(rd/'manifest.json',manifest);write(rd/'pair_check.json'")
needle="        audit_start=time.monotonic();audit_reused=False\n        if all(checks.values()):"
replacement="""        resource_started=time.monotonic()
        assert native_resource_kind in ['input','candidate']
        assert (observed_kind=='installed_candidate') == (native_resource_kind=='candidate')
        assert native_resource_worker['job']==native['job'] and native_resource_worker['static_identity']==self.pool.identity
        native_resource_view=bound_native_resources(native_resource_worker,native_resource_kind)
        raw_root=Path(native_resource_worker['native_directory'])
        bound_route=raw_root/'candidate/routed.route' if native_resource_kind=='candidate' else Path(native_resource_worker['job'])/'routed.route'
        assert sha(bound_route)==before, 'Resource counter belongs to a different actual route'
        if native_resource_kind=='candidate':
            assert native['source_native_directory']==str(raw_root)
            assert native['source_worker_input_route_sha256']==native_resource_worker['route_sha256']
        assurance=dict(passed=all(checks.values()),assurance_kind='native_actual_route_tree_census',
            independent_physical_audit=False,bound_native_view=native_resource_view,
            actual_route_sha256=before,packed_sha256=sha(rd/'packed.net'),placed_sha256=sha(rd/'placed.place'),
            graph_sha256=self.cache.g.receipt['graph_sha256'],
            qualification='Actual native FULL/STA/census state. Independent physical verification is deferred, never fabricated; scope/domain checks are separate. Publication needs this state final_independent_validation.json and the context input seal.')
        write(rd/'native_resource_assurance.json',assurance)
        resource_seconds=time.monotonic()-resource_started
        audit_start=time.monotonic();audit_reused=False;audit_deferred=False
        if all(checks.values()) and physical_reference is None:
            checks['bound_native_resource_count']=True
            audit_deferred=True
        elif all(checks.values()):"""
rep(needle,replacement)
rep("        audit_elapsed=time.monotonic()-audit_start",
    "        audit_elapsed=time.monotonic()-audit_start\n        if physical_reference is not None and checks.get('physical_audit'):\n            independent=read(rd/'independent_audit.json')['physical_metrics']\n            assert all(independent[k]==v for k,v in native_resource_view['physical_metrics'].items()), 'Reference physical audit disagrees with native counts'")
rep("        write(b/'completion.json',result);self.states.append(str(b));",
    "        result.update(resource_assurance_policy='native_per_candidate_final_independent',independent_physical_audit_deferred=audit_deferred,independent_physical_audit_passed=bool(checks.get('physical_audit')),native_resource_assurance_sha256=sha(rd/'native_resource_assurance.json'),publication_requires_final_independent_validation=True)\n        result['timing']['native_resource_binding_seconds']=resource_seconds\n        result['qualification']='Private native FULL/freshSTA/resource-count state, not an independent physical audit. Every publication requires this state final independent validation and the context final input seal; deferred rejected states cannot be published merely because another final state passed. No borrowed native time or cold full-algorithm claim.'\n        write(b/'completion.json',result);self.states.append(str(b));")
at=t.index('    def close(self):')
t=t[:at]+'''    def independently_validate(self,state):
        """Verify the actual selected route once; never upgrade another state."""
        state=Path(state).resolve();assert str(state) in self.states
        complete=read(state/'completion.json');assert complete['passed']
        self._check_inputs();started=time.monotonic();rd=run_dir(state)
        route_sha=sha(rd/'routed.route');complete_sha=sha(state/'completion.json')
        view=resource_assurance(state);manifest=read(rd/'manifest.json')
        previous_base=study.BASE;previous_reader=study.cr.read_graph_evidence;previous_records=study.cr.graph_records
        try:
            if not (rd/'independent_audit.json').exists():
                study.BASE=state;study.cr.read_graph_evidence=self.cache.evidence
                result=study.audit_batch({'fixture':{'original_graph':str(self.graph)}},[manifest],state/'final_independent_physical_batch.json')
                assert result['passed'] and result['legal_count']==1
            audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
            assert all(audit['physical_metrics'][k]==v for k,v in view['physical_metrics'].items()), 'Final native census differs from independent physical audit'
            assert sha(rd/'routed.route')==route_sha and sha(state/'completion.json')==complete_sha
            self._check_inputs()
            result=dict(passed=True,state=str(state),route_sha256=route_sha,
                independent_audit_sha256=sha(rd/'independent_audit.json'),
                native_counter_fields_match_independent=True,
                context_input_seal=str(self.directory/'input_seal.json'),
                complete_final_independent_validation_seconds=time.monotonic()-started,
                qualification='Independent physical verification of this exact state only; does not retrospectively certify every private candidate or form cold algorithm time.')
        except Exception as error:
            result=dict(passed=False,state=str(state),error_type=type(error).__name__,error=str(error),
                complete_final_independent_validation_seconds=time.monotonic()-started)
        finally:
            study.BASE=previous_base;study.cr.read_graph_evidence=previous_reader;study.cr.graph_records=previous_records
        write(state/'final_independent_validation.json',result)
        return result

    def close(self,*,final_state):
        """Seal static inputs AND the explicitly chosen final independent route."""
        if self.closed:return
        validation=self.independently_validate(final_state) if final_state is not None else dict(passed=False,reason='No selected final state')
        self.pool.close();pc=read(self.pool.directory/'completion.json')
        checks={p:sha(p)==h and file_stat(p)==self.cache_stats[p] for p,h in self.cache_hashes.items()}
        passed=pc['passed'] and all(checks.values()) and validation['passed']
        final=None if final_state is None else str(Path(final_state).resolve())
        write(self.directory/'input_seal.json',dict(passed=passed,pool_completion=str(self.pool.directory/'completion.json'),
            pool_completion_sha256=sha(self.pool.directory/'completion.json'),cache_checks=checks,
            final_independently_validated_state=final,final_independent_validation=validation,
            qualification='Static epoch and selected final route seal. Other private native-count states require their own independent verification before publication.'))
        self.closed=True
        write(self.directory/'completion.json',dict(passed=passed,states=self.states,final_state=final,
            final_independent_validation=validation,resource_assurance_policy='native_per_candidate_final_independent',
            complete_component_workflow_seconds=time.monotonic()-self.started,
            complete_single_configuration_algorithm_seconds=None,
            source_sha256={str(p):sha(p) for p in [self.directory/'input_seal.json',self.directory/'states.json']},
            qualification='Private native-census state workflow plus actual final independent physical verification. All candidate failures/materialization/check/STA/restoration costs stay in the actor workflow; no cold-time or every-candidate independent-audit claim.'))
        assert passed,'Native context or selected final independent route failed; do not publish'
'''
compile(t,str(target),'exec');target.write_text(t)
write(D/'native_census_state_evaluator_preparation_01.json',dict(passed=True,
    source=str(source),source_sha256=sha(source),target=str(target),target_sha256=sha(target),
    assurance_interface='state_resource_assurance.py',native_calls=0,route_calls=0,
    actual_receipt_replay_pending=True,independent_final_audit_required=True,
    qualification='Independent implementation/syntax preparation. Not a passed actual worker integration, algorithm quality point or measured runtime gain. Existing evaluator and every registered actor unchanged.'))
print(dict(prepared=str(target),actual_validation_pending=True),flush=True)
