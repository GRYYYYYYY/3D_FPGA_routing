"""Small adversarial fixtures; no native work or production artifact mutation."""
import ast, copy, tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
import complete_resource_prefix_equivalence_v1 as original
import complete_resource_prefix_quality_equivalence_v2 as qualified
import compare_BNN_terminal_wire_qualified_v2 as report


def rejects(call):
    try: call()
    except (AssertionError, FileNotFoundError, KeyError): return True
    raise AssertionError('Invalid evidence accepted')


def main():
    checks = {}
    old_ast = ast.parse(Path(original.__file__).read_text())
    new_ast = ast.parse(Path(qualified.__file__).read_text())
    def helpers(tree):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(tree)
                if isinstance(n,ast.FunctionDef) and n.name != 'compare'}
    assert helpers(old_ast) == helpers(new_ast)
    checks['original_identity_transaction_and_protocol_helpers_AST_exact'] = True
    with tempfile.TemporaryDirectory(prefix='terminal-wire-comparison-') as temp:
        t = Path(temp); a, b = t/'actual', t/'baseline'
        def state(p, margin=1.):
            p.mkdir(parents=True)
            write(p/'completion.json',dict(passed=True,run=str(p)))
            write(p/'manifest.json',{})
            write(p/'endpoint_vector.json',dict(cpd_s=1.,setup={'e':margin},hold={'e':1.},endpoint_ids=[[0,0]],constraints_sha256='fixed'))
            (p/'routed.route').write_text('header\nNet 0 (test)\nNode 1 SINK\n')
            return str(p)
        for i, case in enumerate([a,b]):
            initial = state(case/'initial'); resource = state(case/'resource'); final = state(case/'final',2. if case==a else 1.)
            flow=case/'flow'; flow.mkdir(); actor=flow/'resource_flow/repair'; actor.mkdir(parents=True)
            tx=actor/'transaction'; tx.mkdir(); request=tx/'request';request.write_text('same physical request\n')
            state(tx/'reuse_off')
            (tx/'reuse_off/joint_native.log').write_text(f'QUERY 1 2 3 4 5 6 {i+2}.0 8 9\nCOMPLETE 1 {i+2}.0 3\n')
            role=dict(state=initial,request=str(request),objective='weighted_soft',queries=[[1,1]],removed_pins={'1':[1]},fixed_target_paths=None,seed_order='delay_rr_id',crossing_reuse_enabled=False,domain_failure_release=False)
            write(tx/'registration.json',dict(roles={'reuse_off':role}))
            write(tx/'progress.json',dict(reuse_off=dict(status='legal_evaluated',evaluation=resource,resources={'wirelength':100},policies={'resources_under_timing':{'accepted':True}},cpd_s=1.)))
            write(actor/'attempts.json',[dict(round=0,candidate_rank=0,removed_pins={'1':[1]},accepted_role='reuse_off',native_transaction_complete=True,current_state=initial,transaction=str(tx))])
            write(actor/'process_costs.json',[dict(tag='repair',seconds=i+2)])
            proof=dict(passed=True,complete_configuration_verified=True,initial_state=initial,resource_final_state=resource,final_state=final)
            write(flow/'completion.json',proof)
            if case==a:
                proof.update(resource_policy_final_state=resource,resource_final_state=final)
                write(case/'completion.json',proof)
            else:
                proof.pop('complete_configuration_verified')
                proof.update(complete_configuration_quality_verified=True,complete_observer_measurement_available=False,
                    source_sha256={str(flow/'completion.json'):sha(flow/'completion.json')})
                quality=t/'baseline_quality.json';write(quality,proof)
        exact=lambda:qualified.compare(a,b,quality)['resource_prefix_actual_states_requests_and_native_work_exact']
        assert exact()
        checks['equal_prefix_with_different_terminal_and_elapsed_fields'] = True
        vector=b/'resource/endpoint_vector.json';saved=vector.read_bytes();v=read(vector);v['setup']['e']=.5;write(vector,v)
        assert not exact();vector.write_bytes(saved);checks['changed_endpoint_detected'] = True
        request=b/'flow/resource_flow/repair/transaction/request';saved=request.read_bytes();request.write_text('different request\n')
        assert not exact();request.write_bytes(saved);checks['changed_request_detected'] = True
        log=b/'flow/resource_flow/repair/transaction/reuse_off/joint_native.log';saved=log.read_bytes();log.write_text(log.read_text().replace('8 9','8 10'))
        assert not exact();log.write_bytes(saved);checks['changed_native_work_detected'] = True
        proof=read(quality);bad=copy.deepcopy(proof);bad['initial_state']=str(t/'foreign');write(quality,bad)
        checks['foreign_quality_flow_rejected']=rejects(exact);write(quality,proof)
        (b/'measurement').mkdir();write(b/'measurement/completion.json',{'passed':True})
        checks['fabricated_observer_receipt_rejected']=rejects(exact);(b/'measurement/completion.json').unlink()
        completion=a/'completion.json';saved=completion.read_bytes();completion.unlink()
        checks['nonterminal_actual_rejected']=rejects(exact);completion.write_bytes(saved)
        baseline_cfg=dict(input_sha256={'physical':'digest'},route_command=['--seed','11'],domain_mode='unrestricted')
        actual_cfg=dict(baseline_cfg,terminal_resource_policy='endpoint_wire_before_timing')
        report.check_config_pair(actual_cfg,baseline_cfg)
        bad=copy.deepcopy(actual_cfg);bad['route_command']=['--seed','21']
        checks['wrong_seed_config_rejected']=rejects(lambda:report.check_config_pair(bad,baseline_cfg))
        bad=copy.deepcopy(actual_cfg);bad['input_sha256']['physical']='other'
        checks['different_input_binding_rejected']=rejects(lambda:report.check_config_pair(bad,baseline_cfg))
        for case,seconds in [(a,100),(b,90)]:
            write(case/'config.json',actual_cfg if case==a else baseline_cfg)
            (case/'measurement').mkdir(exist_ok=True)
            command=['python','flow.py','--config',str(case/'config.json'),'--output',str(case/'flow')]
            write(case/'measurement/registration.json',dict(command=command))
            (case/'measurement/gnu_time.txt').write_text(f'Command being timed: "{" ".join(command)}"\nElapsed (wall clock) time (h:mm:ss or m:ss): 1:{seconds-60:02d}\nMaximum resident set size (kbytes): 100\nExit status: 0\n')
        old_time=report.observed_gnu(b)
        old_time.update(original_observer_receipt_available=False,complete_observer_wall_seconds=None,sampled_tree_PSS_peak_kib=None,undisturbed_timing=False)
        write(a/'measurement/completion.json',dict(complete_command_wall_seconds=777.))
        costs=report.cost_comparison(a,b,old_time,True)
        assert costs['descriptive_GNU_seconds_difference']==10.
        assert costs['baseline_observer_wall_seconds'] is None and costs['baseline_sampled_tree_PSS_peak_kib'] is None
        checks['GNU_scope_not_mixed_with_777_second_observer_and_missing_PSS'] = True
        assert report.cost_comparison(a,b,old_time,False)['descriptive_GNU_seconds_difference'] is None
        checks['divergent_prefix_disables_attributed_cost_difference'] = True
        bad=dict(old_time,original_observer_receipt_available=True)
        checks['old_observer_qualification_cannot_be_erased']=rejects(lambda:report.cost_comparison(a,b,bad,True))
        reg=a/'measurement/registration.json';saved=reg.read_bytes();v=read(reg);v['command'][0]='other-python';write(reg,v)
        checks['GNU_command_mismatch_rejected']=rejects(lambda:report.observed_gnu(a));reg.write_bytes(saved)
        # Exercise the real reporting branch for an unsuccessful measured command.
        fixture=t/'report_fixture';fixture.mkdir();root=fixture/'BNN_terminal_wire_qualified_comparison_02';root.mkdir()
        recovery=fixture/'recovery';recovery.mkdir()
        write(root/'plan.json',dict(recovery_queue=str(recovery),actual=str(a),baseline=str(b),qualification='Synthetic validation fixture, not native evidence.'))
        write(recovery/'completion.json',dict(status='registered_never_executed_tasks_terminal',passed=False,results={'terminal_wire':dict(returncode=1,verification=None)}))
        for name in ['complete_resource_prefix_quality_equivalence_v2.py','endpoint_timing_policy_streaming_v2.py','orphaned_flow_time_evidence_v2.py']:
            (fixture/name).write_bytes((D/name).read_bytes())
        saved_D=report.D;report.D=fixture
        try: report.main()
        finally: report.D=saved_D
        result=read(root/'completion.json')
        assert result['registered_roles']==1 and result['verified_complete_roles']==0
        assert result['actual_quality'] is None and result['actual_observer_wall_seconds']==777.
        checks['failed_configuration_retained_with_observed_cost_no_quality']=True
    output=D/'BNN_terminal_wire_qualified_comparison_validation_02.json'
    assert not output.exists()
    files=[Path(__file__).resolve(),Path(original.__file__),Path(qualified.__file__),Path(report.__file__),D/'orphaned_flow_time_evidence_v2.py']
    write(output,dict(passed=True,checks=checks,native_calls=0,production_data_rewritten=False,
        fixture_scope='Adversarial synthetic comparison/accounting checks only; no actual terminal result or speed claim.',
        source_sha256={str(p):sha(p) for p in files}))
    print(dict(passed=True,checks=len(checks),native_calls=0),flush=True)


if __name__=='__main__':main()
