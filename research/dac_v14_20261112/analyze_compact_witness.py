#!/usr/bin/env python3
"""Exact compact/full cache equivalence, strict certificate reuse and unified costs."""
import argparse,collections,math,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from compact_witness_records import records
from verify_path_witnesses_v2 import fields
from analyze_native_reconvergence_v2 import observe

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch',type=Path);args=ap.parse_args();b=args.batch.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3));signal.alarm(300)
    done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms'];assert read(b/'input_seal.json')['passed']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['C0','C1']};lines={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()}
    same_records=records(lines['C0'])==records(lines['C1']);assert same_records
    prefix=lambda ls:[l for l in ls if l.startswith('H3D_PREFIX_')]
    assert prefix(lines['C0'])==prefix(lines['C1'])
    assert route_body(dirs['C0']/'routed.route')==route_body(dirs['C1']/'routed.route')
    assert sha(dirs['C0']/'h3d_final_guides.csv')==sha(dirs['C1']/'h3d_final_guides.csv')
    previous=D/'candidate_path_cached_eltwise_dev_01';physics=previous/'cached_score_analysis.json';assert read(physics)['passed']
    previous_lines=(previous/'runs/eltwise_layer_K1/stdout.log').read_text().splitlines()
    assert records(previous_lines)==records(lines['C0']) and prefix(previous_lines)==prefix(lines['C0'])
    full=fields(next(l for l in reversed(lines['C0']) if l.startswith('H3D_CANDIDATE_PATH_CAPTURE ')))
    compact=fields(next(l for l in reversed(lines['C1']) if l.startswith('H3D_CANDIDATE_PATH_CAPTURE ')))
    counts=fields(next(l for l in reversed(lines['C1']) if l.startswith('H3D_CANDIDATE_PATH_COMPACT ')))
    assert int(counts['full_records'])==int(full['records']) and int(counts['compact_records'])==int(compact['records'])<=int(full['records'])
    for field in ['record_limit','skipped_queries','forward_endpoints','reverse_endpoints']:assert full[field]==compact[field]
    assert int(full['skipped_queries'])==0
    paths=lambda ls:[l for l in ls if l.startswith(('H3D_CANDIDATE_PATH ','H3D_PATH_PRICE_CACHE_OBSERVATION '))]
    assert paths(previous_lines)==paths(lines['C0'])==paths(lines['C1'])
    m=read(dirs['C1']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);graph_hash=sha(graph)
    assert any(Path(p).resolve()==graph.resolve() and h==graph_hash for p,h in read(physics)['source_sha256'].items())
    inputs=[Path(__file__),D/'compact_witness_records.py',D/'compact_witness_unit_01/validation.json',physics,b/'registration.json',b/'input_seal.json',b/'completion.json',previous/'runs/eltwise_layer_K1/stdout.log']
    inputs += [p/n for p in dirs.values() for n in ['stdout.log','manifest.json','independent_audit.json','final_guide_audit.json']]
    rows=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()]
    rows += [dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    result=dict(status='sealed_compact_cache_exact_equivalence',passed=True,observations=rows,full_cache_records=int(full['records']),compact_cache_records=int(compact['records']),cache_record_reduction_pct=(1-int(compact['records'])/int(full['records']))*100,
        same_non_time_records=True,same_all_prefix_records=True,same_all_query_cache_paths=True,same_complete_route=True,same_final_guides=True,cache_skips=0,
        physics_and_objective_reuse=dict(source=str(physics),sha256=sha(physics),graph_sha256=graph_hash,criterion='Every raw query/path/snapshot and scored/fingerprint/decision record, all prefix tables and exact same RRG hash. Never inferred from matching CPD.'),
        source_sha256={str(p):sha(p) for p in inputs},qualification='One seen native case. Random graph exact-path/minimal-ancestor union tests and complete native equivalence pass. Record count reduction is measured; allocator/RSS/full-process speedup requires same-environment formal timing and is not implied. No QoR improvement claim.')
    write(b/'compact_analysis.json',result);print({k:v for k,v in result.items() if k not in ['observations','source_sha256','physics_and_objective_reuse','qualification']})

if __name__=='__main__':main()
