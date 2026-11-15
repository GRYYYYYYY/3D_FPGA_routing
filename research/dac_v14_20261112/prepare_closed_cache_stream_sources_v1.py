"""Fork frozen scripts: explicit same-flow metadata and existing streaming loader.

No registered source is edited. Search, native binaries, acceptance, audits and
timeouts stay unchanged. The full engineering control combines two changes;
component measurements do not predict its complete cost.
"""
import ast
import difflib
from pathlib import Path
from retained_prefix_workflow import D, write, sha

mapping = {
    'run_serial_census_state_analysis_v1.py': 'run_serial_census_state_analysis_stream_v1.py',
    'run_serial_seed_resource_state_analysis_v1.py': 'run_serial_seed_resource_state_analysis_stream_v1.py',
    'run_independent_resource_state_analysis.py': 'run_independent_resource_state_analysis_stream_v1.py',
    'run_independent_timing_cone_analysis.py': 'run_independent_timing_cone_analysis_stream_v1.py',
    'run_serial_lazy_resource_transactions_v1.py': 'run_serial_lazy_resource_transactions_stream_v1.py',
    'run_serial_lazy_resource_repair_v1.py': 'run_serial_lazy_resource_repair_stream_v1.py',
    'run_complete_serial_joint_index_flow_v1.py': 'run_complete_serial_joint_stream_flow_v1.py',
    'run_registered_independent_transactions.py': 'run_registered_independent_stream_transactions_v1.py',
    'run_complete_flow_critical_portfolio_v1.py': 'run_complete_flow_critical_portfolio_stream_v1.py',
    'run_complete_resource_timing_joint_indexes_v1.py': 'run_complete_resource_timing_joint_stream_v1.py',
    'verify_complete_resource_timing_joint_indexes_v1.py': 'verify_complete_resource_timing_joint_stream_v1.py',
}
leaf = set(list(mapping)[:4])
diffs = []
records = []
for old, new in mapping.items():
    original = (D/old).read_text()
    source = original
    # Redirect calls and their source-binding entries consistently.
    for before, after in mapping.items():
        source = source.replace(before, after)
    if old in leaf:
        assert source.count('from endpoint_timing_policy import load') == 1
        source = source.replace('from endpoint_timing_policy import load',
                                'from endpoint_timing_policy_streaming_v2 import load')
        source = source.replace("D / 'endpoint_timing_policy.py'",
                                "D / 'endpoint_timing_policy_streaming_v2.py'")
    if old == 'run_registered_independent_transactions.py':
        a = "p.add_argument('--selector',choices=['full','compact'],default='compact');a=p.parse_args()"
        b = "p.add_argument('--selector',choices=['full','compact'],default='compact');p.add_argument('--audit-cache',type=Path,required=True);p.add_argument('--full-graph-cache',type=Path,required=True);a=p.parse_args()\na.audit_cache=a.audit_cache.resolve();a.full_graph_cache=a.full_graph_cache.resolve()\nassert a.audit_cache.parent==a.full_graph_cache.parent\nassert read(a.audit_cache/'completion.json')['passed'] and read(a.full_graph_cache/'completion.json')['passed']"
        assert source.count(a) == 1
        source = source.replace(a, b)
        source = source.replace("D/'rr_audit_cache_bnn_01'", 'a.audit_cache')
        source = source.replace("D/'full_route_graph_cache_bnn_01'", 'a.full_graph_cache')
        source = source.replace('if a.selector==\'compact\':\n proof=',
                                "selector_files += [a.audit_cache/'completion.json',a.full_graph_cache/'completion.json',D/'endpoint_timing_policy_streaming_v2.py']\nif a.selector=='compact':\n proof=", 1)
        assert 'rr_audit_cache_bnn_01' not in source and 'full_route_graph_cache_bnn_01' not in source
    if old == 'run_complete_flow_critical_portfolio_v1.py':
        source = source.replace("['initial-state','batch','query-graph','audit-cache']",
                                "['initial-state','batch','query-graph','audit-cache','full-graph-cache']")
        a = ' command=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic();status=\'completed\''
        b = " if script=='run_registered_independent_stream_transactions_v1.py':args=[*args,'--audit-cache',a.audit_cache,'--full-graph-cache',a.full_graph_cache]\n"+a
        assert source.count(a) == 1
        source = source.replace(a, b)
    if old == 'run_complete_resource_timing_joint_indexes_v1.py':
        a = "'--audit-cache',resource_flow/'graph_audit_cache','--policy'"
        b = "'--audit-cache',resource_flow/'graph_audit_cache','--full-graph-cache',resource_flow/'full_graph_cache','--policy'"
        assert source.count(a) == 1
        source = source.replace(a, b)
        a = "assert config['cache_mode']=='joint_build_inside_flow'"
        assert a in source
        source = source.replace(a, "assert config['endpoint_loader_strategy']=='existing_streaming_v2_all_observations'\nassert config['metadata_cache_strategy']=='explicit_same_measured_flow_only'\n"+a)
    if old == 'verify_complete_resource_timing_joint_indexes_v1.py':
        a = 'payload=dict(passed=True,complete_configuration_verified=True'
        assert source.count(a) == 1
        checks = """# Require actual metadata consumers, not merely index generation, inside flow.
assert config['endpoint_loader_strategy']=='existing_streaming_v2_all_observations'
assert config['metadata_cache_strategy']=='explicit_same_measured_flow_only'
metadata_consumers=[]
for receipt_path in flow.rglob('full_graph_cache_receipt.json'):
 receipt=read(receipt_path)
 for entry in [receipt,receipt['parent']]:
  consumed=Path(entry['cache_completion']).resolve()
  assert consumed.is_relative_to(flow),'External metadata cache consumer'
  assert consumed in [(resource_flow/'graph_audit_cache/completion.json').resolve(),(resource_flow/'full_graph_cache/completion.json').resolve()]
 metadata_consumers.append(str(receipt_path));files.append(receipt_path)
for analysis_path in timing.glob('round_*/proposal_*/transaction/*_audit/analysis.json'):
 analysis=read(analysis_path)
 if 'graph_cache' in analysis:
  consumed=Path(analysis['graph_cache']['cache_completion']).resolve()
  assert consumed==(resource_flow/'graph_audit_cache/completion.json').resolve()
  assert consumed.is_relative_to(flow),'External transaction metadata cache'
  metadata_consumers.append(str(analysis_path));files.append(analysis_path)
for costs_path in timing.glob('round_*/proposal_*/transaction/process_costs.json'):
 for row in read(costs_path):
  command=row.get('command',[])
  if '--cache' in command:assert Path(command[command.index('--cache')+1]).resolve()==(resource_flow/'graph_audit_cache').resolve()
  if '--full-graph-cache' in command:assert Path(command[command.index('--full-graph-cache')+1]).resolve()==(resource_flow/'full_graph_cache').resolve()
 files.append(costs_path)
assert metadata_consumers,'No actual metadata consumer receipts'
write(root/'metadata_consumers.json',dict(passed=True,all_within_measured_flow=True,receipts=metadata_consumers))
files.append(root/'metadata_consumers.json')
"""
        source = source.replace(a, checks+a)
        source = source.replace("Graph audit/full indexes and physical query graph are built inside;",
                                "Graph indexes are generated and actual metadata consumers remain inside this measured flow; existing streaming v2 validates all JSON lines and native COMPLETE/pin counts;")
    ast.parse(source)
    target = D/new
    assert not target.exists(), new
    target.write_text(source)
    diffs.extend(difflib.unified_diff(original.splitlines(True), source.splitlines(True),
                                      fromfile=old, tofile=new))
    records.append(dict(original=old, variant=new, original_sha256=sha(D/old),
                        variant_sha256=sha(target), native_binary_changes=False))
out = D/'closed_cache_stream_source_preparation_01'
out.mkdir(exist_ok=False)
(out/'sources.diff').write_text(''.join(diffs))
write(out/'manifest.json', dict(scripts=records, source_sha256={str(Path(__file__).resolve()):sha(__file__)},
      qualification='Two engineering changes: explicit same-flow metadata paths and adoption of already validated streaming v2 at remaining native observation sites. No native run, no new route quality/time. Frozen prior drivers remain unchanged.'))
print(dict(prepared=True, scripts=len(records), native_calls=0), flush=True)
