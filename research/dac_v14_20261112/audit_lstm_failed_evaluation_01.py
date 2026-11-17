"""Audit only the existing ctime-interfered evaluation, after registered audits.

No native/STA subprocesses, original completion writes, or whole-role admission.
The original failure stays authoritative; this records independent raw evidence.
"""
import argparse
import fcntl
import os
import time
import traceback
from pathlib import Path
from retained_prefix_workflow import D, read, write, route_body, sha
from recovery_prefix_v1 import Evidence, live_identity
from cp1r3_raw_admission_v1 import Audit, parse_request, parse_native, vector_digest
from endpoint_timing_policy_streaming_v2 import load, compare

RELEASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3')
FLOW = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/domain/flow')
TX = FLOW/'resource_flow/repair/round_013/candidate_00'


def exact_metadata_failure(seal, registration, prior, expected):
    """An exact incident exception, not a general ignore-ctime policy."""
    assert seal['passed'] is False
    failed = {p for p,row in seal['inputs'].items() if row['passed'] is False}
    assert failed == set(expected) and len(failed) == 5
    for p,h in registration['source_sha256'].items():
        assert seal['inputs'][p]['sha256'] == h
    for p in failed:
        old,new,bound = prior['inputs'][p],seal['inputs'][p],expected[p]
        assert old['passed'] is True
        assert old['sha256'] == new['sha256'] == registration['source_sha256'][p]
        assert old['stat_identity'][:4] == new['stat_identity'][:4]
        assert old['stat_identity'][4] != new['stat_identity'][4]
        assert new == bound['failed_final_seal']
        assert old == bound['prior_successful_seal']
    return True


