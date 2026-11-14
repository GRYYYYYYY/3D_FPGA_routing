#!/usr/bin/env python3
"""Independent resource export policy; full native STA and frontier remain mandatory."""
import shutil
import subprocess
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

src = D / 'candidate_full_sta_workspace_01'
out = D / 'export_policy_workspace_01'
assert not out.exists() and shutil.disk_usage(D).free >= 80 * 1024**3
base = read(D / 'candidate_full_sta_stage_01/binding.json')
assert all(sha(src / name) == h for name, h in base['source_sha256'].items())
subprocess.run(['cp', '-a', '--reflink=auto', str(src), str(out)], check=True)
if (out / 'build').exists():
    shutil.rmtree(out / 'build')
header = out / 'vpr/src/base/h3d_candidate_observer.h'
s = header.read_text()
needle = '        if (setenv("VPR_H3D_FINAL_STA_TRACE", (directory + "/native_sta_frontier.jsonl").c_str(), 1)'
replacement = '''        // Graph text is optional output. The caller still executes native FULL,
        // fresh complete STA and the full-precision frontier unconditionally.
        const char* echo_path = std::getenv("VPR_H3D_FINAL_TIMING_ECHO");
        const bool full_echo = echo_path && *echo_path;
''' + needle
assert s.count(needle) == 1
s = s.replace(needle, replacement)
old = 'setenv("VPR_H3D_FINAL_TIMING_ECHO", (directory + "/timing_graph.full_precision.echo").c_str(), 1)'
new = 'setenv("VPR_H3D_FINAL_TIMING_ECHO", full_echo ? (directory + "/timing_graph.full_precision.echo").c_str() : "", 1)'
assert s.count(old) == 1
header.write_text(s.replace(old, new))

pool = D / 'export_policy_analysis_pool.py'
assert not pool.exists()
s = (D / 'candidate_full_sta_analysis_pool.py').read_text()
for kind, folder in [('restored', 'restored'), ('candidate', 'actual')]:
    needle = f"{kind}_files = [{folder}/n for n in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo','native_state_gate.txt']]"
    replacement = f"{kind}_files = [{folder}/n for n in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','native_state_gate.txt']]+([{folder}/'timing_graph.full_precision.echo'] if echo else [])"
    assert s.count(needle) == 1
    s = s.replace(needle, replacement)
s = s.replace('        paths += list(snapshots.values())', '''        if not echo:
            assert not any((native/part/'timing_graph.full_precision.echo').exists() for part in ['.','candidate','candidate_restored']), 'Compact export unexpectedly produced a full graph echo'
        paths += list(snapshots.values())''')
s = s.replace('candidate_full_STA_passed=candidate_gate,native_options=options',
              'candidate_full_STA_passed=candidate_gate,full_timing_echo_requested=bool(echo),native_options=options')
pool.write_text(s)

evaluator = D / 'pool_state_evaluator_v7.py'
assert not evaluator.exists()
s = (D / 'pool_state_evaluator_v6.py').read_text()
needle = "        metrics=parse_metrics((rd/'stdout.log').read_text(errors='replace')) if (rd/'stdout.log').exists() else {}"
assert s.count(needle) == 1
s = s.replace(needle, needle + "\n        full_echo_requested=native.get('full_timing_echo_requested',True)")
s = s.replace("native_precision_echo=(rd/'timing_graph.full_precision.echo').is_file()",
              "native_precision_capture=(rd/'timing_graph.full_precision.echo').is_file() if full_echo_requested else vector is not None and native['passed']")
s = s.replace('observed_state_kind=observed_kind,actual_installed_candidate=',
              'full_timing_echo_requested=full_echo_requested,can_select_timing_cone=full_echo_requested,observed_state_kind=observed_kind,actual_installed_candidate=')
needle = "        assert worker['static_identity']==self.pool.identity and worker['passed'] and worker['candidate_full_STA_passed']"
assert s.count(needle) == 1
s = s.replace(needle, "        assert worker.get('full_timing_echo_requested',True)==origin.get('full_timing_echo_requested',True),'Export-level view differs from immutable actual receipt'\n" + needle)
old = "for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo']:"
new = "for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']+(['timing_graph.full_precision.echo'] if worker.get('full_timing_echo_requested',True) else []):"
assert s.count(old) == 1
evaluator.write_text(s.replace(old, new))
files = [Path(__file__).resolve(), header, pool, evaluator, D / 'candidate_full_sta_stage_01/binding.json',
         D / 'candidate_full_sta_native_binding_01.json', D / 'endpoint_loader_streaming_integration_01/completion.json',
         D / 'resource_only_export_optimization_hypothesis_01.json']
write(D / 'export_policy_preparation_01.json', dict(passed=True, workspace=str(out), source_sha256={str(f): sha(f) for f in files},
      question='Does respecting per-job full graph-echo output level reduce export/materialization overhead while all native search, FULL/freshSTA, complete frontier/endpoint records, constraints and final decisions stay exact?',
      qualification='Independent new version. Existing resource-first timing decoder/kernel untouched. Full graph-echo default remains; compact output advertises unavailable timing-cone text and requires explicit full reobservation before that consumer. No precision reduction, missing endpoint inference, STA omission or claimed speedup; build and paired tiny/large validation pending.'))
print(out, flush=True)
