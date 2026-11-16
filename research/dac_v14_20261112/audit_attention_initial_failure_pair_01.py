"""Bounded audit of two actually closed initial-route failures; no native work."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).resolve().parent
Q = D / 'unified_input_integration_01'
OUT = D / 'attention_initial_failure_pair_01'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not OUT.exists(), 'Do not overwrite the observed pair or repeat native work'
    names = ['attention_native', 'attention_domain']
    results = read(Q / 'queue/results.json')
    configs = [read(Q / 'configs' / (name + '.json')) for name in names]
    differences = [key for key in configs[0].keys() | configs[1].keys()
                   if configs[0].get(key) != configs[1].get(key)]
    assert set(differences) == {'domain_mode', 'domain_feedback'}
    files = [Path(__file__).resolve(), Q / 'plan.json']
    manifests, normalized_commands, private_inputs, shared_inputs, outcomes = [], [], [], [], {}
    for name in names:
        case = Q / name
        run = case / 'flow/resource_flow/initial/runs/state'
        config = Q / 'configs' / (name + '.json')
        manifest_path = run / 'manifest.json'
        measurement_path = case / 'measurement/completion.json'
        manifest, measurement = read(manifest_path), read(measurement_path)
        row = results[name]
        assert row['status'] == 'initial_route_failed' and row['quality'] is None
        assert row['completion'] is None and row['command_returncode'] == 1
        assert manifest['status'] == manifest['execution_status'] == 'failed'
        assert manifest['returncode'] == 2 and measurement['returncode'] == 1
        assert not measurement['passed'] and not measurement['live_descendants_after_command_exit']
        assert not manifest['metrics']['routing_success_reported']
        assert not manifest['metrics']['native_full_check_passed']
        assert row['complete_seconds'] == measurement['complete_command_wall_seconds']
        assert Path(row['measurement']) == measurement_path
        assert not (case / 'flow/resource_flow/repair').exists()
        assert not (case / 'flow/timing').exists()
        command = manifest['command']
        assert command[command.index('--max_router_iterations') + 1] == '200'
        assert command[command.index('--routing_failure_predictor') + 1] == 'off'
        assert command[command.index('--router_max_convergence_count') + 1] == '8'
        assert manifest['timeout_seconds'] == 1800
        normalized_commands.append([arg.replace(str(run), '<private-run>') for arg in command])
        private = {Path(path).name: value for path, value in manifest['private_input_sha256'].items()}
        assert len(private) == 2 and set(private) == {'packed.net', 'placed.place'}
        assert all(manifest['outputs'][key]['sha256'] == value for key, value in private.items())
        private_inputs.append(private)
        shared = manifest['shared_inputs']
        assert shared[str(config)]['sha256'] == digest(config)
        primary = [command[0], command[1], command[2], command[command.index('--read_rr_graph') + 1]]
        recorded = {}
        for path in primary:
            item = shared[path]
            st = Path(path).stat()
            assert list(item['stat_identity']) == [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
            recorded[path] = item['sha256']
        shared_inputs.append(recorded)
        log = (run / 'stdout.log').read_text()
        assert digest(run / 'stdout.log') == manifest['outputs']['stdout.log']['sha256']
        assert 'Routing failed.' in log and 'VPR failed to implement circuit' in log
        overused = re.findall(r'Total number of overused nodes: (\d+)', log)
        assert overused == ['231']
        assert re.search(r'^\s*200\s+\d+\.\d+\s+', log, re.MULTILINE)
        assert manifest['environment']['VPR_H3D_MODE'] == 'off'
        outcomes[name] = dict(status='initial_route_failed', quality=None,
            full_method_repair_entered=False, overused_nodes=231, completed_router_iterations=200,
            complete_command_wall_seconds=measurement['complete_command_wall_seconds'],
            sampled_tree_PSS_peak_kib=measurement['sampled_tree_PSS_peak_kib'],
            missing_memory_observations=measurement['missing_memory_observations'],
            original_native_returncode=manifest['returncode'], command_returncode=measurement['returncode'],
            live_descendants_after_command_exit=[], manifest=str(manifest_path), measurement=str(measurement_path))
        files += [config, manifest_path, measurement_path, run / 'stdout.log', run / 'time.txt']
        manifests.append(manifest)
    assert normalized_commands[0] == normalized_commands[1]
    assert private_inputs[0] == private_inputs[1] and shared_inputs[0] == shared_inputs[1]
    assert manifests[0]['execution_limit'] == manifests[1]['execution_limit']
    notes = [Q / 'measurement_environment_note_01.json',
             D / 'publication_housekeeping_20261116_01/intervention.json',
             D / 'publication_housekeeping_20261116_01/verification.json']
    assert all(path.exists() for path in notes)
    OUT.mkdir()
    snapshot = OUT / 'queue_results_at_analysis.json'
    write(snapshot, {name: results[name] for name in names})
    files += notes + [snapshot]
    result = dict(passed=True, observed_at=datetime.now(timezone.utc).isoformat(),
        status='matched_initial_failure_receipts_verified', registered_roles=2,
        closed_roles=2, legal_complete_roles=0, native_calls_new=0,
        matched_actual_route_commands_except_private_paths=True,
        matched_recorded_private_input_hashes=private_inputs[0],
        matched_recorded_primary_shared_input_hashes=shared_inputs[0],
        recorded_primary_shared_stat_identities_still_match=True,
        input_hash_scope='Recorded runner digests and current stat identities; no new large-input rehash during measured successor.',
        treatment_config_differences=sorted(differences), outcomes=outcomes,
        independent_sample_count_claim=None, final_legal_endpoint_comparison=None,
        environment_notes=[str(path) for path in notes],
        source_sha256={str(path): digest(path) for path in files},
        qualification='One circuit/physical-input pair, two failed arms; preserve both costs and failures. No legal repair starting route was obtained, so domain, failure-release and owner benefits are not evaluated here. Failed-route CPD/wire fields and illegal output routes are not legal quality points. This is the earlier registered development version, not dev03 confirmation or an unseen-input claim. Native timing includes the documented short Git-housekeeping overlap; neither time is a controlled/interleaved speed comparison. No experiment, rule, queue or input modified; no additional native execution.')
    write(OUT / 'completion.json', result)
    print(json.dumps({key: result[key] for key in ['passed', 'status', 'closed_roles', 'legal_complete_roles', 'native_calls_new']}))


if __name__ == '__main__':
    main()
