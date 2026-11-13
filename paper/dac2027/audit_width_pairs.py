#!/usr/bin/env python3
"""Independently inspect recorded pair identities; do not reread large payloads."""
from pathlib import Path
import collections, hashlib, json
P = Path(__file__).resolve().parent
ROOT = P.parents[1]
B = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
read = lambda p: json.loads(p.read_text())
errors, counts, seen = [], collections.Counter(), set()
seal_document = read(B/'paired_width_input_integrity.json')
if not seal_document['passed']: errors.append('width input seal failed')
for case in sorted((B/'paired_width_cases').glob('*/result.json')):
    d = read(case)
    source = B/'runs'/d['placement']
    seal = seal_document['inputs']
    for width, group in d['widths'].items():
        for role, name in group['roles'].items():
            counts['roles'] += 1
            if name in seen: errors.append(f'duplicate: {name}')
            seen.add(name)
            run = B/'runs'/name
            manifest, pair = read(run/'manifest.json'), read(run/'pair_check.json')
            if not (pair['passed'] and all(pair['checks'].values()) and pair['source']==str(source) and pair['source_width']==100 and pair['target_width']==int(width)):
                errors.append(f'pair check: {name}')
            for filename in ('packed.net', 'placed.place'):
                src = str(source/filename)
                private = manifest['private_input_sha256'].get(str(run/filename))
                registered = manifest['shared_inputs'].get(src, {}).get('sha256')
                sealed = seal.get(src, {}).get('sha256')
                if not private or not private == registered == sealed or not seal.get(src, {}).get('passed'):
                    errors.append(f'digest binding {filename}: {name}')
            if manifest['tags']['width'] != int(width): errors.append(f'width: {name}')
            counts[manifest['execution_status']] += 1
    counts['cases'] += 1
if counts['cases'] != 24 or counts['roles'] != 144: errors.append('unexpected coverage')
result = {'status':'passed' if not errors else 'failed','counts':dict(counts),'errors':errors,
          'scope':'Recorded pair_check and private/shared/sealed SHA256 equality only; no independent rehash of large payload bytes or semantic route audit.',
          'seal_sha256':hashlib.sha256((B/'paired_width_input_integrity.json').read_bytes()).hexdigest()}
(P/'data/width_pair_audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
