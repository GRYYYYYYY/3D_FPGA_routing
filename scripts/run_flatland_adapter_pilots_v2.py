#!/usr/bin/env python3
"""Independent repeat after removing quadratic candidate-reachability work."""
import sys
import run_flatland_adapter_pilots as study

study.RUN_TAG = 'adapter_pilot_v2'
study.BINARY = study.ROOT/'artifacts/bin/flatland-edge-v2/vpr'

if __name__ == '__main__': study.main(sys.argv[1])
