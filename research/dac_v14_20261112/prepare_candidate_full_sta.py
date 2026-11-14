#!/usr/bin/env python3
"""Independent native candidate FULL/STA callback; no edits to registered quality jobs."""
import shutil
import subprocess
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

src = D / 'domain_failure_release_workspace_01'
out = D / 'candidate_full_sta_workspace_01'
assert not out.exists() and shutil.disk_usage(D).free >= 80 * 1024**3
base = read(D / 'domain_failure_release_stage_01/binding.json')
assert all(sha(src / name) == h for name, h in base['source_sha256'].items())
subprocess.run(['cp', '-a', '--reflink=auto', str(src), str(out)], check=True)
if (out / 'build').exists():
    shutil.rmtree(out / 'build')

header = out / 'vpr/src/route/h3d_joint_native_repair.h'
s = header.read_text().replace('#include <map>', '#include <map>\n#include <functional>\n#include <exception>')
needle = 'namespace h3d_joint_native_repair {'
addition = r'''
/** @brief Install complete candidate copies while preserving original tree identities. */
class ScopedCandidateTrees {
  public:
    /** @brief Restore original trees, including their sink lookup pointers. */
    ~ScopedCandidateTrees() {
        auto& routing = g_vpr_ctx.mutable_routing();
        for (auto& [net, tree] : originals_) routing.route_trees[net].emplace(std::move(tree));
    }
    /** @brief Substitute candidate trees; occupancy already describes these local trees. */
    void install(const std::map<ParentNetId, std::unique_ptr<RouteTree>>& candidates) {
        auto& routing = g_vpr_ctx.mutable_routing();
        for (const auto& [net, tree] : candidates) {
            VTR_ASSERT(routing.route_trees[net]);
            originals_.emplace(net, std::move(routing.route_trees[net].value()));
            routing.route_trees[net].emplace(*tree, net);
        }
    }
  private:
    std::map<ParentNetId, RouteTree> originals_; ///< Original trees moved intact, never assigned candidate data.
};
'''
assert s.count(needle) == 1
s = s.replace(needle, needle + addition)
old = 'inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat) {'
new = 'inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat,\n                             const std::function<void()>& candidate_observer = {}) {'
assert s.count(old) == 1
s = s.replace(old, new)
# Erasing the active domain is a state mutation, independent of assertion level.
s = s.replace('VTR_ASSERT(vertical_domain_nets.erase(net) == 1);',
              'const size_t erased = vertical_domain_nets.erase(net);\n                VTR_ASSERT(erased == 1);')
needle = '    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(tree->root(), -1);\n    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(routing.route_trees[net]->root(), 1);'
addition = r'''    std::exception_ptr candidate_error;
    if (transaction_ok && candidate_observer) {
        try {
            ScopedCandidateTrees installed;
            installed.install(trees);
            candidate_observer();
        } catch (...) {
            candidate_error = std::current_exception();
        }
    }
'''
assert s.count(needle) == 1
s = s.replace(needle, addition + needle)
needle = '    VTR_LOG("JOINT_NATIVE_REPAIR complete=%d restored=%zu/%zu occupancy_restored=1\\n", transaction_ok, finished, nqueries);'
assert s.count(needle) == 1
s = s.replace(needle, needle + '\n    if (candidate_error) std::rethrow_exception(candidate_error);')
header.write_text(s)

