"""Bounded coordinate comparison; do not mistake names/header bytes for new starts."""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'cp1r3_distinct_input_cohort_01';protocol=read(root/'protocol.json');matrix_path=D/'mechanism_selection_evidence_01/pairs.json'
reference=next(r for r in read(matrix_path) if r['label']=='Eltwise SB')
selected=next(r for r in protocol['selected_inputs'] if r['id']=='eltwise_sb')
old_initial=Path(reference['native']['actor']).parent/'initial';old_run=Path(read(old_initial/'completion.json')['run'])
old_place=old_run/'placed.place';new_place=Path(selected['copies']['placement']['source'])
def coordinates(path):
    result={}
    for line in path.read_text().splitlines():
        row=line.split()
        if len(row)>=5 and all(x.lstrip('-').isdigit() for x in row[1:5]):
            assert row[0] not in result;result[row[0]]=list(map(int,row[1:5]))
    assert result;return result
old,new=coordinates(old_place),coordinates(new_place);assert old.keys()==new.keys()
changed=sum(old[name]!=new[name] for name in old);assert changed>0
for name in ['circuit','architecture','graph','packed']:
    assert selected['declared_physical_identity'][name+'_sha256']==reference['native']['declared_physical_identity'][name]
assert sha(old_place)==reference['native']['declared_physical_identity']['placement']
assert sha(new_place)==selected['declared_physical_identity']['placement_sha256']
normalized=lambda rows:hashlib.sha256(json.dumps([[name,*rows[name]] for name in sorted(rows)],separators=(',',':')).encode()).hexdigest()
target=root/'placement_independence_01.json';assert not target.exists()
write(target,dict(passed=True,control='eltwise_sb',same_declared_circuit_architecture_graph_and_packing=True,
    same_block_names=True,placed_blocks=len(old),blocks_with_changed_coordinates=changed,
    original_normalized_coordinates_sha256=normalized(old),selected_normalized_coordinates_sha256=normalized(new),
    actual_different_placement_not_just_header_or_seed=True,new_circuit_identity=False,
    new_native_calls=0,new_full_method_results=0,large_graph_or_packing_rehashes=0,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'protocol.json',matrix_path,old_initial/'completion.json',old_place,new_place]},
    qualification='Actual block-name/x/y/subblock/layer records compared on two bounded128KBplacement files; header pathnames and block numbering excluded. Candidate is a new actual placement relative to the older SB-only table input, with the same declared graph/packing. This is not a new circuit or new routing result, nor isolated architecture causality. Fresh roots and full byte admission remain required.'))
print(dict(passed=True,placed_blocks=len(old),changed_coordinates=changed,new_native_calls=0))
