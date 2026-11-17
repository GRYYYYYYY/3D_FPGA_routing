"""Create a reversible source patch for a future release; do not install it."""
import ast
import difflib
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out=D/'owner_registration_development_fix_02';assert not out.exists()
plan=read(D/'cp1r3_distinct_input_cohort_01/plan.json')
runtime=Path(plan['release'])/'runtime'
helper=D/'owner_runtime_registration_v2.py'
sources={str(helper):sha(helper)}; edits=[]
transform={
 'current_owner_transaction_v1.py':[
  ('from controller_runtime import package_files','from controller_runtime import package_files\nfrom owner_runtime_registration_v2 import bind_runtime'),
  ("domain_mode='unrestricted', seed_order='delay_rr_id'):","domain_mode='unrestricted', seed_order='delay_rr_id', *, runtime_config):"),
  ("    write(output/'registration.json',registration)","    registration=bind_runtime(registration,runtime_config)\n    write(output/'registration.json',registration)"),
  ("    a=p.parse_args();r=prepare(a.state,a.root_state,a.selection,a.full_graph_cache,a.output,a.rank,a.domain_mode,a.seed_order)","    p.add_argument('--runtime-config',type=Path,required=True)\n    a=p.parse_args();r=prepare(a.state,a.root_state,a.selection,a.full_graph_cache,a.output,a.rank,a.domain_mode,a.seed_order,runtime_config=a.runtime_config)")],
 'run_unified_resource_repair_v1.py':[
  ('from controller_runtime import package_files,admit_controller','from controller_runtime import package_files,admit_controller\nfrom owner_runtime_registration_v2 import bind_for_execution'),
  (" registered=read(tx/'registration.json');registered['runtime_config']=str(a.runtime_config.resolve());registered['source_sha256'][str(a.runtime_config.resolve())]=sha(a.runtime_config);write(tx/'registration.json',registered)"," bind_for_execution(tx,a.runtime_config)"),
  ("prepared=prepare_owner(current,initial,owner_selection,cache_dir,tx,rank=oi,domain_mode='unrestricted',seed_order=a.seed_order)","prepared=prepare_owner(current,initial,owner_selection,cache_dir,tx,rank=oi,domain_mode='unrestricted',seed_order=a.seed_order,runtime_config=a.runtime_config)")]
}
pending={};patch=[]
for name,replacements in transform.items():
    p=runtime/name;before=p.read_text();after=before;sources[str(p)]=sha(p)
    for old,new in replacements:
        assert after.count(old)==1,(name,old)
        after=after.replace(old,new);edits.append(dict(file=name,old=old,new=new))
    ast.parse(after)
    restored=after
    for old,new in reversed(replacements):
        assert restored.count(new)==1
        restored=restored.replace(new,old)
    assert restored==before
    pending[name]=after
    patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/runtime/'+name,tofile='b/runtime/'+name))
assert all(sha(p)==h for p,h in sources.items())
out.mkdir();(out/'runtime').mkdir()
for name,content in pending.items():(out/'runtime'/name).write_text(content)
(out/'runtime'/helper.name).write_bytes(helper.read_bytes())
(out/'changes.patch').write_text(''.join(patch))
write(out/'source_patch.json',dict(passed=True,source_sha256=sources,edits=edits,
    development_source_sha256={str(p):sha(p) for p in (out/'runtime').iterdir()},
    inverse_transform_exact=True,new_native_or_STA_calls=0,installed_in_release=False,
    qualification='Prospective source patch only. Owner runtime binding moves before preparation sealing; invoke validates exact bytes before launch. Requests, selection, acceptance, terminal rules, and original verifier remain unchanged. The original historical failure is not repaired in place. Full future release packaging and end-to-end validation remain required.'))
print(dict(passed=True,edits=len(edits),source_patch=str(out),installed=False))
