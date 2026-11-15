"""Cross-check every completed private native-census candidate against direct audit."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import resource_assurance,require_publication_proof

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
queue=D/'native_census_resource_equivalence_recovery_02/queue';registry=read(queue/'registration.json')
observed_bytes=(queue/'results.json').read_bytes();import json
observed=json.loads(observed_bytes);names=[n for n in registry['cases'] if n in observed]
assert names and all(observed[n]['passed'] and observed[n]['comparison']['passed'] for n in names)
assert all(sha(f)==h for f,h in registry['source_sha256'].items())
root=a.output.resolve();root.mkdir(exist_ok=False);snapshot=root/'observed_results.json';snapshot.write_bytes(observed_bytes)
files=[Path(__file__).resolve(),snapshot,queue/'registration.json',D/'state_resource_assurance.py',D/'native_resources_from_receipt.py'];results={}
for name in names:
 old=D/'direct_scope_resource_equivalence_recovery_02'/name;new=queue.parent/name
 oa,na=[read(x/'attempts.json') for x in [old,new]];assert len(oa)==len(na)
 for actor in [old,new]:
  closed=read(actor/'completion.json');assert closed['passed']
  assert all(sha(f)==h for f,h in closed['source_sha256'].items())
  files += [actor/'completion.json',actor/'attempts.json',actor/'registration.json']
 old_final,new_final=[Path(read(x/'completion.json')['final_state']) for x in [old,new]]
 final_view=require_publication_proof(new_final);assert final_view.get('publication_independently_validated')
 assert resource_assurance(old_final)['physical_metrics']==read(run_dir(new_final)/'independent_audit.json')['physical_metrics']
 files += [new_final/'final_independent_validation.json',new/'evaluation_context/input_seal.json',run_dir(new_final)/'independent_audit.json']
 legal=other=deferred=0
 for x,y in zip(oa,na):
  assert all(x[k]==y[k] for k in ['round','candidate_rank','bundle_removed_pins']) and x['pair'].keys()==y['pair'].keys()
  txa=old/f"round_{x['round']:03d}"/f"candidate_{x['candidate_rank']:02d}";txb=new/f"round_{y['round']:03d}"/f"candidate_{y['candidate_rank']:02d}"
  for fname in ['request.txt','domain.txt']:
   assert sha(txa/fname)==sha(txb/fname);files += [txa/fname,txb/fname]
  for role in x['pair']:
   aa,bb=x['pair'][role],y['pair'][role]
   assert all(aa.get(k)==bb.get(k) for k in ['status','accepted','CPD_s','resources'])
   if aa['status']!='legal_evaluated':other+=1;continue
   sa,sb=Path(aa['evaluation']),Path(bb['evaluation']);va,vb=read(sa/'endpoint_vector.json'),read(sb/'endpoint_vector.json')
   assert all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
   assert route_body(run_dir(sa)/'routed.route')==route_body(run_dir(sb)/'routed.route')
   ref=resource_assurance(sa);actual=resource_assurance(sb)
   assert ref['independent_physical_audit'] and actual['independent_physical_audit'] is False
   assert actual['resource_axes']==ref['resource_axes']==bb['resources']
   assert all(ref['physical_metrics'][k]==v for k,v in actual['physical_metrics'].items())
   native=read(sb/'completion.json');assert native['publication_requires_final_independent_validation'] is True
   assert native['checks']['native_FULL'] and native['checks']['native_complete']
   deferred+=int(native['independent_physical_audit_deferred']);legal+=1
   assurance_path=Path(actual['evidence']);assurance=read(assurance_path);view=assurance['bound_native_view']
   files += [sa/'endpoint_vector.json',sb/'endpoint_vector.json',sb/'completion.json',run_dir(sa)/'routed.route',run_dir(sb)/'routed.route',Path(ref['evidence']),assurance_path,Path(view['origin_receipt']),Path(view['census_path'])]
 comp=observed[name]['comparison']
 results[name]=dict(passed=True,legal_candidates_exact=legal,native_counters_match_reference_independent_metrics=legal,deferred_candidate_audits=deferred,other_matched_outcomes=other,requests_domains_and_all_policy_outcomes_exact=True,final_independent_and_context_seal_passed=True,reference_direct_imported_seconds=comp['reference_imported_workflow_seconds'],native_census_imported_seconds=comp['direct_imported_workflow_seconds'],observed_seconds_difference=comp['direct_imported_workflow_seconds']-comp['reference_imported_workflow_seconds'])
closed=(queue/'completion.json').exists()
if closed:
 receipt=read(queue/'completion.json');assert receipt['passed'];files.append(queue/'completion.json')
write(root/'completion.json',dict(passed=True,roles=results,completed_roles=len(names),registered_roles=len(registry['cases']),engineering_cohort_terminal=closed,native_calls_new=0,source_sha256={str(f):sha(f) for f in files},qualification='Every legal accepted/rejected candidate in completed roles has exact full endpoint vector, ordered route body, requests/domains, resource axes and policy outcomes versus the direct independently audited trajectory. Every actual native counter field, including crossing-edge-kind histogram, matches that reference. Native assurance remains explicitly native, not an independently executed candidate audit. Only each final selected state has its own final independent verification and sealed context; private intermediates/rejects are not published as independently audited states and their original gates are unchanged. One-time read-only cross-reference verification is separate research cost and makes no new native calls. Imported complete repair workflow costs exclude initial routing and graph construction, are not cold full-flow times, repetitions or statistical speedups. Completed roles are not independent circuit samples.'))
print(dict(passed=True,completed_roles=len(names),roles=results,native_calls_new=0),flush=True)
