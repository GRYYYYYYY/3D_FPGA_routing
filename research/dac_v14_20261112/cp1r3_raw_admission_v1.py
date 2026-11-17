"""Additional read-only admission after frozen-check replay; never route again.

Actual raw bytes and traces are consumed only under the shared serial lock.
Historical results remain untouched. Unsupported receipt schemas fail closed.
"""
import argparse
import collections
import fcntl
import hashlib
import importlib.util
import json
import math
import resource
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from retained_prefix_workflow import D, read, write, sha, route_body
from recovery_prefix_v1 import Evidence, live_identity
from endpoint_timing_policy_streaming_v2 import load, compare
from observation_timing_identity_v2 import check as timing_identity

ROOT = D/'CP1r3_raw_admission_01'
COHORT = D/'cp1r3_distinct_input_cohort_01'
SUPPLEMENT = D/'CP1r3_supplemental_verifier_01'
AXES = ['wirelength', 'SB_pairs', 'CB_sources']
GRAPH_FILES = ['audit_cache/nodes.npy', 'audit_cache/edges.npy',
               'audit_cache/switches.npy', 'full_cache/extra.npy',
               'full_cache/metadata.json', 'query_graph/graph.bin']


def parse_request(text, role):
    lines = text.splitlines(); cursor = 1; groups = int(lines[0]); pins = []
    assert groups >= 0 and not role['fixed_target_paths'], 'Protected paths require an explicit parser'
    for line in lines[cursor:cursor+groups]:
        fields = list(map(int, line.split()))
        assert len(fields) == fields[1]+2 and fields[0] >= 0 and fields[1] > 0
        pins.extend((fields[0], pin) for pin in fields[2:])
    cursor += groups
    assert int(lines[cursor]) == 0, 'Unparsed protected paths'; cursor += 1
    count = int(lines[cursor]); cursor += 1; queries = []
    for line in lines[cursor:cursor+count]:
        fields = line.split(); assert len(fields) == 3
        net, pin, criticality = int(fields[0]), int(fields[1]), float(fields[2])
        assert net >= 0 and pin > 0 and math.isfinite(criticality) and 0 <= criticality <= 1
        queries.append((net, pin, criticality))
    cursor += count
    assert cursor == len(lines) and len(queries) == count, 'Incomplete or trailing request'
    expected = [(q['net'], q['pin'], q['raw_criticality']) for q in role['queries']]
    assert queries == expected, 'Registered order/raw criticality mismatch'
    assert len(set(pins)) == len(pins) == count
    assert collections.Counter(pins) == collections.Counter((n,p) for n,p,c in queries)
    assert collections.Counter(pins) == collections.Counter(
        (int(n), p) for n, values in role['removed_pins'].items() for p in values)
    return queries


def parse_native(lines, expected):
    queries = []; attempts = 0; complete = None
    pairs = [(n,p) for n,p,c in expected]; pair_set = set(pairs)
    for line in lines:
        fields = line.split(); assert fields and complete is None, 'Rows after COMPLETE'
        kind = fields[0]
        if kind == 'QUERY':
            assert len(fields) == 8 and fields[3] in ['0','1']
            value = float(fields[4]); seconds = float(fields[7])
            assert math.isfinite(value) and 0 <= value <= 1
            assert math.isfinite(seconds) and seconds >= 0
            assert int(fields[5]) >= 0 and int(fields[6]) >= 0
            queries.append((int(fields[1]), int(fields[2]), fields[3] == '1'))
        elif kind == 'ATTEMPT':
            assert len(fields) == 6 and (int(fields[1]),int(fields[2])) in pair_set
            assert math.isfinite(float(fields[3])) and float(fields[3]) >= 1
            assert fields[4] in ['0','1'] and fields[5] in ['0','1']; attempts += 1
        elif kind == 'COMPLETE':
            assert len(fields) == 6 and fields[1] in ['0','1'] and fields[-1] == 'occupancy_restored'
            assert math.isfinite(float(fields[4])) and float(fields[4]) >= 0
            complete = fields
        else:
            assert kind in {'KEEP','NODE','FAIL_TARGET','FAIL_EDGE','OCC','MODE','DOMAIN_RELEASE'}, kind
    assert complete is not None
    assert int(complete[3]) == len(pairs)
    assert [(n,p) for n,p,ok in queries] == pairs[:len(queries)]
    finished = sum(ok for n,p,ok in queries)
    assert int(complete[2]) == finished
    success = complete[1] == '1'
    if success:
        assert len(queries) == finished == len(pairs)
    else:
        assert queries and not queries[-1][2] and all(q[2] for q in queries[:-1])
    return dict(success=success,requested=len(pairs),observed_queries=len(queries),
                successful_queries=finished,attempts=attempts,ordered_prefix_or_full_match=True)


