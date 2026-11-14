#!/usr/bin/env python3
"""Bind the actual tested policy/operator scope without broad extrapolation."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'repair_seed_order_native_binding_01.json'
assert not out.exists()
proofs=['repair_seed_order_tiny_01/completion.json','repair_seed_order_eltwise_01/completion.json','fused_preset_tiny_01/completion.json']
for name in proofs:
    data=read(D/name);assert data['passed'] and all(sha(path)==digest for path,digest in data['source_sha256'].items())
stage=D/'repair_seed_order_stage_01'
binding=read(stage/'binding.json')
assert sha(stage/'bin/vpr')==binding['binary_sha256']
assert all(sha(D/'repair_seed_order_workspace_01'/name)==digest for name,digest in binding['source_sha256'].items())
files=[Path(__file__).resolve(),stage/'binding.json',D/'repair_seed_order_mechanism_01.json']+[D/name for name in proofs]
result=dict(passed=True,binary_sha256=binding['binary_sha256'],source_sha256={str(path):sha(path)for path in files},
    actual_scope=['12standalone tiny default/policy/membership/FULLSTA/independentLOAD/failure/error restoration checks',
        '6real eltwise source-by-policy transactions with6independent LOAD/full physical audits',
        '6tiny preset-plus-subsequent-native-query/independentLOAD checks across old export and new seed backends'],
    evidence='Native default reproduces known tiny/eltwise candidates. Both explicit policies remove actual eltwise source-order sensitivity. No physical timing model, native primary formula or congestion mechanism changed; actual path costs can differ with choices. Source restoration and dedicated candidate FULL/freshSTA remain real.',
    unsupported=['general flat/RCV/high-fanout policy APIs','arbitrary nonzeroRC/multilayer resource graphs','large CPD-changing forced-path quality','automatic global-policy transfer before its own cohort passes','cold full-algorithm speedup'],
    native_calls_for_binding=0)
write(out,result);write(stage/'native_validation_binding_01.json',dict(result,binding=str(out),binding_sha256=sha(out)))
print(dict(passed=True,binary_sha256=binding['binary_sha256']),flush=True)
