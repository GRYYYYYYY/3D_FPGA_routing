#!/usr/bin/env python3
"""Bounded metadata-reader profiling; no graph outputs or algorithm changes."""
import argparse
from collections import Counter
import gc
import hashlib
import resource
import time

import derive_flatland_common_plane as reader
from compare_lazagna_graphs import records
from lazagna_common import ROOT,utc,write_json


def main(limit,disabled):
    source=ROOT/'results/architecture_flow_20261027/runs/controlled_graph_sb_n200_w100_ideal/rr_graph.xml'
    output=ROOT/'results/architecture_flow_20261027'/f'metadata_profile_{limit}_{"no_gc" if disabled else "gc"}.json'
    if output.exists():raise FileExistsError(output)
    count=0;stats=Counter();starts={}
    def limited(path):
        nonlocal count
        for section,e in records(path):
            if section=='rr_nodes':
                if count==limit:break
                count+=1
            yield section,e
    def callback(phase,info):
        generation=info['generation']
        if phase=='start':starts[generation]=time.perf_counter()
        else:
            stats[f'generation{generation}_seconds']+=time.perf_counter()-starts[generation]
            stats[f'generation{generation}_collections']+=1
    reader.records=limited;gc.collect();gc.callbacks.append(callback)
    if disabled:gc.disable()
    start=time.perf_counter();data=reader.metadata(source);seconds=time.perf_counter()-start
    gc.callbacks.remove(callback)
    digest=hashlib.sha256()
    for key in data['keys']:digest.update(repr(key).encode());digest.update(b'\n')
    digest.update(data['layers'].tobytes());digest.update(repr(sorted(data['switches'].items())).encode())
    result=dict(utc=utc(),source=str(source),node_limit=limit,nodes=count,gc_disabled=disabled,
        elapsed_seconds=seconds,gc=dict(stats),metadata_digest=digest.hexdigest(),
        ordinary_nodes=len(data['ordinary']),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        purpose='Metadata construction overhead only; unrelated to VPR algorithm runtime or QoR')
    write_json(output,result);print(result,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--nodes',type=int,default=600000)
    p.add_argument('--disable-gc',action='store_true');a=p.parse_args();main(a.nodes,a.disable_gc)