def execute(output):
    # The original queue gets its unchanged first attempt before reconciliation.
    assert (D/'CP1r3_raw_admission_01/queue_priority_04/completion.json').exists()
    cohort = read(D/'cp1r3_distinct_input_cohort_01/queue_priority_02/registration.json')
    assert not live_identity(cohort['pid'],cohort['start_ticks'])
    assert not output.exists() and not output.resolve().is_relative_to(FLOW)
    with (D/'critical_scope_runner.lock').open('r') as serial:
        fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir(parents=True)
        started = time.monotonic(); evidence = Evidence()
        for name in ['audit_lstm_failed_evaluation_01.py','cp1r3_raw_admission_v1.py',
                     'recovery_prefix_v1.py','endpoint_timing_policy_streaming_v2.py']:
            evidence.bind(D/name)
        write(output/'execution_registration.json',dict(
            status='independent_failed_evaluation_raw_audit_registered',pid=os.getpid(),
            original_evaluation=str(TX/'reuse_on_evaluation'),
            source_sha256=evidence.bound.copy(),new_native_or_STA_calls=0))
        try:
            audit = Audit(RELEASE,evidence)
            doc = audit.document
            incident = doc(D/'LSTM_retention_metadata_incident_01/incident.json')
            evidence.verify({p:row['sha256'] for p,row in incident['source_evidence'].items()})
            expected = {row['path']:row for row in incident['failed_inputs']}
            evaluation = TX/'reuse_on_evaluation'; run = evaluation/'runs/state'
            assert not (evaluation/'completion.json').exists()
            assert not (run/'analysis_gate.json').exists()
            closed = doc(TX/'completion.json')
            assert closed['passed'] is False and closed['roles']['reuse_on']['status']=='FULL_STA_failed'
            registration = doc(evaluation/'registration.json')
            assert not live_identity(registration['pid'],registration['start_ticks'])
            seal = doc(evaluation/'input_seal.json')
            prior = doc(TX/'reuse_on/input_seal.json')
            exact_metadata_failure(seal,registration,prior,expected)
            evidence.verify(registration['source_sha256'])
            for p,row in seal['inputs'].items():evidence.bind(p,row['sha256'])
            source = Path(registration['source']).parent.parent
            role = doc(TX/'registration.json')['roles']['reuse_on']
            assert Path(role['state']).resolve() == source.resolve()
            original = audit.state(source,FLOW)
            control = audit.state(TX/'reuse_on',FLOW)
            assert all(original[k]==control[k] for k in ['route_body_sha256','vector_semantic_sha256','resources','packed_sha256','placed_sha256'])
            evidence.verify(role['source_sha256'])
            worker_manifest=doc(Path(control['run'])/'manifest.json');env=worker_manifest['environment']
            assert evidence.bind(role['request'])==evidence.bind(env['VPR_JOINT_NATIVE_REQUEST'])
            assert env['VPR_JOINT_NATIVE_OBJECTIVE']==role['objective']
            assert env['VPR_JOINT_NATIVE_SEED_ORDER']==role['seed_order']
            assert role['crossing_reuse_enabled'] and role['domain_failure_release']
            assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']=='1'
            assert evidence.bind(role['crossing_domain'])==evidence.bind(env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])
            request = parse_request(Path(role['request']).read_text(),role)
            native_log = Path(control['run'])/'joint_native.log';evidence.bind(native_log)
            with native_log.open() as stream:queries = parse_native(stream,request)
            assert queries['success']
            scope = doc(TX/'reuse_on_audit/analysis.json');assert scope['passed']
            evidence.verify(scope['source_sha256'])
            assert [(q['net'],q['pin']) for q in scope['queries']]==[(n,p) for n,p,c in request]
            domain = doc(TX/'reuse_on_domain_audit.json');assert domain['passed']
            evidence.verify(domain['source_sha256'])
            manifest = doc(run/'manifest.json')
            assert manifest['status']=='completed' and manifest['returncode']==0
            assert manifest['metrics']['native_full_check_passed']
            for p,row in manifest['shared_inputs'].items():evidence.bind(p,row['sha256'])
            for name,row in manifest['outputs'].items():evidence.bind(run/name,row['sha256'])
            assert evidence.bind(run/'routed.route')==evidence.bind(scope['candidate_route'],scope['candidate_sha256'])
            assert evidence.bind(run/'packed.net')==original['packed_sha256']
            assert evidence.bind(run/'placed.place')==original['placed_sha256']
            physical = doc(run/'independent_audit.json');proof=physical['audit']
            assert proof['passed'] and not proof['errors'] and proof['route']['overused_rr_nodes']==0
            evidence.bind(proof['inputs']['rr_graph'],proof['inputs']['rr_graph_sha256'])
            graph=manifest['command'][manifest['command'].index('--read_rr_graph')+1]
            assert evidence.bind(graph)==proof['inputs']['rr_graph_sha256']
            assert evidence.bind(run/'routed.route')==proof['inputs']['route_sha256']
            vector = doc(evaluation/'endpoint_vector.json');trace=run/'native_sta_frontier.jsonl'
            evidence.bind(trace,vector['trace_sha256'])
            evidence.bind(str(trace)+'.constraints.echo',vector['constraints_sha256'])
            assert vector_digest(load(trace))==vector_digest(vector)
            stdout=run/'stdout.log';evidence.bind(stdout)
            metrics=audit.metrics.parse_metrics(stdout.read_text(errors='replace'))
            assert metrics['native_full_check_passed'] and 'VPR succeeded' in stdout.read_text(errors='replace')
            assert metrics['critical_path_ns']==float(format(vector['cpd_s']*1e9,'.6g'))
            assert metrics['critical_path_ns']==manifest['metrics']['critical_path_ns']
            m=physical['physical_metrics']
            resources=dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
            assert metrics['wirelength']==resources['wirelength']
            endpoints=compare(read(source/'endpoint_vector.json'),vector)
            assert endpoints['compatible']
            assert not (evaluation/'completion.json').exists() and not (run/'analysis_gate.json').exists()
            evidence.unchanged()
            write(output/'audit.json',dict(passed=True,
                kind='independent_raw_evidence_of_historically_failed_evaluation',
                historical_status='FULL_STA_failed',historical_completion_created=False,
                candidate_admitted_to_controller=False,whole_role_admitted=False,
                clean_full_method_cost_admitted=False,CPD_ns=vector['cpd_s']*1e9,
                resources=resources,endpoints=endpoints,request=queries,
                route_body_sha256=route_body(run/'routed.route'),
                fixed_resource_limits=role['fixed_resource_limits'],
                source_sha256=evidence.bound,new_native_or_STA_calls=0,
                complete_additional_audit_seconds=time.monotonic()-started))
        except BaseException:
            write(output/'failure.json',dict(passed=False,error=traceback.format_exc(),
                complete_additional_audit_seconds=time.monotonic()-started,
                historical_failure_unchanged=True,new_native_or_STA_calls=0))
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    execute(parser.parse_args().output.resolve())
