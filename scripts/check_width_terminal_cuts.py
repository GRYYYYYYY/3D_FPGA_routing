#!/usr/bin/env python3
"""Check the observed W120 DLA-medium stall without changing any solver trial.

Terminal demands come from the new graph's one-iteration preparation route, not
from reusing W100 node IDs. The graph was an output of that preparation; the
in-memory source view binds it as the cut checker's graph input. No archived
manifest is modified, and these exploratory checks do not prune the width arm.
"""
import json
from pathlib import Path
import time

from check_route import sha256
from check_terminal_cuts import scan_group
from diagnose_failures import BASE,write_json
from verify_terminal_cuts import verify_one


def main():
    queue=json.loads((BASE/'width_parallel_state.json').read_text())
    case='dla_like.medium';width=120
    job=next(j for j in queue['jobs'] if j['circuit']==case and j['width']==width
             and j['stage'].startswith('prepare_'))
    output=Path(job['output']);manifest_path=output/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['status'] in ['completed','failed'] and manifest['returncode'] in [0,2]
    assert manifest['metrics']['last_iteration']==1
    graph=output/'rr_graph.xml';graph_hash=manifest['outputs']['rr_graph.xml']['sha256']
    assert sha256(graph)==graph_hash
    source_view=json.loads(json.dumps(manifest))
    source_view['inputs']['rr_graph']=dict(path=str(graph),sha256=graph_hash)
    source=dict(circuit=case,original_output=str(output),manifest=source_view)
    path=BASE/'width_terminal_cut_check.json'
    state=dict(started_epoch=time.time(),case=case,width=width,
               preparation_manifest=str(manifest_path),preparation_manifest_sha256=sha256(manifest_path),
               scope='Exploratory necessary-capacity check using fixed terminals from this width; no registered routing trial is omitted')
    write_json(path,state)
    result=scan_group((graph_hash,[source],True,False,True))
    state['scan']=result;write_json(path,state)
    if result['certificates']:state['verification']=verify_one(result['evidence'])
    assert sha256(manifest_path)==state['preparation_manifest_sha256']
    state['finished_epoch']=time.time();write_json(path,state)
    print(json.dumps(dict(case=case,width=width,certificates=result['certificates'],
                         independently_verified=state.get('verification',{}).get('passed',False))),flush=True)


if __name__=='__main__':main()
