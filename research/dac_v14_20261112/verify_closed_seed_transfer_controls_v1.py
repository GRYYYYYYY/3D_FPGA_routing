"""Verify closure and actual own-current native/domain controls for all eight original roles."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from state_resource_assurance import require_publication_proof

out=D/'closed_seed_transfer_eight_roles_01.json';assert not out.exists()
roots=[('eltwise_A0','stable_seed_transfer_dev_01/eltwise_A0_native','stable_seed_transfer_dev_01/eltwise_A0_paired',None),('bnn_A0','stable_seed_transfer_dev_01/bnn_A0_native','stable_seed_transfer_dev_01/bnn_A0_paired',None),('bnn_R1','native_checkpoint_recovery_03/bnn_R1_native','stable_seed_transfer_recovery_01/bnn_R1_paired','stable_seed_transfer_dev_01/bnn_R1_native'),('bnn_Tf','native_checkpoint_recovery_02/bnn_Tf_native','stable_seed_transfer_recovery_02/bnn_Tf_paired','stable_seed_transfer_recovery_01/bnn_Tf_native')]
files=[Path(__file__).resolve()];results={}
for label,nn,pn,original in roots:
 n,p=[D/x for x in [nn,pn]];nr,pr=[read(x/'registration.json') for x in [D/original if original else n,p]]
 matched={k:nr[k]==pr[k] for k in ['initial_state','bundle_size','seed_order','graph_echo','local_probe','anchor','full_graph_cache']};assert all(matched.values())
 assert nr['domain_mode']=='unrestricted' and pr['domain_mode']=='paired'
 role_results=[]
 for actor in [n,p]:
  c=read(actor/'completion.json');assert c['passed'] and c['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
  assert c['initial_state']==nr['initial_state']
  assert all(sha(f)==h for f,h in c['source_sha256'].items())
  final=Path(c['final_state']);assert require_publication_proof(final)['passed']
  pool=read(actor/'pool/completion.json');seal=read(actor/'evaluation_context/input_seal.json');assert pool['passed'] and seal['passed']
  assert all(sha(f)==h for f,h in pool['source_sha256'].items()) and all(sha(f)==h for f,h in seal['source_sha256'].items())
  role_results.append(dict(actor=str(actor),final_state=c['final_state'],accepted_steps=c['accepted_steps'],attempted_scopes=c['attempted_scopes'],CPD_s=c['final_CPD_s'],resources=c['final_resources'],whole_configuration_seconds=None,recovery_segment_seconds=c.get('complete_recovery_segment_seconds'),historical_imported_workflow_seconds=c.get('complete_imported_algorithm_workflow_seconds')))
  files += [actor/'registration.json',actor/'completion.json',actor/'pool/completion.json',actor/'evaluation_context/input_seal.json',final/'completion.json',final/'endpoint_vector.json']
 a,b=role_results;delta={k:b['resources'][k]-a['resources'][k] for k in a['resources']}
 endpoints=compare(read(Path(a['final_state'])/'endpoint_vector.json'),read(Path(b['final_state'])/'endpoint_vector.json'))
 results[label]=dict(matched_original_fields=matched,native=a,paired=b,paired_minus_native_resources=delta,endpoint_comparison=endpoints,complete_cost_comparison_available=False)
 if original:files.append(D/original/'registration.json')
assert results['bnn_R1']['paired_minus_native_resources']==dict(wirelength=1673,SB_pairs=-38,CB_sources=-1)
assert results['bnn_Tf']['paired_minus_native_resources']==dict(wirelength=1650,SB_pairs=-31,CB_sources=-2)
write(out,dict(passed=True,registered_roles=8,successfully_closed_menus=8,matched_own_current_pairs=results,native_calls_new=0,source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},qualification='All eight original root/control roles close the declared own-current native/domain rank windows. Each branch recomputes current selection after its own commits; source parameters/root/anchor/seed/K8/rank match per pair. Later owner-release five-connection intervention is a separate opportunity, never substituted into these trajectory endpoints. These are development roots on two known circuits, not eight independent benchmark samples. Recovery times are partial segments; no historical whole cost or paired speedup reconstructed. Legal candidates/rejects retain their existing observation identities and no new archive record is implied by this summary.'))
print(dict(passed=True,closed=8,registered=8,R1_paired_minus_native=results['bnn_R1']['paired_minus_native_resources'],Tf_paired_minus_native=results['bnn_Tf']['paired_minus_native_resources'],native_calls_new=0),flush=True)
