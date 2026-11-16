"""Exercise new subset-domain auditor with real prior traces and adverse variants."""
import copy,subprocess,sys,tempfile,ast
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from compose_current_scope_union_v1 import compose
out=D/'robot_union_mechanism_validation_01';out.mkdir(exist_ok=False)
sharing=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00';owner=D/'robot_owner_scope_pair_01/transaction'
s=read(sharing/'registration.json')['roles']['reuse_on'];o=read(owner/'registration.json')['roles']['target_plus_owner'];union=compose(s,o)
assert len(union['queries'])==25 and len(union['removed_pins'])==5 and union['domain_nets']==[3140,3438,8785]
checks=[dict(name='actual_same_source_union',passed=True)]
for name,change in [('changed_source',lambda r:r.update(state=r['state']+'_different')),('changed_weight',lambda r:r['queries'][0].update(raw_criticality=.123)),('changed_budget',lambda r:r['fixed_resource_limits'].update(CB_sources=999))]:
 bad=copy.deepcopy(o);change(bad)
 try:compose(s,bad)
 except AssertionError:checks.append(dict(name=name,passed=True))
 else:raise AssertionError(name)
# Run real native evidence through the new auditor in private symlink fixtures.
# Original workers, audits, registration and domain evidence are never overwritten.
for name,allow_release,drop_net,expect in [('actual_release_trace',True,False,0),('release_disabled_on_actual_releases',False,False,1),('trace_contains_undeclared_domain_net',True,True,1)]:
 fixture=out/name;fixture.mkdir();role=copy.deepcopy(s);role['domain_failure_release']=allow_release
 if drop_net:
  mask=fixture/'domain.txt';mask.write_text('3\n3140\n3438\n8785\n');role['crossing_domain']=str(mask)
 write(fixture/'registration.json',dict(roles={'reuse_on':role}))
 (fixture/'reuse_on').symlink_to(sharing/'reuse_on',target_is_directory=True);(fixture/'reuse_on_audit').symlink_to(sharing/'reuse_on_audit',target_is_directory=True)
 with (fixture/'check.log').open('x') as log:
  r=subprocess.run([sys.executable,str(D/'audit_selected_retained_domain_v1.py'),'--batch',str(fixture),'--role','reuse_on'],stdout=log,stderr=subprocess.STDOUT)
 assert (r.returncode==0)==(expect==0),name
 checks.append(dict(name=name,passed=True,actual_returncode=r.returncode,expected_success=expect==0))
 if expect==0:
  result=read(fixture/'reuse_on_domain_audit.json');old=read(sharing/'reuse_on_domain_audit.json')
  for key in ['initial_domain_nets','final_domain_nets','released_queries','actual_candidate_guided_sources']:assert result[key]==old[key],key
# Verify the new backend differs only in explicit release dispatch/domain auditor and labels.
old=(D/'run_joint_crossing_source_transactions_v2.py').read_text();new=(D/'run_joint_crossing_source_transactions_v3.py').read_text()
assert "if role.get('domain_failure_release'):native_args+=['--domain-feedback']" in new
assert "'audit_selected_retained_domain_v1.py' if role.get('crossing_reuse_enabled')" in new
core=(D/'crossing_source_stage_01/h3d_joint_native_repair.h').read_text();assert 'VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE' in core and 'DOMAIN_RELEASE ' in core
checks.append(dict(name='native_option_and_new_dispatch_present',passed=True,qualification='Source capability/dispatch check, not new native execution.'))
files=[Path(__file__).resolve(),D/'compose_current_scope_union_v1.py',D/'audit_selected_retained_domain_v1.py',D/'run_joint_crossing_source_transactions_v3.py',D/'run_joint_crossing_source_transactions_v2.py',D/'crossing_source_stage_01/h3d_joint_native_repair.h',sharing/'registration.json',sharing/'reuse_on_domain_audit.json',owner/'registration.json']
write(out/'completion.json',dict(passed=True,checks=checks,union_connections=25,union_nets=5,restricted_nets=union['domain_nets'],new_native_calls=0,existing_receipts_unchanged=True,source_sha256={str(f):sha(f) for f in files},qualification='Actual prior released-domain trace passes new auditor; altered release policy and undeclared domain membership reject. New partial-domain combined native outcomes remain unexecuted.'))
print(dict(passed=True,checks=len(checks),native_calls=0))