observer = out / 'vpr/src/base/h3d_candidate_observer.h'
observer.write_text(r'''#pragma once
/** @file Dedicated real-candidate FULL/STA export and restored-source observation. */
#include <cstdlib>
#include <fstream>
#include <functional>
#include <string>
#include <utility>
#include <vector>
#include "globals.h"
#include "vpr_error.h"
#include "vtr_log.h"

namespace h3d_candidate_observer {
/** @brief Restore output hooks and route digest after an actual state observation. */
class ScopedOutputPaths {
  public:
    /** @brief Preserve the source identity, not the digest of a diagnostic serialization. */
    explicit ScopedOutputPaths(const std::string& directory)
        : route_id_(g_vpr_ctx.routing().routing_id) {
        for (const char* name : {"VPR_H3D_FINAL_STA_TRACE", "VPR_H3D_FINAL_TIMING_ECHO"}) {
            const char* old = std::getenv(name);
            paths_.push_back({name, {old != nullptr, old ? old : ""}});
        }
        if (setenv("VPR_H3D_FINAL_STA_TRACE", (directory + "/native_sta_frontier.jsonl").c_str(), 1)
            || setenv("VPR_H3D_FINAL_TIMING_ECHO", (directory + "/timing_graph.full_precision.echo").c_str(), 1)) {
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot set private candidate output hooks");
        }
    }
    /** @brief Restore all source hooks even when the native check throws. */
    ~ScopedOutputPaths() {
        for (const auto& [name, value] : paths_) {
            if (value.first) setenv(name.c_str(), value.second.c_str(), 1);
            else unsetenv(name.c_str());
        }
        g_vpr_ctx.mutable_routing().routing_id = route_id_;
    }
  private:
    std::string route_id_; ///< Source route digest prior to diagnostic print_route.
    std::vector<std::pair<std::string, std::pair<bool, std::string>>> paths_; ///< Existing output hook identities.
};
} // namespace h3d_candidate_observer
''')
api = out / 'vpr/src/base/vpr_api.cpp'
s = api.read_text().replace('#include "h3d_analysis_queue.h"', '#include "h3d_analysis_queue.h"\n#include "h3d_candidate_observer.h"')
old = '        h3d_joint_native_repair::run_if_requested(net_list, vpr_setup.RouterOpts, is_flat);'
new = r'''        const char* candidate_path = std::getenv("VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY");
        const std::string candidate_directory = candidate_path ? candidate_path : "";
        std::function<void()> candidate_observer;
        // This uses the same native checker and a new independent STA object;
        // the original timing_info/net_delay remain untouched for source analysis.
        const auto observe_state = [&](const std::string& directory, const char* kind) {
            h3d_candidate_observer::ScopedOutputPaths paths(directory);
            VTR_LOG("H3D_ACTUAL_STATE_BEGIN %s\n", kind);
            check_route(net_list, vpr_setup.RouterOpts.route_type, e_check_route_option::FULL, is_flat);
            print_route(net_list, vpr_setup.FileNameOpts.PlaceFile.c_str(), (directory + "/routed.route").c_str(), is_flat);
            NetPinsMatrix<float> current_delay = make_net_pins_matrix<float>(net_list);
            load_net_delay_from_routing(net_list, current_delay);
            auto current_calc = std::make_shared<AnalysisDelayCalculator>(atom_ctx.netlist(), atom_ctx.lookup(), current_delay, vpr_setup.RouterOpts.flat_routing);
            auto current_timing = make_setup_hold_timing_info(current_calc, vpr_setup.AnalysisOpts.timing_update_type);
            current_timing->update();
            h3d_native_sta_frontier::write_if_requested(net_list, current_delay, *current_timing, is_flat);
            h3d_native_timing_echo::write_if_requested(*current_timing, *current_calc);
            std::ofstream receipt(directory + "/native_state_gate.txt");
            receipt << kind << " FULL fresh_STA actual_installed_trees\n";
            receipt.close();
            if (!receipt) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot write actual native state gate");
            VTR_LOG("H3D_ACTUAL_STATE_COMPLETE %s\n", kind);
        };
        if (!candidate_directory.empty()) candidate_observer = [&]() { observe_state(candidate_directory, "candidate"); };
        h3d_joint_native_repair::run_if_requested(net_list, vpr_setup.RouterOpts, is_flat, candidate_observer);
        if (!candidate_directory.empty()) observe_state(candidate_directory + "_restored", "restored_source");'''
assert s.count(old) == 1
s = s.replace(old, new)
api.write_text(s)

