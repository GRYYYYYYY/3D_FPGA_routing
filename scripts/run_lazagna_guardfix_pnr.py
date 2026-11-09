#!/usr/bin/env python3
"""Disclosed minimal placement-guard correction controls, not original runs."""
import concurrent.futures
import time
from lazagna_common import BASE,ROOT,utc,write_json
from run_lazagna_routes import run_one


def main():
    path=BASE/'guardfix_pnr_state.json'
    if path.exists():raise RuntimeError('Guardfix control state exists')
    jobs=[]
    for case,clock in [('bnn','route'),('conv_layer','ideal'),('dla_like.small','ideal')]:
        jobs.append(dict(name=f'paper_guardfix_{clock}_pnr_{case}_w300',case=case,family='paper',width=300,arm='primary',clock_model=clock,state='queued'))
    state=dict(stage='waiting_build',utc=utc(),jobs=jobs);write_json(path,state)
    write_json(BASE/'guardfix_pnr_protocol.json',dict(utc=utc(),reason='Historical VTR commit af5b6a4434 replaces valid-coordinate assertions with inverted !=OPEN rejection guards in two placement search-range functions.',
        patch='Only those two if guards are corrected to ==OPEN in a separately linked one-object build. Original sources and binaries retained unchanged.',
        controls={'bnn':'Identical to strict original primary, including clock_modeling=route; only placement guard code changes.',
                  'conv_layer,dla_like.small':'Identical to clock-only repaired full PnR, including clock_modeling=ideal; only placement guard code changes.'},
        scope='Causal software-defect controls on the same source revision, not a claim that the authors paper used the defective public snapshot or that every previous native-VTR failure was a tool bug.'))
    binary=ROOT/'artifacts/bin/lazagna-guardfix/vpr'
    while not (binary.parent/'manifest.json').exists():time.sleep(2)
    state['stage']='routing'
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending={}
        for j in jobs:
            j['state']='running';pending[pool.submit(run_one,j,None,j['clock_model'],False,binary)]=j
        write_json(path,state)
        for f in concurrent.futures.as_completed(pending):
            j=pending[f]
            try:j.update(f.result())
            except Exception as e:j.update(state='supervisor_error',error=repr(e))
            write_json(path,state);print(j['name'],j['state'],j.get('native_legal'),flush=True)
    state.update(stage='finished',finished_utc=utc());write_json(path,state)


if __name__=='__main__':main()
