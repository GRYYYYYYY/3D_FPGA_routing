"""Stream the existing native endpoint vector without retaining unrelated pins.

Every input line still uses the same standard-library JSON decoder. Numbers,
endpoint/domain identities, duplicate-tag minima and all acceptance guards are
unchanged. This module does not select targets, run STA or decide acceptance.
The original loader and all registered native flows remain untouched.
"""
import json
import math
from pathlib import Path

from retained_prefix_workflow import sha


def load(path):
    path = Path(path)
    endpoint_ids, setup, hold = [], {}, {}
    endpoint_count = metric_count = 0
    metrics = last = None
    for line in path.open():
        row = json.loads(line)
        last = row
        if row['type'] == 'timing_metrics':
            metric_count += 1
            metrics = row
        elif row['type'] == 'endpoint':
            endpoint_count += 1
            identity = (row['node'], row['atom_pin'], row['name'])
            endpoint_ids.append(identity)
            for kind, values in [('setup', setup), ('hold', hold)]:
                for tag in row[kind + '_tags']:
                    key = json.dumps([*identity, tag['launch'], tag['capture']],
                                     separators=(',', ':'))
                    value = tag['slack_s']
                    if key in values:
                        previous = values[key]
                        assert isinstance(value, (int, float))
                        assert isinstance(previous, (int, float))
                        value = min(value, previous)
                    values[key] = value
    assert last is not None and last['type'] == 'complete'
    assert endpoint_count == last['endpoint_rows']
    assert metric_count == 1
    assert len(endpoint_ids) == len(set(endpoint_ids))
    endpoint_ids.sort(key=lambda key: key[0])
    cpd = metrics['least_slack_CPD_s']
    assert isinstance(cpd, (int, float)) and math.isfinite(cpd)
    return dict(cpd_s=cpd, metrics=metrics, endpoint_ids=endpoint_ids,
                setup=setup, hold=hold,
                constraints_sha256=sha(str(path) + '.constraints.echo'),
                trace_sha256=sha(path))
