#!/usr/bin/env python3
"""Second immutable attempt: omit unmeasured entries from the finite DP table."""
import argparse
import run_h3d_delay_study as study

study.BASE = study.ROOT/'results/h3d_delay_20261027_v2'
study.BINARY = study.ROOT/'artifacts/bin/delay-20261027-v2/vpr'

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['register','pilot','main','serial'])
    action=parser.parse_args().action
    study.register() if action=='register' else study.phase_run(action)
