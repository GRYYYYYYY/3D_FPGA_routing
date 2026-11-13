"""Small, independently testable helpers for complete-repeat timing summaries."""
import hashlib
import math
import re
import statistics


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def planned_roles(reg):
    assert reg['circuits'] and reg['arms'] and reg['orders']
    assert len(set(reg['circuits'])) == len(reg['circuits'])
    assert len(set(reg['arms'])) == len(reg['arms'])
    roles = []
    for c in reg['circuits']:
        for repeat, order in enumerate(reg['orders']):
            assert len(order) == len(reg['arms']) and set(order) == set(reg['arms'])
            roles.extend((c, repeat, arm) for arm in order)
    return roles


def parse_time(text):
    result = {}
    labels = {
        'Maximum resident set size (kbytes)': ('max_rss_kib', int),
        'User time (seconds)': ('user_cpu_seconds', float),
        'System time (seconds)': ('system_cpu_seconds', float),
        'Major (requiring I/O) page faults': ('major_page_faults', int),
        'Minor (reclaiming a frame) page faults': ('minor_page_faults', int),
        'Voluntary context switches': ('voluntary_context_switches', int),
        'Involuntary context switches': ('involuntary_context_switches', int),
        'File system inputs': ('filesystem_input_blocks', int),
        'File system outputs': ('filesystem_output_blocks', int),
        'Exit status': ('gnu_time_exit_status', int),
    }
    for line in text.splitlines():
        line = line.strip()
        for label, (key, convert) in labels.items():
            if line.startswith(label + ':'):
                assert key not in result
                result[key] = convert(line[len(label) + 1:].strip())
                assert math.isfinite(result[key]) and result[key] >= 0
        match = re.match(r'Elapsed \(wall clock\) time .*\):\s*(\S+)$', line)
        if match:
            values = [float(v) for v in match[1].split(':')]
            assert 1 <= len(values) <= 3 and all(math.isfinite(v) and v >= 0 for v in values)
            result['gnu_time_elapsed_seconds'] = sum(v * 60**i for i, v in enumerate(reversed(values)))
    return result


def group_statistics(group):
    complete = all(r['status'] == 'legal' for r in group)
    out = dict(complete=complete, statuses=[r['status'] for r in group], positions=[r['position'] for r in group])
    for field, label in [('process_seconds', 'process'), ('planning_seconds', 'planning'),
                         ('max_rss_kib', 'max_rss_kib'), ('router_seconds', 'router')]:
        values = [r.get(field) for r in group]
        usable = complete and all(v is not None for v in values)
        out[label + '_repeats'] = values
        out[label + '_median'] = statistics.median(values) if usable else None
        out[label + '_max'] = max(values) if usable else None
    return out
