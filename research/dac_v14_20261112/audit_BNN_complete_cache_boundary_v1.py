"""Audit actual metadata cache consumers; no native replay or timing adjustment."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out = D/'BNN_complete_cache_boundary_01'
out.mkdir(exist_ok=False)
case = D/'complete_resource_timing_full_flow_01/bnn_native'
flow = case/'flow'
done = read(case/'completion.json')
assert done['passed']
files = [Path(__file__).resolve(), case/'completion.json']
components = {
    'audit': (flow/'resource_flow/graph_audit_cache', ['nodes.npy','edges.npy','switches.npy']),
    'full': (flow/'resource_flow/full_graph_cache', ['extra.npy','metadata.json']),
}
verified = {}
def verify_payload(directory, kind):
    directory = Path(directory).resolve()
    key = str(directory), kind
    if key in verified:
        return verified[key]
    original, names = components[kind]
    left, right = read(directory/'completion.json'), read(original/'completion.json')
    assert left['passed'] and right['passed']
    assert left['graph_sha256'] == right['graph_sha256']
    pairs = []
    for name in names:
        actual, expected = sha(directory/name), sha(original/name)
        assert actual == left['payload_sha256'][name]
        assert expected == right['payload_sha256'][name]
        assert actual == expected
        pairs.append(dict(file=name, byte_exact=True, sha256=actual))
        files.extend([directory/name, original/name])
    files.extend([directory/'completion.json', original/'completion.json'])
    result = dict(directory=str(directory), expected_same_command=str(original), payloads=pairs,
                  graph_sha256=left['graph_sha256'])
    verified[key] = result
    return result

rows = []
for attempt in read(flow/'timing/attempts.json'):
    tx = Path(attempt['evaluation']).parent
    # Actual attempt schema is checked rather than inferring a successful role.
    if not (tx/'registration.json').exists() and (tx/'transaction/registration.json').exists():
        tx = tx/'transaction'
    roles = read(tx/'registration.json')['roles']
    for role in roles:
        audit = tx/(role+'_audit/analysis.json')
        if not audit.exists():
            continue
        analysis = read(audit)
        assert analysis['passed']
        if 'graph_cache' in analysis:
            receipt = analysis['graph_cache']
            directory = Path(receipt['cache_completion']).parent
            proof = verify_payload(directory, 'audit')
            rows.append(dict(kind='native_scope_capacity_audit', receipt=str(audit),
                             directory=str(directory), within_actual_flow=directory.is_relative_to(flow),
                             byte_exact_same_command_payload=True))
            files.append(audit)
        evaluation = tx/(role+'_evaluation')
        receipt_path = evaluation/'full_graph_cache_receipt.json'
        if receipt_path.exists():
            receipt = read(receipt_path)
            directory = Path(receipt['cache_completion']).parent
            verify_payload(directory, 'full')
            parent = Path(receipt['parent']['cache_completion']).parent
            verify_payload(parent, 'audit')
            rows.append(dict(kind='candidate_LOAD_full_physical_audit', receipt=str(receipt_path),
                             directory=str(directory), parent_directory=str(parent),
                             within_actual_flow=directory.is_relative_to(flow) and parent.is_relative_to(flow),
                             byte_exact_same_command_payload=True))
            files.append(receipt_path)
assert len(rows) == 6 and all(not r['within_actual_flow'] for r in rows)
assert all(r['byte_exact_same_command_payload'] for r in rows)
paths = sorted({str(Path(f).resolve()) for f in files})
write(out/'consumers.json', rows)
write(out/'payloads.json', list(verified.values()))
write(out/'completion.json', dict(passed=True, native_calls=0,
      actual_complete_seconds=done['complete_wall_seconds'],
      external_metadata_consumers=len(rows), metadata_payloads_byte_exact=True,
      route_candidate_or_query_history_import_detected=False,
      original_whole_command_cost_adjustment_seconds=0,
      source_sha256={p:sha(p) for p in paths},
      artifact_sha256={n:sha(out/n) for n in ['consumers.json','payloads.json']},
      qualification='Actual completed BNN timing uses six external immutable metadata-cache references despite building byte-identical audit/full indexes inside the measured command. No external route, native candidate or query result is implicated. Every consumed metadata payload is byte-exact to its own-command generated payload. Actual quality and7933.245508622378s total remain unchanged and inseparable; no cost subtraction/addition. The strictly closed-input reproduction claim must be qualified: the legacy metadata aliases are additional static runtime dependencies. Pending joint-index control reuses this coordinator and is expected to retain that path behavior; its actual execution is not yet observed. A separate explicit cache-path version must verify every actual consumer remains inside its measured flow.'))
print(dict(passed=True, actual_external_consumers=len(rows), all_payloads_exact=True), flush=True)