def vector_digest(v):
    core = {k:v[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']}
    return hashlib.sha256(json.dumps(core,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class Audit:
    def __init__(self, release, evidence):
        self.e = evidence; self.states = {}; self.trace_vectors = {}; self.release = Path(release)
        path = self.release/'runtime/runtime_metrics.py'; self.e.bind(path)
        spec = importlib.util.spec_from_file_location('cp1r3_frozen_metrics_readonly',path)
        self.metrics = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.metrics)

    def document(self, path):
        self.e.bind(path); return read(path)

    def state(self, state, flow):
        state = Path(state).resolve(); assert state.is_relative_to(flow)
        if str(state) in self.states:return self.states[str(state)]
        done = self.document(state/'completion.json'); assert done['passed']
        run = Path(done['run']).resolve(); assert run.is_relative_to(state)
        manifest = self.document(run/'manifest.json')
        assert manifest['status'] == 'completed' and manifest['returncode'] == 0
        assert manifest['metrics']['native_full_check_passed']
        for path, row in manifest['shared_inputs'].items():self.e.bind(path,row['sha256'])
        # A route-mode command legitimately creates a new route. Private
        # input hashes are separately checked by original frozen/seal checks;
        # actual post-command outputs below bind the observed state.
        for name,row in manifest['outputs'].items():self.e.bind(run/name,row['sha256'])
        materialized = done.get('status') == 'standalone_candidate_materialization_terminal'
        if materialized:
            assert done['native_analysis_calls'] == 0 and done['consumed_already_executed_worker_receipt']
            self.e.verify(done['source_sha256'])
            reg = self.document(state/'registration.json'); self.e.verify(reg['source_sha256'])
            worker = Path(reg['source_worker']); source_control = self.state(worker,flow)
            exports = self.document(worker/'candidate_exports.json')
            assert exports['passed'] and exports['candidate_gate_present']
            assert manifest['execution_scope'] == 'standalone_installed_candidate_callback'
            assert manifest['observed_state_kind'] == 'installed_candidate'
            assert manifest['source_worker_completion'] == str(worker/'completion.json')
            native,restored = Path(exports['candidate']),Path(exports['restored'])
            for location,label in [(native,'candidate'),(restored,'restored_source')]:
                gate = location/'native_state_gate.txt'; self.e.bind(gate)
                assert gate.read_text() == label+' FULL fresh_STA actual_installed_trees\n'
            self.e.bind(native/'routed.route',manifest['actual_installed_candidate']['sha256'])
            serialized = manifest['serialized_candidate_route_provenance']
            assert serialized['same_complete_physical_tree_verified']
            assert self.e.bind(serialized['route'],serialized['sha256']) == self.e.bind(run/'routed.route')
            restored_trace = restored/'native_sta_frontier.jsonl'; self.e.bind(restored_trace)
            self.e.bind(str(restored_trace)+'.constraints.echo')
            assert vector_digest(load(restored_trace)) == source_control['vector_semantic_sha256']
            gate = self.document(run/'analysis_gate.json')
            assert all(gate[k] is True for k in ['passed','native_candidate_FULL_fresh_STA','physical_capacity_audit','source_restored'])
            analysis = self.document(state/'independent_native_analysis_audit.json')
            assert analysis['passed'] and analysis['legal_count'] == 1 and analysis['failed_count'] == 0
        else:
            seal = self.document(state/'input_seal.json'); assert seal['passed']
            for path,row in seal['inputs'].items():
                assert row['passed']; self.e.bind(path,row['sha256'])
        physical = self.document(run/'independent_audit.json')
        proof = physical['audit']; assert proof['passed'] and not proof['errors']
        assert proof['route']['overused_rr_nodes'] == 0
        self.e.bind(proof['inputs']['rr_graph'],proof['inputs']['rr_graph_sha256'])
        assert self.e.bind(run/'routed.route') == proof['inputs']['route_sha256']
        if Path(proof['inputs']['route']).resolve() != run/'routed.route':
            reuse = self.document(state/'physical_audit_reuse.json'); assert reuse['passed']
            origin = Path(reuse['original']).resolve(); assert origin.is_relative_to(flow)
            assert self.e.bind(origin,reuse['original_sha256']) == self.e.bind(run/'independent_audit.json')
            assert self.e.bind(proof['inputs']['route'],reuse['exact_route_sha256']) == self.e.bind(run/'routed.route')
            assert reuse['graph_sha256'] == proof['inputs']['rr_graph_sha256']
        graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
        assert self.e.bind(graph) == proof['inputs']['rr_graph_sha256']
        vector = self.document(state/'endpoint_vector.json')
        trace = run/'native_sta_frontier.jsonl'; digest = self.e.bind(trace)
        self.e.bind(str(trace)+'.constraints.echo',vector['constraints_sha256'])
        assert vector['trace_sha256'] == digest
        # Deduplicate parsing only for identical actual trace and constraint
        # bytes within this audit. Each file is independently hashed first.
        key = (digest,vector['constraints_sha256'])
        if key not in self.trace_vectors:
            raw = load(trace); self.trace_vectors[key] = vector_digest(raw)
        assert vector_digest(vector) == self.trace_vectors[key], 'Stored vector differs from raw STA'
        stdout = (run/'stdout.log').read_text(errors='replace')
        if materialized:
            native_trace = native/'native_sta_frontier.jsonl'
            assert self.e.bind(native_trace) == digest
            assert self.e.bind(str(native_trace)+'.constraints.echo') == vector['constraints_sha256']
            original_stdout = (Path(source_control['run'])/'stdout.log').read_text(errors='replace')
            begin,end = 'H3D_ACTUAL_STATE_BEGIN candidate\n','H3D_ACTUAL_STATE_COMPLETE candidate\n'
            assert original_stdout.count(begin) == original_stdout.count(end) == 1
            fragment = original_stdout.split(begin,1)[1].split(end,1)[0]
            assert stdout == begin+fragment+end and 'Completed routing consistency check successfully.' in fragment
            assert manifest['metrics']['critical_path_ns'] == vector['cpd_s']*1e9
        else:
            metrics = self.metrics.parse_metrics(stdout)
            assert metrics['native_full_check_passed'] and 'VPR succeeded' in stdout
            assert float(format(vector['cpd_s']*1e9,'.6g')) == metrics['critical_path_ns']
            assert metrics['critical_path_ns'] == manifest['metrics']['critical_path_ns']
        body = route_body(run/'routed.route'); assert body == done['route_body_sha256']
        m = physical['physical_metrics']
        row = dict(state=str(state),run=str(run),route_body_sha256=body,
            packed_sha256=self.e.bind(run/'packed.net'),placed_sha256=self.e.bind(run/'placed.place'),
            vector_semantic_sha256=vector_digest(vector),CPD_ns=vector['cpd_s']*1e9,
            constraints_sha256=vector['constraints_sha256'],raw_STA_sha256=digest,
            resources=dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],
                SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used']),
            actual_FULL_raw_STA_and_original_physical_proof_bound=True)
        self.states[str(state)] = row; return row

    def transaction(self, tx, flow):
        registration = self.document(tx/'registration.json'); progress = self.document(tx/'progress.json')
        closed = self.document(tx/'completion.json'); assert closed['passed']
        self.e.verify(closed['source_sha256']); results = []
        assert set(progress) == set(registration['roles'])
        for name,role in registration['roles'].items():
            row = progress[name]; worker = tx/name
            self.e.verify(role['source_sha256'])
            if row['status'] == 'not_executed_domain_candidate_accepted':
                assert name == 'reuse_off' and not worker.exists()
                assert progress['reuse_on']['policies']['resources_under_timing']['accepted']
                results.append(dict(role=name,status=row['status'],native_calls_new=0)); continue
            assert not row.get('native_reused'), 'External/native reuse needs a separate explicit provenance adapter'
            source = self.state(role['state'],flow); control = self.state(worker,flow)
            assert all(source[k] == control[k] for k in
                ['route_body_sha256','packed_sha256','placed_sha256','vector_semantic_sha256'])
            wr = self.document(worker/'registration.json')
            assert not live_identity(wr['pid'],wr['start_ticks'])
            self.e.verify(wr['source_sha256'])
            run = Path(control['run']); manifest = self.document(run/'manifest.json'); env = manifest['environment']
            assert self.e.bind(role['request']) == self.e.bind(env['VPR_JOINT_NATIVE_REQUEST'])
            assert env['VPR_JOINT_NATIVE_OBJECTIVE'] == role['objective']
            assert env['VPR_JOINT_NATIVE_SEED_ORDER'] == role['seed_order']
            assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE'] == ('1' if role['domain_failure_release'] else '0')
            if role['crossing_reuse_enabled']:
                assert self.e.bind(role['crossing_domain']) == self.e.bind(env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])
            else:assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'] == ''
            request = parse_request(Path(role['request']).read_text(),role)
            self.e.bind(run/'joint_native.log')
            with (run/'joint_native.log').open() as stream:actual = parse_native(stream,request)
            audit = self.document(tx/(name+'_audit/analysis.json')); assert audit['passed']
            if actual['success']:
                assert row['status'] == 'legal_evaluated' and audit['candidate_route']
                self.e.verify(audit['source_sha256'])
                candidate = Path(audit['candidate_route']); self.e.bind(candidate,audit['candidate_sha256'])
                evaluated = self.state(row['evaluation'],flow)
                assert route_body(candidate) == evaluated['route_body_sha256']
                assert row['resources'] == evaluated['resources'] and row['cpd_s']*1e9 == evaluated['CPD_ns']
                assert [(q['net'],q['pin']) for q in audit['queries']] == [(n,p) for n,p,c in request]
            else:
                assert row['status'] == 'transaction_failed_rolled_back' and audit['candidate_route'] is None
            domain = tx/(name+'_domain_audit.json')
            if domain.exists():
                result = self.document(domain); assert result['passed']
                self.e.verify(result.get('source_sha256',{}))
            results.append(dict(role=name,status=row['status'],request=actual))
        return dict(transaction=str(tx),roles=results)

    def case(self, target, original, out):
        case = Path(target['case']); flow = (case/'flow').resolve()
        supplement = SUPPLEMENT/'cases'/target['input']/target['arm']/'completion.json'
        supplemental = self.document(supplement)
        assert supplemental['passed'] and supplemental['original_frozen_result_unchanged']
        self.e.verify(supplemental['source_sha256'])
        replay = self.document(supplement.parent/'replayed_verifier/completion.json')
        assert replay['passed'] and replay['complete_configuration_verified']
        measure = self.document(case/'measurement/completion.json')
        assert measure['passed'] and measure['returncode'] == 0 and not measure['live_descendants_after_command_exit']
        assert not any(live_identity(pid,tick) for pid,tick in measure['process_identities'].items())
        assert measure['complete_command_wall_seconds'] == original['complete_seconds']
        config = self.document(case/'config.json'); self.e.verify(config['input_sha256'])
        self.e.bind(target['config'],target['config_sha256'])
        admission = self.document(case/'confirmation_input.json')
        assert admission['passed'] and admission['release_manifest_sha256'] == read(ROOT/'plan.json')['release_manifest_sha256']
        assert admission['configuration_sha256'][target['arm']] == target['config_sha256']
        done = self.document(flow/'completion.json'); assert done['passed']; self.e.verify(done['source_sha256'])
        joint = flow/'resource_flow/joint_graph_indexes'; graphs = self.document(joint/'completion.json')
        assert graphs['passed']; self.e.bind(graphs['graph'],graphs['graph_sha256'])
        self.e.verify(graphs['source_sha256'])
        for name,digest in graphs['artifact_sha256'].items():self.e.bind(joint/name,digest)
        states = [self.state(p.parent,flow) for p in sorted(flow.rglob('endpoint_vector.json'))]
        assert states
        txs = []
        for path in sorted(flow.rglob('registration.json')):
            value = read(path)
            if 'roles' in value:txs.append(self.transaction(path.parent,flow))
        # All named terminal/selection states must be among the raw-audited set.
        for field in ['initial_state','resource_final_state','resource_policy_final_state','timing_initial_state','final_state']:
            assert str(Path(done[field]).resolve()) in self.states
        initial,final = [self.states[str(Path(done[k]).resolve())] for k in ['initial_state','final_state']]
        assert final['resources'] == replay['resources'] and final['CPD_ns'] == replay['CPD_ns']
        endpoints = compare(read(Path(initial['state'])/'endpoint_vector.json'),read(Path(final['state'])/'endpoint_vector.json'))
        assert endpoints['compatible']; write(out/'own_initial_final_endpoints.json',endpoints)
        no_gain = (initial['resources'] == final['resources'] and initial['vector_semantic_sha256'] == final['vector_semantic_sha256'])
        write(out/'states.json',states); write(out/'transactions.json',txs)
        return dict(passed=True,status='supplementary_full_admission_passed',quality_admitted=True,
            original_verification_passed=original['status']=='complete_legal_verified',
            original_status=original['status'],supplementary_verification_passed=True,
            execution_ended=True,timeout=False,infrastructure_error=False,legal_no_gain=no_gain,
            legal_no_gain_definition='Identical final physical resource counts and complete timing vector to own root',
            quality=dict(CPD_ns=final['CPD_ns'],resources=final['resources']),initial=initial,final=final,
            graph_payload_sha256={name:self.e.bind(joint/name) for name in GRAPH_FILES},
            complete_algorithm_seconds=original['complete_seconds'],
            original_verification_seconds=original['independent_research_verification_seconds'],
            original_failures_preserved=True,new_native_or_STA_calls=0,
            original_physical_proof_revalidated=True,new_physical_solver_executions=0)


def execute():
    plan = read(ROOT/'plan.json'); assert not (ROOT/'execution').exists()
    for q in [COHORT/'queue_priority_02', SUPPLEMENT/'queue_priority_03']:
        assert (q/'completion.json').exists()
        reg = read(q/'registration.json'); assert not live_identity(reg['pid'],reg['start_ticks'])
    lock = (D/'critical_scope_runner.lock').open('r'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    e = Evidence(); e.bind(ROOT/'plan.json'); e.verify(plan['source_sha256'])
    out = ROOT/'execution'; out.mkdir(); started = time.monotonic(); audit = Audit(plan['release'],e); rows = []
    for target in plan['targets']:
        before = time.monotonic(); cpu = time.process_time(); dest = out/target['input']/target['arm']; dest.mkdir(parents=True)
        original_path = COHORT/(target['input']+'_results.json'); e.bind(original_path)
        original = read(original_path)[target['arm']]
        supplement = SUPPLEMENT/'cases'/target['input']/target['arm']/'completion.json'
        try:
            if not supplement.exists() or not read(supplement)['passed']:
                row = dict(passed=False,status='not_admitted_original_or_supplementary_checks_incomplete',
                    quality_admitted=False,quality=None,original_status=original['status'],legal_no_gain=None,
                    execution_ended=original.get('measurement') is not None,
                    timeout='timeout' in original['status'],infrastructure_error=None,
                    original_verification_passed=original['status']=='complete_legal_verified',
                    complete_algorithm_seconds=original['complete_seconds'])
            else:row = audit.case(target,original,dest)
        except Exception:
            error = traceback.format_exc(); (dest/'failure.log').write_text(error)
            row = dict(passed=False,status='additional_raw_admission_failed',quality_admitted=False,quality=None,
                original_status=original['status'],legal_no_gain=None,infrastructure_error=True,
                complete_algorithm_seconds=original['complete_seconds'],error=error)
        row.update(input=target['input'],arm=target['arm'],readonly_audit_seconds=time.monotonic()-before,
            readonly_CPU_seconds=time.process_time()-cpu,new_native_or_STA_calls=0,original_failure_rewritten=False)
        write(dest/'completion.json',row); rows.append(row); write(out/'roles.json',rows)
    pairs = []
    for name in dict.fromkeys(t['input'] for t in plan['targets']):
        pair = {r['arm']:r for r in rows if r['input']==name}; n,d = pair['native'],pair['domain']
        item = dict(input=name,matched=False,delta_domain_minus_native=None)
        if n['passed'] and d['passed']:
            item['matched'] = all(n['initial'][k] == d['initial'][k] for k in
                ['route_body_sha256','packed_sha256','placed_sha256','vector_semantic_sha256']) and n['graph_payload_sha256']==d['graph_payload_sha256']
            if item['matched']:
                change = compare(read(Path(n['final']['state'])/'endpoint_vector.json'),read(Path(d['final']['state'])/'endpoint_vector.json'))
                assert change['compatible']; write(out/(name+'_paired_endpoints.json'),change)
                item.update(delta_domain_minus_native={**{k:d['quality']['resources'][k]-n['quality']['resources'][k] for k in AXES},
                    'CPD_ns':d['quality']['CPD_ns']-n['quality']['CPD_ns'],
                    'complete_seconds':d['complete_algorithm_seconds']-n['complete_algorithm_seconds']},
                    endpoint_summary={k:v for k,v in change.items() if k!='changes'})
        pairs.append(item)
    e.unchanged(); write(out/'pairs.json',pairs)
    write(out/'completion.json',dict(passed=True,status='all_registered_roles_accounted',
        all_roles_admitted=all(r['passed'] for r in rows),registered_roles=len(rows),
        matched_pairs=[p['input'] for p in pairs if p['matched']],complete_readonly_seconds=time.monotonic()-started,
        process_max_RSS_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=e.bound,
        new_native_or_STA_calls=0,original_failures_preserved=True,automatic_manuscript_update=False,
        qualification='Whole frozen-check replay plus additional actual-byte/request/raw-STA and original physical-proof binding. Revalidated physical proof, not a new physical solver run. Failed/ineligible roles stay null; complete algorithm times are original measured commands, audit costs separate. Pair matching permits descriptive within-input comparison only, not interleaved timing, independent architectures or universal benefit.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--execute',action='store_true'); args = parser.parse_args()
    assert args.execute; execute()