queue = out / 'vpr/src/base/h3d_analysis_queue.h'
s = queue.read_text()
s = s.replace('(operation != "repair" && operation != "repair_feedback")',
              '(operation != "repair" && operation != "repair_feedback"\n                        && operation != "repair_fused" && operation != "repair_feedback_fused")')
s = s.replace('"VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE"})',
              '"VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE", "VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY"})')
s = s.replace('if (operation == "repair" || operation == "repair_feedback") {',
              'if (operation == "repair" || operation == "repair_feedback" || operation == "repair_fused" || operation == "repair_feedback_fused") {\n                    const bool fused = operation == "repair_fused" || operation == "repair_feedback_fused";\n                    if (fused) {\n                        fs::create_directory("candidate");\n                        fs::create_directory("candidate_restored");\n                    }')
s = s.replace('operation == "repair_feedback" ? "1" : "0", 1)',
              '(operation == "repair_feedback" || operation == "repair_feedback_fused") ? "1" : "0", 1)\n                        || setenv("VPR_JOINT_NATIVE_CANDIDATE_DIRECTORY", fused ? "candidate" : "", 1)')
queue.write_text(s)

pool = D / 'candidate_full_sta_analysis_pool.py'
assert not pool.exists()
s = (D / 'native_feedback_analysis_pool.py').read_text()
s = s.replace('domain_failure_release=False):', 'domain_failure_release=False, candidate_full_sta=False):')
s = s.replace('assert not domain_failure_release or (repair and crossing_domain is not None)',
              'assert not domain_failure_release or (repair and crossing_domain is not None)\n        assert not candidate_full_sta or repair')
s = s.replace('options = dict(operation=("repair_feedback" if domain_failure_release else "repair") if repair else "analysis",',
              'operation = (("repair_feedback" if domain_failure_release else "repair") + ("_fused" if candidate_full_sta else "")) if repair else "analysis"\n        options = dict(operation=operation,')
s = s.replace("quoted('repair_feedback' if domain_failure_release else 'repair')", 'quoted(operation)')
needle = '        paths += list(snapshots.values())'
addition = '''        candidate_gate = None
        if candidate_full_sta and native_ok:
            restored = native/'candidate_restored'
            restored_files = [restored/n for n in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo','native_state_gate.txt']]
            complete = complete and all(p.is_file() for p in restored_files) and 'H3D_ACTUAL_STATE_COMPLETE restored_source' in stdout
            paths += restored_files
            if transaction_succeeded:
                actual = native/'candidate'
                candidate_files = [actual/n for n in ['routed.route','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo','native_state_gate.txt']]
                candidate_gate = all(p.is_file() for p in candidate_files) and 'H3D_ACTUAL_STATE_COMPLETE candidate' in stdout
                complete = complete and candidate_gate
                paths += candidate_files
'''
assert s.count(needle) == 1
s = s.replace(needle, addition + needle)
s = s.replace('native_transaction_succeeded=transaction_succeeded,native_options=options',
              'native_transaction_succeeded=transaction_succeeded,candidate_full_STA_passed=candidate_gate,native_options=options')
pool.write_text(s)
files = [Path(__file__).resolve(), header, observer, api, queue, pool, D / 'domain_failure_release_stage_01/binding.json',
         D / 'automatic_domain_release_mechanism_01.json']
write(D / 'candidate_full_sta_preparation_01.json', dict(passed=True, workspace=str(out),
      base='domain_failure_release_stage_01', source_sha256={str(p): sha(p) for p in files},
      question='Can one native child install actual candidate copies, run native FULL/fresh STA/serialization, restore original trees/occupancy/digest/output hooks and reobserve the original FULL/STA, without another route LOAD?',
      qualification='Independent default-off implementation. Current uniform quality cohort unchanged. New per-job fused operation identities and separate candidate/restored-source artifacts. Physical/scope audits and exact accepted endpoint comparisons remain mandatory; build/tiny/large and state materialization validation pending. No cold-algorithm time or in-process accepted-state performance claim.'))
print(out, flush=True)
