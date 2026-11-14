#!/usr/bin/env python3
"""Prepare an opt-in per-net domain failure fallback in an independent VTR tree."""
import shutil
import subprocess
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

src = D / 'native_repair_queue_workspace_01'
out = D / 'domain_failure_release_workspace_01'
assert not out.exists() and shutil.disk_usage(D).free >= 80 * 1024**3
base = read(D / 'native_repair_queue_stage_01/binding.json')
assert all(sha(src / n) == h for n, h in base['source_sha256'].items())
subprocess.run(['cp', '-a', '--reflink=auto', str(src), str(out)], check=True)
# Relocated generated build files contain absolute source paths. Never reuse them.
if (out / 'build').exists():
    shutil.rmtree(out / 'build')

header = out / 'vpr/src/route/h3d_joint_native_repair.h'
s = header.read_text()
old = '    std::vector<int> original_occ;'
new = '''    const char* release_text = std::getenv("VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE");
    const bool release_failed_domain = release_text && std::string(release_text) == "1";
    if (release_text && *release_text && std::string(release_text) != "0"
        && std::string(release_text) != "1") {
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid domain-failure-release flag");
    }
    std::vector<int> original_occ;'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '        for (float pressure = 1.f; pressure <= 1.e8f; pressure *= 10.f) {'
new = '''        // Failed searches have not committed a branch or changed occupancy.
        // Retry only this net without its domain, preserving prior restorations.
        const int search_passes = release_failed_domain && params.repair_allowed_crossing_sources_ ? 2 : 1;
        for (int pass = 0; pass < search_passes; ++pass) {
            if (pass) {
                router->reset_path_costs();
                router->clear_modified_rr_node_info();
                params.repair_allowed_crossing_sources_ = nullptr;
                VTR_ASSERT(vertical_domain_nets.erase(net) == 1);
                vertical_trace << "RELEASE " << number << ' ' << pin << " domain_search_infeasible\\n";
                out << "DOMAIN_RELEASE " << number << ' ' << pin << '\\n';
            }
        for (float pressure = 1.f; pressure <= 1.e8f; pressure *= 10.f) {'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''        if (!feasible) {
            out << "FAIL_TARGET "'''
new = '''            if (feasible) break;
        }
        if (!feasible) {
            out << "FAIL_TARGET "'''
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace(' * require independent FULL/STA and the selected acceptance policy.',
              ' * require independent FULL/STA and the selected acceptance policy. The opt-in\n'
              ' * failure-release mode relaxes only a failed net domain before any tree update;\n'
              ' * capacity and the complete transaction gates remain mandatory.')
header.write_text(s)

queue = out / 'vpr/src/base/h3d_analysis_queue.h'
s = queue.read_text()
s = s.replace('operation != "repair"', '(operation != "repair" && operation != "repair_feedback")')
s = s.replace('"VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE", "VPR_CURRENT_STA_NATIVE_PRESSURE_START"',
              '"VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE", "VPR_CURRENT_STA_NATIVE_PRESSURE_START",\n'
              '                                         "VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE"')
s = s.replace('if (operation == "repair") {', 'if (operation == "repair" || operation == "repair_feedback") {')
s = s.replace('if (setenv("VPR_JOINT_NATIVE_REQUEST", native_request.c_str(), 1)',
              'if (setenv("VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE", operation == "repair_feedback" ? "1" : "0", 1)\n'
              '                        || setenv("VPR_JOINT_NATIVE_REQUEST", native_request.c_str(), 1)')
queue.write_text(s)
pool = D / 'native_feedback_analysis_pool.py'
assert not pool.exists()
s = (D / 'native_repair_analysis_pool.py').read_text()
s = s.replace('crossing_domain=None, pressure_start=1.):', 'crossing_domain=None, pressure_start=1., domain_failure_release=False):')
s = s.replace('assert crossing_domain is None or repair',
              'assert crossing_domain is None or repair\n        assert not domain_failure_release or (repair and crossing_domain is not None)')
s = s.replace('options = dict(operation="repair" if repair else "analysis",',
              'options = dict(operation=("repair_feedback" if domain_failure_release else "repair") if repair else "analysis",')
s = s.replace("quoted('repair')", "quoted('repair_feedback' if domain_failure_release else 'repair')")
pool.write_text(s)
files = [Path(__file__).resolve(), header, queue, pool, D / 'native_repair_queue_stage_01/binding.json',
         D / 'failure_feedback_domain_dev_02/completion.json', D / 'domain_order_potential_02/completion.json']
write(D / 'domain_failure_release_preparation_01.json', dict(
    passed=True, workspace=str(out), base='native_repair_queue_stage_01',
    source_sha256={str(p): sha(p) for p in files},
    question='Can automatic search-failure-triggered per-net release reproduce the validated partial-domain resource gain without a manual net list or restarting the transaction?',
    qualification='New independent opt-in implementation. Existing registered versions unchanged. Native failure is evidence of this search failure, not a mathematical capacity certificate. Reset heap/path costs before unrestricted retry. Preserve native capacity, real Tdel, full-transaction rollback and subsequent native candidate FULL/STA. Build/tiny/matched large validation pending; no time or QoR claim.'))
print(out, flush=True)
