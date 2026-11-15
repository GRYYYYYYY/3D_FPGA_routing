"""Count actual modern complete-flow finals from proofs, not inherited scalar increments."""
import collections,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent=D/'multiobjective_joint_index_closed_01';out=D/'multiobjective_engineering_inventory_01'
assert not out.exists();pc=read(parent/'completion.json');assert pc['passed']
assert read(parent/'verification.json')['passed']
assert all(sha(parent/f)==h for f,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');rows=[];sources=[Path(__file__).resolve(),parent/'completion.json',parent/'verification.json',parent/'points.json']
for p in points:
    if p.get('record_kind') not in ['complete_measured_algorithm_final','measured_whole_configuration_final']:continue
    root=Path(p['batch_full_path']);proof=Path(p.get('measurement_proof',p.get('complete_configuration_verification',str(root/'completion.json'))))
    c=read(proof);measurement=root/'measurement/completion.json';m=read(measurement);config=root/'config.json';cfg=read(config)
    assert c['passed'] and c['complete_configuration_verified'] and m['passed']
    assert p['actor_final_selected'] and p['state']==c['final_state']
    assert p['CPD_ns']==c['CPD_ns'] and {k:p[k] for k in ['wirelength','SB_pairs','CB_sources']}==c['resources']
    assert p['complete_single_configuration_seconds']==c['complete_wall_seconds']==m['complete_command_wall_seconds']
    memory=p.get('measured_memory',p.get('memory_observation'));assert memory
    assert all(value==c[key]==m[key] for key,value in memory.items())
    rows.append(dict(id=p['id'],case=str(root),circuit=p['circuit'],cache_mode=cfg['cache_mode'],
        state=p['state'],quality=dict(CPD_ns=p['CPD_ns'],**c['resources']),complete_seconds=c['complete_wall_seconds'],
        proof=str(proof),measurement=str(measurement),memory=memory))
    sources.extend([proof,measurement,config])
assert len(rows)==len({r['case'] for r in rows})==33
assert len({r['circuit'] for r in rows})==5
byid={r['id']:r for r in rows};history=[]
for name in ['multiobjective_closed_R1_native_01','multiobjective_connection_budget_closed_01','multiobjective_lazy_snapshot_closed_01','multiobjective_joint_index_closed_01']:
    root=D/name;c=read(root/'completion.json');old=read(root/'points.json')
    ids={p['id'] for p in old if p.get('record_kind') in ['complete_measured_algorithm_final','measured_whole_configuration_final']}
    assert ids<=byid.keys()
    history.append(dict(archive=name,records=len(old),inherited_scalar=c['complete_measured_configurations_total'],
        enumerated_complete_configs=len(ids),difference=len(ids)-c['complete_measured_configurations_total']))
    sources += [root/'completion.json',root/'points.json']
assert all(h['difference']==4 for h in history)
out.mkdir()
for name in ['points.json','points.csv']:shutil.copy2(parent/name,out/name);assert sha(parent/name)==sha(out/name)
write(out/'complete_configuration_inventory.json',dict(passed=True,scope='Modern fresh-route-plus-complete-repair final records only; excludes historical initial-route timing cohorts and imported-only repair observations.',
    configurations=rows,count=33,cache_modes=dict(collections.Counter(r['cache_mode'] for r in rows)),
    circuits=sorted({r['circuit'] for r in rows}),historical_scalar_reconciliation=history,
    qualification='Counts independently enumerated actual case/measurement proofs. Four-count inherited undercount affects named modern configuration totals, not point cardinality or individual quality/time/memory. Historical scalar values preserved in parent artifacts; no inferred exclusion criterion or independent-sample claim. C223uses640-record archive and must say30modern configurations rather than26; current658-record archive has33.'))
write(out/'completion.json',dict(passed=True,parent=str(parent),records=len(points),added=[],native_calls=0,
    complete_measured_configurations_total=33,complete_known_circuits=5,complete_vertical_families=pc['complete_vertical_families'],
    inherited_count_corrected_from=pc['complete_measured_configurations_total'],
    source_sha256={str(f):sha(f) for f in dict.fromkeys(sources)},
    artifact_sha256={f:sha(out/f) for f in ['points.json','points.csv','complete_configuration_inventory.json']}))
write(out/'verification.json',dict(passed=True,records=len(points),added=0,parent_points_byte_exact=True,
    complete_case_identities_unique=True,actual_final_quality_time_memory_match_primary_proofs=True,
    complete_measured_configurations_total=33,complete_known_circuits=5,historical_undercount=4,
    paper_C223_count_correction_required=dict(old=26,new=30),native_calls_new=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),out/'completion.json',out/'complete_configuration_inventory.json']}))
print(dict(passed=True,records=len(points),complete_configurations=33,known_circuits=5,history=history),flush=True)
