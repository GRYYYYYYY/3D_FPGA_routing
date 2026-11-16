"""Check scheduling transforms and actual leases without creating replacement queues."""
import ast,copy,os,signal,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from confirmation_priority_waiter_guard_02 import check

root=D/'confirmation_priority_handoff_02';plan=read(root/'plan.json');checks=[];guards=[]
assert hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal')
fd=os.pidfd_open(os.getpid());os.close(fd)
assert all(sha(p)==h for p,h in plan['protected_source_sha256'].items())
for path,row in plan['revisions'].items():
    text=Path(path).read_text();ast.parse(text);assert sha(path)==row['sha256']
    if row.get('only_status_destination_changed'):
        for old,new,count in reversed(row['replacements']):assert text.count(new)==count;text=text.replace(new,old)
    else:
        assert text.startswith(row['bootstrap']);text=text[len(row['bootstrap']):]
        assert text.count(row['added_source_binding'])==1;text=text.replace(row['added_source_binding'],'',1)
        for old,new,count in reversed(row['replacements']):assert text.count(new)==count;text=text.replace(new,old,count)
    assert text==Path(row['parent']).read_text() and sha(row['parent'])==row['parent_sha256']
    checks.append('source_reverses_'+Path(path).name)
for i,node in enumerate(plan['stages']):
    check(node)
    expected=Path(plan['active_predecessor']) if i==0 else Path(plan['stages'][i-1]['new_queue'])
    assert Path(node['predecessor'])==expected
    for label,update in [('wrong_pid',dict(pid=node['pid']+1)),('wrong_start_ticks',dict(start_ticks='0')),('wrong_script',dict(old_script='/not/the/queue.py')),('existing_execution',dict(forbidden_paths=[node['old_queue']]))]:
        changed={**node,**update}
        try:check(changed)
        except AssertionError:guards.append(node['batch']+'_'+label)
        else:raise AssertionError('Lease guard failed '+label)
    # Execute only AST nodes before q assignment. All real imports and
    # protocol reads run, while queue creation/native work remain unreachable.
    code="""import ast,sys
from pathlib import Path
p=Path(sys.argv[1]);tree=ast.parse(p.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='q' for t in n.targets):break
 nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),{'__file__':str(p),'__name__':'__priority_startup_probe__'})
print('queue imports and protocol reads passed before queue creation')
"""
    result=subprocess.run([sys.executable,'-I','-B','-c',code,node['wrapper']],capture_output=True,text=True,timeout=30,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert result.returncode==0,(node['batch'],result.stdout,result.stderr)
    assert not Path(node['new_queue']).exists();checks.append('actual_import_prefix_'+node['batch'])
selected=read(D/'cp1r3_distinct_input_cohort_01/protocol.json')['selected_inputs']
assert [row['id'] for row in selected]==['lstm','dla_small','eltwise_sb']
placement=read(D/'cp1r3_distinct_input_cohort_01/placement_independence_01.json');assert placement['passed']
files=[Path(__file__).resolve(),D/'prepare_confirmation_priority_handoff_02.py',D/'confirmation_priority_waiter_guard_02.py',D/'apply_confirmation_priority_handoff_02.py',root/'plan.json',*map(Path,plan['revisions'])]
for p in files:
    if p.suffix=='.py':ast.parse(p.read_text())
write(root/'validation.json',dict(passed=True,checks=checks,lease_negative_guards=guards,actual_waiting_owners=6,
    source_transforms_reversible=True,actual_import_prefixes_executed=True,replacement_queues_created=False,
    input_or_fixed_confirmation_algorithm_changes=False,new_native_calls=0,
    source_sha256={str(p):sha(p) for p in files},
    qualification='Scheduling/status/provenance change only. Real queue leases are waiting, child-free and have no method outputs. Six import-prefix probes stop before queue creation. Original experimental protocols/core method code are unchanged; actual handoff/cancellation/startup follows this validation.'))
print(dict(passed=True,checks=len(checks),lease_negative_guards=len(guards),native_calls=0))
