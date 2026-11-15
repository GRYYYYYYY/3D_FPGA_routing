"""Generate proposals from hash-bound physical/STA inputs, with no native calls."""
import argparse
import json
import math
import resource
import time
from pathlib import Path
from retained_prefix_workflow import read, write, sha
from full_route_graph_cache import FullRouteGraphCache
from endpoint_timing_policy_streaming_v2 import load
from current_sta_selector import select as sta_select
from selection_kernels import crossing_scopes, owner_scopes


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();start=time.monotonic()
    package=Path(__file__).resolve().parent
    sealed=read(package/'artifact_manifest.json')
    assert all(sha(package/n)==h for n,h in sealed['sha256'].items()),'Package changed'
    spec=read(a.inputs);assert spec['format']=='explicit_selection_observation_v1'
    assert set(spec['files'])=={'route','trace','constraints','vector','audit','graph'}
    paths={}
    bound={str(a.inputs.resolve()):sha(a.inputs)}
    for key,row in spec['files'].items():
        path=(a.inputs.resolve().parent/row['path']).resolve()
        assert sha(path)==row['sha256'],('Observation input changed',key)
        paths[key]=path;bound[str(path)]=row['sha256']
    run=paths['route'].parent
    assert paths['route'].name=='routed.route' and paths['trace']==run/'native_sta_frontier.jsonl'
    assert paths['constraints']==run/'native_sta_frontier.jsonl.constraints.echo'
    vector=read(paths['vector'])
    assert json.loads(json.dumps(load(paths['trace'])))==vector,'Vector/actual STA mismatch'
    audit=read(paths['audit']);assert audit['audit']['passed']
    margin=spec['minimum_margin_ns'];near=spec['near_ns']
    assert isinstance(margin,(int,float)) and math.isfinite(margin) and margin>=0
    assert isinstance(near,(int,float)) and math.isfinite(near) and near>=0
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
    directory=(a.inputs.resolve().parent/spec['cache']['path']).resolve()
    assert sha(directory/'completion.json')==spec['cache']['completion_sha256']
    cache=FullRouteGraphCache(paths['graph'],directory)
    for directory in [cache.directory,cache.g.directory]:
        for name in ['completion.json',*read(directory/'completion.json')['payload_sha256']]:
            bound[str(directory/name)]=sha(directory/name)
    out=a.output.resolve();out.mkdir(exist_ok=False)
    critical=sta_select(paths['trace'],near_ns=near)
    crossing=crossing_scopes(run,vector,cache,minimum_margin_s=margin*1e-9)
    assert all(audit['physical_metrics'][k]==v for k,v in crossing['actual_resources'].items()),'Route/resource census mismatch'
    owner=owner_scopes(run,vector,cache,minimum_margin_ns=margin)
    write(out/'sta.json',critical);write(out/'crossing.json',crossing);write(out/'owner.json',owner)
    assert all(sha(f)==h for f,h in bound.items()),'Input changed during selection'
    write(out/'completion.json',dict(passed=True,native_calls_new=0,route_searches_new=0,
        selected_STA_connections=len(critical['targets']),crossing_scopes=len(crossing['candidates']),
        owner_groups=len(owner['groups']),complete_selection_seconds=time.monotonic()-start,
        source_sha256=bound,package_manifest_sha256=sha(package/'artifact_manifest.json'),
        artifact_sha256={n:sha(out/n) for n in ['sta.json','crossing.json','owner.json']},
        full_method_frozen=False,native_feasibility_established=False,accepted=None,
        qualification='Explicit supplied observation, exact current STA parsing, cache/route census and original selection kernels. Proposals only: this entry does not establish native route legality, replacement feasibility, acceptance, or algorithm benefit. Caller must independently admit native FULL and physical proof before executing a transaction.'))

if __name__=='__main__':main()
