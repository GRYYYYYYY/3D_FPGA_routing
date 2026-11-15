"""Read-only physical-input inventory; no new policy outcomes or seed-based independence."""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
root=D/'confirmation_input_inventory_01';root.mkdir(exist_ok=False)
base=D.parents[1]/'results/architecture_flow_20261027/runs'
names=['training_attention_layer_s11_hybrid_o_n60_w100_p0_a0','heldout_clstm_like.small_s21_hybrid_o_n60_w100_p0_a0','heldout_reduction_layer_s21_hybrid_o_n125_w100_p0_a0','heldout_robot_rl_s21_hybrid_o_n60_w100_p0_a0','heldout_robot_rl_s23_hybrid_o_n60_w100_p0_a0','heldout_robot_rl_s21_hybrid_o_n60_w100_p1_a0']
def coordinates(p):
 rows=[]
 for line in p.read_text().splitlines():
  tokens=line.split()
  if len(tokens)>=6 and tokens[-1].startswith('#') and all(x.lstrip('-').isdigit() for x in tokens[1:5]):rows.append((tokens[0],*map(int,tokens[1:5])))
 assert rows and len(rows)==len({r[0] for r in rows})
 return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest(),len(rows)
rows=[];files={};coords={}
for name in names:
 b=base/name;m=read(b/'manifest.json');command=m['command'];circuit=Path(command[2]).stem
 sourcefiles=[b/'manifest.json',b/'packed.net',b/'placed.place',Path(command[2]),Path(command[1])]
 assert all(f.exists() for f in sourcefiles)
 for f in [b/'packed.net',b/'placed.place']:assert sha(f)==m['outputs'][f.name]['sha256']
 digest,n=coordinates(b/'placed.place');coords[name]=digest
 for f in sourcefiles:files[str(f)]=sha(f)
 sdc=command[command.index('--sdc_file')+1] if '--sdc_file' in command else None
 rows.append(dict(name=name,circuit=circuit,source_manifest=str(b/'manifest.json'),packing_sha256=sha(b/'packed.net'),placement_bytes_sha256=sha(b/'placed.place'),placement_coordinates_sha256=digest,placed_blocks=n,netlist_sha256=sha(command[2]),architecture_sha256=sha(command[1]),rr_graph=command[command.index('--read_rr_graph')+1],explicit_sdc=sdc,known_historical_input=True,new_policy_result_observed=False,new_policy_registered=False,role='existing_robot_reference' if name==names[3] else 'candidate_input'))
robot=rows[3:];comparison=dict(s21_p0_vs_s23_p0=dict(same_packing=robot[0]['packing_sha256']==robot[1]['packing_sha256'],same_placement_coordinates=robot[0]['placement_coordinates_sha256']==robot[1]['placement_coordinates_sha256']),s21_p0_vs_p1=dict(same_packing=robot[0]['packing_sha256']==robot[2]['packing_sha256'],same_placement_coordinates=robot[0]['placement_coordinates_sha256']==robot[2]['placement_coordinates_sha256']))
assert comparison['s21_p0_vs_s23_p0']==dict(same_packing=True,same_placement_coordinates=False)
write(root/'inputs.json',rows)
write(root/'completion.json',dict(passed=True,candidate_records=len(rows)-1,existing_reference_records=1,circuit_identities=len({r['netlist_sha256'] for r in rows}),distinct_placement_coordinate_sets=len(set(coords.values())),robot_comparison=comparison,explicit_SDC_instances=sum(r['explicit_sdc'] is not None for r in rows),source_sha256=files,artifact_sha256={'inputs.json':sha(root/'inputs.json')},native_calls_new=0,qualification='Inventory of historical physical inputs, selected by circuit/placement identity before any new unified-policy execution. Names training/heldout are historical labels, not new unseen-test claims. Actual block-name/coordinate records are normalized without headers or block numbering. Robot seed23 here changes placement coordinates with identical packing, unlike route-only seed repeats. p1 also changes packing and must not be called a placement-only control. RRG byte binding, current applicability, fresh route identities and explicit SDC remain required before confirmation registration. No new quality evidence yet.'))
print(dict(passed=True,inputs=len(rows),robot_comparison=comparison,explicit_SDC_instances=sum(r['explicit_sdc'] is not None for r in rows)))
