#!/usr/bin/env python3
"""Freeze validated selector candidate for future independently registered batches."""
import shutil,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'compact_selector_stage_01';proof=D/'compact_cone_benchmark_01/completion.json';c=read(proof)
assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items())
assert set(c['summary'])=={'bnn_initial','bnn_accepted','spmv'}
assert all(r['status']=='identical' for r in c['rows'])
b.mkdir(exist_ok=False);files=[D/'compact_timing_cone.py',D/'current_sta_arrival_cone_compact.py',D/'current_sta_arrival_cone.py',D/'native_timing_echo_v2.py',D/'run_registered_native_transactions_v2.py',D/'compact_timing_cone_validation_01/completion.json',proof,Path(__file__).resolve()]
for p in files:
 name=p.name if p.name!='completion.json' else p.parent.name+'_completion.json';shutil.copy2(p,b/name)
write(b/'binding.json',dict(status='selector_component_validated_future_integration_candidate',source_sha256={str(p):sha(p) for p in files},snapshot_sha256={p.name:sha(p) for p in b.iterdir() if p.is_file()},
 benchmark=c['summary'],native_calls=0,runtime_model='Source snapshot with existing D runtime dependencies bound through original implementation/proof digests.',
 qualification='Exact selector equivalence tested on current and initialBNN plusSPMV and domain/disabled/float32 fixtures. Component development runtime only. Future coordinator integration still needs an independent native batch; neither running nor queued cohort was modified.',frozen_at=time.time()))
print(c['summary'],flush=True)
