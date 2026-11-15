"""Select routed connections afresh from an immutable native STA observation."""
import json
import math
import struct


def select(path, near_ns=0.):
    rows=[]
    for line in open(path):
        r=json.loads(line)
        if (r['type']=='pin' and not r['driver'] and not r['ignored'] and not r['global']
                and r['route_tree_present'] and isinstance(r['setup_slack_s'],(int,float))
                and math.isfinite(r['setup_slack_s'])):
            rows.append(r)
    rows.sort(key=lambda r:(r['setup_slack_s'],r['net'],r['pin']))
    assert rows and near_ns>=0
    worst=rows[0]['setup_slack_s']
    bits=struct.unpack('I',struct.pack('f',abs(worst)))[0]
    ulp=struct.unpack('f',struct.pack('I',bits+1))[0]-abs(worst)
    window=max(8*ulp,near_ns*1e-9)
    selected=[dict(net=r['net'],pin=r['pin'],sink=r['tree_rr'],slack_s=r['setup_slack_s'],
                   raw_criticality=r['setup_criticality_raw'],native_net_delay_s=r['native_net_delay_s'])
              for r in rows if r['setup_slack_s']<=worst+window]
    return dict(targets=selected,worst_slack_s=worst,grouping_ulp_s=ulp,window_s=window,
                near_ns=near_ns,eligible_connections=len(rows),
                qualification='Eight float ULPs group selection ties only. Acceptance uses exact native numbers, with no tolerance.')
