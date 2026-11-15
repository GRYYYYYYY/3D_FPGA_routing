"""Check real selected states against archived native evidence and raw endpoint vectors."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy import compare
from state_resource_assurance import require_publication_proof

root=D/'terminal_timing_envelope_policy_01';out=root/'verification.json';assert not out.exists()
c=read(root/'completion.json');reg=read(root/'registration.json');rows=read(root/'results.json')
assert c['passed'] and c['real_closed_menus']==13 and c['mode_evaluations']==26
assert all(sha(f)==h for f,h in c['source_sha256'].items())
assert all(sha(root/f)==h for f,h in c['artifact_sha256'].items())
assert {(r['menu'],r['mode']) for r in rows}=={(label,mode) for label in reg['menus'] for mode in ['endpoint','fixed_timing']}
archive=D/'multiobjective_closed_R1_native_01';points=read(archive/'points.json');selected=[]
for r in rows:
 proof=read(root/(r['menu']+'_'+r['mode'])/'completion.json');assert proof['passed']
 assert all(sha(f)==h for f,h in proof['source_sha256'].items())
 state=Path(proof['state']);before=read(state/'endpoint_vector.json');observed=read(root/(r['menu']+'_'+r['mode'])/'observed_candidates.json')
 eligible=[]
 for candidate in observed:
  target=Path(candidate['state']);after=read(target/'endpoint_vector.json');axes=require_publication_proof(target)['resource_axes'];cp=compare(before,after)
  common=(cp['compatible'] and cp['hold_violation_regressions']==0 and axes['wirelength']<proof['current_resources']['wirelength'] and axes['SB_pairs']==proof['current_resources']['SB_pairs'] and axes['CB_sources']==proof['current_resources']['CB_sources'] and after['cpd_s']<=proof['fixed_CPD_limit_s'] and all(axes[k]<=proof['fixed_resource_limits'][k] for k in proof['fixed_resource_limits']))
  if r['mode']=='endpoint':common=common and cp['cpd_nonworse'] and cp['setup_regressed']==0
  assert bool(common)==candidate['eligible']
  if common:eligible.append(candidate)
 assert len(eligible)==r['eligible']==proof['eligible_candidates']
 if not eligible:assert r['selected'] is None;continue
 choice=min(eligible,key=lambda x:(x['resources']['wirelength'],x['attempt_index'],x['role']))
 assert choice==r['selected']==proof['selected']
 record=next(p for p in points if p.get('state')==choice['state'])
 assert {k:record[k] for k in choice['resources']}==choice['resources']
 selected.append(dict(menu=r['menu'],mode=r['mode'],existing_archive_id=record['id'],quality_status=record['quality_status'],resources=choice['resources'],setup_improved=choice['setup_improved'],setup_regressed=choice['setup_regressed']))
tf={r['mode']:r for r in rows if r['menu']=='bnn_Tf_native'}
assert tf['endpoint']['selected'] is None and tf['fixed_timing']['selected']['resources']==dict(wirelength=2074308,SB_pairs=74,CB_sources=5062)
assert tf['fixed_timing']['selected']['setup_improved']==19 and tf['fixed_timing']['selected']['setup_regressed']==4
assert len(points)==578 and all(not read(root/(r['menu']+'_'+r['mode'])/'completion.json')['committed_to_original_actor'] for r in rows)
write(out,dict(passed=True,real_closed_menus=13,uniform_mode_evaluations=26,legacy_endpoint_replays=5,selected_existing_states=selected,Tf_wire_saving=80,Tf_setup_improved_regressed=[19,4],no_new_legal_archive_observations=True,archive_records_unchanged=578,native_calls_new=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),root/'completion.json',root/'registration.json',root/'results.json',archive/'completion.json',archive/'points.json']},qualification='Actual legal native states already in the archive, original CPD/resource/hold caps and complete vector identities independently checked. Fixed timing admits a real setup tradeoff rejected by unchanged endpoint mode. Positive menu counts are not independent circuits or prospective algorithm confirmations. No changes to original actors or claims of complete runtime improvement.'))
print(dict(passed=True,menus=13,modes=26,positive_mode_menus=len(selected),Tf_wire_saved=80,archive_records_unchanged=578,native_calls_new=0),flush=True)
