#!/usr/bin/env python3
"""Two disclosed clock-only PnR repairs, including fresh placement."""
import concurrent.futures
import json
from lazagna_common import BASE,utc,write_json
from run_lazagna_routes import run_one


def main():
    path=BASE/'repaired_pnr_state.json'
    if path.exists():raise RuntimeError('Repair state exists')
    jobs=[dict(name=f'paper_ideal_pnr_{c}_w300',case=c,family='paper',width=300,arm='primary',state='queued') for c in ['conv_layer','dla_like.small']]
    state=dict(stage='routing',utc=utc(),jobs=jobs)
    write_json(path,state)
    write_json(BASE/'repaired_pnr_protocol.json',dict(utc=utc(),cases=[j['case'] for j in jobs],
        reason='Strict route-clock PnR produced placements with very few annealing temperatures and many aborted moves. Fixed-placement ideal-clock diagnosis cannot exclude this upstream effect.',
        change='Repeat paper-era full pack/place/route/analysis, changing only clock_modeling route to ideal versus each strict primary. Same exact binary, BLIF, architecture, RRG, seed, inner_num and default routing budget.',
        scope='Disclosed clock-model repair, not an unchanged original-parameter reproduction or a matched-placement algorithm comparison.'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending={}
        for j in jobs:
            j['state']='running';pending[pool.submit(run_one,j,None,'ideal')]=j
        write_json(path,state)
        for f in concurrent.futures.as_completed(pending):
            j=pending[f]
            try:j.update(f.result())
            except Exception as e:j.update(state='supervisor_error',error=repr(e))
            write_json(path,state);print(j['name'],j['state'],j.get('native_legal'),flush=True)
    state.update(stage='finished',finished_utc=utc());write_json(path,state)


if __name__=='__main__':main()
