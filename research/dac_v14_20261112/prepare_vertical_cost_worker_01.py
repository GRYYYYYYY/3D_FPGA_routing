"""Derive a private worker while retaining all established candidate gates."""
import ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'vertical_cost_baseline_dev_01';out=root/'run_vertical_cost_seed_analysis.py';assert not out.exists()
parent=D/'run_crossing_source_seed_analysis_v1.py';before=parent.read_text();after=before
replacements=[
 ("    parser.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],required=True)",
  "    parser.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],required=True)\n    parser.add_argument('--vertical-cost-weight',type=float,choices=[0.,.5,1.,2.],required=True)"),
 ("    args = parser.parse_args()", "    args = parser.parse_args()\n    assert not args.crossing_domain and not args.domain_feedback and not args.explicit_crossings\n    assert args.objective == 'weighted_soft' and args.candidate_full_sta and not args.trace_off\n    assert args.candidate_route is None and args.pressure_start == 1."),
 ("    stage = D / 'crossing_source_stage_01'", "    stage = D / 'vertical_cost_baseline_dev_01/build'"),
 ("observation_only=observation, trace_off=args.trace_off, source_sha256=hashes,",
  "observation_only=observation, trace_off=args.trace_off, source_sha256=hashes, vertical_cost_weight=args.vertical_cost_weight,"),
 ("    assert not args.domain_feedback or args.crossing_domain is not None",
  "    env['VPR_JOINT_NATIVE_VERTICAL_COST_WEIGHT']=format(args.vertical_cost_weight,'.17g')\n    env['VPR_JOINT_NATIVE_SEARCH_TRACE']=str(rd/'search_cost_trace.log')\n    assert not args.domain_feedback or args.crossing_domain is not None")]
for old,new in replacements:
    assert after.count(old)==1,old
    after=after.replace(old,new)
# Private script directory is not the research module root.
needle='from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, route_body'
after=after.replace('from coordinated_repair_tree import from_trace','')
after=after.replace(needle,"sys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom coordinated_repair_tree import from_trace\n"+needle)
ast.parse(after);out.write_text(after)
restored=after.replace("sys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom coordinated_repair_tree import from_trace\n"+needle,needle)
restored=restored.replace('import collections\n','import collections\nfrom coordinated_repair_tree import from_trace',1)
for old,new in reversed(replacements):restored=restored.replace(new,old)
assert restored==before,'Changes beyond registered worker adapter'
write(root/'worker_preparation.json',dict(passed=True,parent=str(parent),parent_sha256=sha(parent),
    worker=str(out),worker_sha256=sha(out),inverse_transform_exact=True,
    changes=[dict(old=a,new=b) for a,b in replacements],new_native_or_STA_calls=0,
    existing_FULL_STA_restoration_physical_and_input_gates_retained=True,
    build_executed=False,worker_executed=False))
print(dict(passed=True,worker=str(out),executed=False))
