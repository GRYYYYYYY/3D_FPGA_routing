#!/usr/bin/env python3
"""Resume completed graph generation without changing model or audit semantics.

An interrupted model directory must first be archived by its owner. Existing
raw graphs and any completed common-plane derivation are verified and reused.
"""
import argparse
import gc
from itertools import zip_longest
import json
from pathlib import Path
import shutil

from audit_flatland_controlled_planes import load
from audit_flatland_graphs import audit
from derive_flatland_common_plane import derive
from flatland_formats import prepare_import
from lazagna_common import ROOT,sha256,utc,write_json
from prepare_flatland_benchmark_models import BASE,capacities
from validate_flatland_common_plane import nonplanar_records,resources
from verify_flatland_import_stream import verify as verify_import


def read(path):return json.loads(Path(path).read_text())


def main(size,width,output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    paths={f:BASE/'runs'/f'controlled_graph_{f}_n{size}_w{width}_ideal'/'rr_graph.xml'
           for f in ['sb','cb_o','hybrid_o','matched_2d']}
    bindings={}
    for f,path in paths.items():
        receipt=read(path.parent/'manifest.json');assert receipt['status']=='completed'
        assert receipt['command'][receipt['command'].index('--write_rr_graph')+1]==str(path)
        # The graph-generation runner predates output hashes. Bind the current
        # complete file here; completed derivation hashes are checked below.
        digest=sha256(path)
        bindings[str(path)]=digest
    source_names=['resume_flatland_model_audits.py','prepare_flatland_benchmark_models.py',
        'derive_flatland_common_plane.py','audit_flatland_controlled_planes.py','audit_flatland_graphs.py',
        'validate_flatland_common_plane.py','verify_flatland_import_stream.py','flatland_formats.py','compare_lazagna_graphs.py']
    sources={}
    for name in source_names:
        path=ROOT/'scripts'/name;sources[str(path)]=sha256(path);shutil.copy2(path,output/name)
    write_json(output/'registration.json',dict(utc=utc(),size=size,width=width,sources=sources,
        protocol_sha256=sha256(BASE/'benchmark_protocol.json'),source_graphs=bindings,
        method='Resume from completed and hashed raw graphs; reuse complete derivation or call the unchanged derivation; repeat every original physical/topology/import audit with cyclic GC disabled.',
        graph_generation_repeated=False))
    gc.collect();gc.disable()
    try:
        derived=BASE/'common_plane_models/v2'/f'n{size}_w{width}'/'manifest.json'
        if not derived.exists():derive(size,width)
        data=read(derived)
        assert data['source_graphs']=={str(paths[f]):bindings[str(paths[f])] for f in ['sb','cb_o','hybrid_o']}
        models=data['models']
        for model in models.values():assert sha256(model['graph'])==model['sha256']
        reference=load(models['sb']['graph']);fixtures={};resource_rows={}
        archdir=BASE/'controlled_architectures'/f'n{size}';match=read(archdir/'matched_2d_manifest.json')
        for family in ['sb','cb_o','hybrid_o','matched_2d']:
            original=paths[family];graph=Path(models[family]['graph']) if family!='matched_2d' else original
            if family in ('cb_o','hybrid_o'):
                other=load(graph,reference['identities'])
                assert other['keys']==reference['keys'] and other['edges']==reference['edges'];del other
                for a,b in zip_longest(nonplanar_records(original),nonplanar_records(graph)):
                    assert a==b,f'{family}: nonplanar data changed'
            architecture=archdir/f'{family}.xml';row=audit(graph,architecture)
            slots=row['total_slots'];logical={k:slots[k] for k in ['clb','complex_dsp','spram']}
            logical['io']=slots['io']+slots.get('io_double',0)
            assert logical==capacities(size)
            assert row['unpaired_sb_nodes']==0 and row['nonzero_node_RC_count']==0
            row['logical_slots']=logical;row['wire_resources']=resources(graph)
            write_json(output/f'{family}_physical_audit.json',row);resource_rows[family]=row
            side=match['grid'][0] if family=='matched_2d' else size
            converted=prepare_import(graph,architecture,output/family,width=side,height=side)
            schema_check=verify_import(graph,converted['graph'],converted['unused_segment_id'])
            fixtures[family]=dict(original_graph=str(graph),architecture=str(architecture),conversion=converted,
                native_schema_check=schema_check,physical_audit=str(output/f'{family}_physical_audit.json'))
            write_json(output/'progress.json',dict(utc=utc(),status='auditing',ready_families=list(fixtures)))
            print('resumed model ready',size,width,family,flush=True)
        assert resource_rows['sb']['sb_pair_count']==resource_rows['hybrid_o']['sb_pair_count']
        assert resource_rows['cb_o']['cb_crossing_source_rr_nodes']==resource_rows['hybrid_o']['cb_crossing_source_rr_nodes']
        write_json(output/'manifest.json',dict(utc=utc(),status='ready',size=size,width=width,fixtures=fixtures,
            logical_slots=capacities(size),same_plane_exact=True,
            planar_wire_2d_over_3d=resource_rows['matched_2d']['wire_resources']['total_planar_wire_unit_capacity']/resource_rows['sb']['wire_resources']['total_planar_wire_unit_capacity'],
            limitation='Exact logical capacities and common 3D plane; 2D boundary/I/O/wire inventory differs. Hybrid has additional connectivity, not demonstrated equal physical area.',
            preparation_registration=str(output/'registration.json')))
    except Exception as error:
        write_json(output/'failure.json',dict(utc=utc(),error=str(error)));raise
    finally:gc.enable()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--size',type=int,required=True);p.add_argument('--width',type=int,default=100)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.size,a.width,a.output)
