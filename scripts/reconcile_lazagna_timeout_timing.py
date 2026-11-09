#!/usr/bin/env python3
"""Annotate adopted timeout timing without modifying original run receipts."""
import datetime as dt
import json
from lazagna_common import BASE, sha256, utc, write_json


def main():
    for receipt in sorted((BASE/'runs').glob('native_ideal_compat*/manifest.json')):
        m=json.loads(receipt.read_text());directory=receipt.parent
        if not (m.get('supervisor_adopted') and m['status']=='timeout'):continue
        if m['wall_seconds']>=m['timeout_seconds']:continue
        result=directory/'result.json';output=directory/'timeout_timing_observation.json'
        if not result.exists():continue
        if output.exists():
            old=json.loads(output.read_text());assert old['original_manifest_sha256']==sha256(receipt)
            continue
        start=dt.datetime.fromisoformat(m['start_utc']).timestamp()
        observed=result.stat().st_mtime
        assert observed-start>=m['timeout_seconds']
        write_json(output,{'utc':utc(),'original_manifest_sha256':sha256(receipt),
            'original_reported_wall_seconds':m['wall_seconds'],
            'result_sha256':sha256(result),'completion_observer':'result.json filesystem modification timestamp after output hashing',
            'observed_finish_utc_upper_bound':dt.datetime.fromtimestamp(observed,dt.timezone.utc).isoformat(),
            'observed_wall_seconds_upper_bound':observed-start,'timeout_seconds':m['timeout_seconds'],
            'reason':'The live adopted-job supervisor used the empty GNU-time receipt mtime after a deadline signal. That file retained its creation time. Original receipt preserved; the result-file timestamp supplies only a completion-observer upper bound, unsuitable for performance comparisons.',
            'unchanged':'Solver command, input hashes, timeout deadline, exit status and all routing outputs.'})
        print(directory.name,'timing annotated',flush=True)


if __name__=='__main__':main()
