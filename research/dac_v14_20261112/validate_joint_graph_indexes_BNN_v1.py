"""Compare all immutable payload bytes against the actual closed BNN baseline."""
import struct,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache

started=time.monotonic();root=D/'joint_graph_indexes_BNN_validation_01';done=read(root/'completion.json');assert done['passed'] and done['XML_traversals']==1
out=D/'joint_graph_indexes_BNN_payload_validation_01';out.mkdir(exist_ok=False)
reference=D/'complete_resource_timing_full_flow_01/bnn_native/flow'
assert read(reference.parent/'completion.json')['passed']
assert all(sha(root/n)==h for n,h in done['artifact_sha256'].items())
assert all(sha(p)==h for p,h in done['source_sha256'].items())
old_a=reference/'resource_flow/graph_audit_cache';old_f=reference/'resource_flow/full_graph_cache';old_q=reference/'physical_query_graph'
pairs=[(root/'audit_cache'/n,old_a/n) for n in ['nodes.npy','edges.npy','switches.npy']]
pairs += [(root/'full_cache'/n,old_f/n) for n in ['extra.npy','metadata.json']]
pairs += [(root/'query_graph/graph.bin',old_q/'graph.bin')]
checks=[]
for actual,expected in pairs:
 a,b=sha(actual),sha(expected);checks.append(dict(actual=str(actual),reference=str(expected),byte_exact=a==b,sha256=a,reference_sha256=b))
assert all(c['byte_exact'] for c in checks),checks
cache=FullRouteGraphCache(done['graph'],root/'full_cache')
q=read(root/'query_graph/graph_binding.json');oldq=read(old_q/'graph_binding.json')
for key in ['source_rrg_sha256','nodes','edges','unit','mean_span','binary_graph_sha256']:assert q[key]==oldq[key]
with (root/'query_graph/graph.bin').open('rb') as f:
 assert f.read(8)==b'H3DRQ001';header=struct.unpack('<IQdd',f.read(struct.calcsize('<IQdd')))
assert header==(q['nodes'],q['edges'],q['unit'],q['mean_span'])
write(out/'payload_comparison.json',checks);write(out/'reader_receipt.json',cache.receipt)
files=[Path(__file__).resolve(),D/'build_joint_graph_indexes_v1.py',D/'full_route_graph_cache.py',D/'immutable_rr_audit_cache.py',
 root/'completion.json',reference.parent/'completion.json',old_a/'completion.json',old_f/'completion.json',old_q/'completion.json']
write(out/'completion.json',dict(passed=True,native_calls_new=0,graph=done['graph'],graph_sha256=done['graph_sha256'],
 exact_payload_files=len(checks),audit_sorted_keys_and_query_original_edge_order_both_exact=True,
 nodes=done['nodes'],edges=done['edges'],new_shared_component_seconds=done['shared_complete_build_seconds'],
 old_component_phase_seconds=read(D/'complete_BNN_native_cost_analysis_01/summary.json')['disjoint_category_seconds']['graph_index_construction'],
 complete_readonly_validation_seconds=time.monotonic()-started,source_sha256={str(p):sha(p) for p in files},
 artifact_sha256={n:sha(out/n) for n in ['payload_comparison.json','reader_receipt.json']},
 qualification='All six actual payload files are byte-for-byte equal to their independently built formats in the sealed full native BNN reference, including the complete physical query graph and its edge order; unmodified production FullRouteGraphCache independently loads/verifies the new caches. One known graph, not multiple circuit/architecture confirmation. New shared standalone build and old within-full-command three-build costs are descriptive component observations with uncontrolled host/cache; no subtracting component deltas into whole runtime, no actual new route quality or complete algorithm speedup. The planned full engineering control must generate fresh indexes inside its own measured command and compare actual downstream states/requests/native work.'))
print(dict(passed=True,exact_payload_files=len(checks),nodes=done['nodes'],edges=done['edges'],new_component_seconds=done['shared_complete_build_seconds']),flush=True)
