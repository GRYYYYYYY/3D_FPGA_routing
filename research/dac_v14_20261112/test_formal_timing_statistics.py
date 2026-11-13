#!/usr/bin/env python3
"""Check complete-group admission, registered repeats and GNU time units."""
from formal_timing_statistics import planned_roles, parse_time, group_statistics

reg = dict(circuits=['a', 'b'], arms=['A0', 'R1'], orders=[['A0', 'R1'], ['R1', 'A0']])
assert len(planned_roles(reg)) == 8
for malformed in [dict(reg, circuits=['a', 'a']), dict(reg, orders=[]),
                  dict(reg, orders=[['A0', 'A0']]), dict(reg, arms=['A0', 'A0'])]:
    try:
        planned_roles(malformed)
    except AssertionError:
        pass
    else:
        raise AssertionError('Accepted malformed registration')
r = parse_time('''User time (seconds): 16.28
System time (seconds): 0.85
Elapsed (wall clock) time (h:mm:ss or m:ss): 0:17.73
Maximum resident set size (kbytes): 1040884
Exit status: 0
''')
assert r['max_rss_kib'] == 1040884 and r['gnu_time_elapsed_seconds'] == 17.73
assert r['user_cpu_seconds'] == 16.28 and r['system_cpu_seconds'] == .85
assert parse_time('Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02:03.5')['gnu_time_elapsed_seconds'] == 3723.5
group = [dict(status='legal', position=i, process_seconds=t, planning_seconds=1, max_rss_kib=m)
         for i, (t, m) in enumerate([(2, 100), (4, 300)])]
s = group_statistics(group)
assert s['complete'] and s['process_median'] == 3 and s['max_rss_kib_median'] == 200 and s['max_rss_kib_max'] == 300
for status in ['failed', 'timeout', 'running', 'missing', 'legal_pending_batch_seal']:
    partial = [group[0], dict(group[1], status=status)]
    s = group_statistics(partial)
    assert not s['complete'] and s['process_median'] is None and s['max_rss_kib_median'] is None
    assert s['process_repeats'] == [2, 4] and s['statuses'] == ['legal', status]
print('PASS registered two-repeat schedule, malformed roles, wall/RSS units and failed/unsealed group exclusion')
