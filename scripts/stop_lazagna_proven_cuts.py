#!/usr/bin/env python3
"""Stop only ongoing W100 jobs whose exact fixed-input cut is verified."""
import json
import os
import signal
import time
from pathlib import Path
from lazagna_common import BASE,sha256,utc,write_json


def main():
    for family in ['paper','native']:
        proof=BASE/f'dsp_cuts_{family}_w100.verified.json'
        while not proof.exists():time.sleep(5)
        verified=json.loads(proof.read_text());assert verified['passed'] and verified['complete_graph_scan']
        cuts=json.loads((BASE/f'dsp_cuts_{family}_w100.json').read_text())
        assert sha256(BASE/f'dsp_cuts_{family}_w100.json')==verified['input_sha256']
        for case in ['attention_layer','conv_layer','dla_like.small']:
            c=next(x for x in cuts['certificates'] if x['case']==case)
            name=f"{family}_ideal_{'compat_' if family=='native' else ''}{case}_w100_i200"
            d=BASE/'runs'/name;receipt=d/'manifest.json'
            while not receipt.exists():time.sleep(2)
            m=json.loads(receipt.read_text())
            if m['status']!='running':continue
            assert m['inputs'][str(Path(cuts['graph']).resolve())]==cuts['graph_sha256']
            assert m['inputs'][c['packed_netlist']]==c['packed_sha256']
            assert m['inputs'][c['placement']]==c['placement_sha256']
            try:
                stat=Path(f"/proc/{m['pid']}/stat").read_text().split(')')[1].split()[0]
                if stat=='Z':continue
                os.killpg(m['pid'],0)
            except (FileNotFoundError,ProcessLookupError):continue
            write_json(d/'capacity_proof_cancel.json',{'utc':utc(),'classification':'cancelled_proven_dsp_capacity_cut',
                'reason':'Exact fixed-input DSP cut proves infeasibility regardless of additional negotiation iterations.',
                'verification':str(proof),'verification_sha256':sha256(proof),'demand':c['demand'],'capacity':c['capacity'],
                'coordinate':c['coordinate'],'pid':m['pid'],'signal':'SIGTERM'})
            try:os.killpg(m['pid'],signal.SIGTERM)
            except ProcessLookupError:pass
            print(name,'stopped with verified cut',c['demand'],c['capacity'],flush=True)


if __name__=='__main__':main()
