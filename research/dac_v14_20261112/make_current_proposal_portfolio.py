#!/usr/bin/env python3
"""Build a uniform alternative menu without running native routing or STA."""
import argparse,time
from pathlib import Path
from current_proposal_portfolio import generate
p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();t=time.monotonic();result=generate(a.plan,a.output);print(dict(proposals=[(x['name'],x['repair_connections']) for x in result['proposals']],deduplicated=len(result['duplicates']),complete_process_seconds=time.monotonic()-t),flush=True)
