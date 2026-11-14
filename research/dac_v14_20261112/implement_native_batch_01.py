#!/usr/bin/env python3
"""Create an independent static-state native batching development workspace."""
import shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
src=D/'timing_cone_workspace_01';dst=D/'native_batch_workspace_01';assert not dst.exists()
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('build','.git','__pycache__'))
p=dst/'vpr/src/route/h3d_joint_native_repair.h';s=p.read_text()
s=s.replace('#include <set>','#include <set>\n#include <string>\n#include <vector>')
s=s.replace('inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat) {\n    const char* input = std::getenv("VPR_JOINT_NATIVE_REQUEST");\n    if (!input || !*input) return;\n    VTR_ASSERT(!is_flat);\n    const char* output = std::getenv("VPR_JOINT_NATIVE_OUTPUT");', 'inline void run(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat,\n                const char* input, const char* output, const std::string& objective) {\n    VTR_ASSERT(input && *input);\n    VTR_ASSERT(!is_flat);')
s=s.replace('    const char* objective_text = std::getenv("VPR_JOINT_NATIVE_OBJECTIVE");\n    const std::string objective = objective_text ? objective_text : "weighted_soft";\n','')
needle='} // namespace h3d_joint_native_repair'
extra=r'''
/** @brief One independent transaction from the same immutable loaded route. */
struct t_batch_request {
    std::string input;     ///< Existing transaction request file.
    std::string output;    ///< Unique diagnostic output file.
    std::string objective; ///< Native cost objective for this transaction only.
};

/** @brief Run legacy single requests or explicitly batched static-state requests.
 *
 * Batches amortize input loading; they do not form a sequence of accepted route
 * updates. Each transaction restores original occupancy and global route trees.
 * Parse the complete manifest before executing any request. No environment
 * variable is changed between requests and no acceptance policy is applied here.
 */
inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat) {
    const char* input = std::getenv("VPR_JOINT_NATIVE_REQUEST");
    const char* batch = std::getenv("VPR_JOINT_NATIVE_BATCH");
    if (batch && *batch) {
        if (input && *input)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Single and batch joint requests are mutually exclusive");
        std::ifstream manifest(batch);
        size_t count = 0;
        if (!(manifest >> count) || !count)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid native joint batch count");
        std::vector<t_batch_request> requests;
        std::set<std::string> outputs;
        for (size_t i = 0; i < count; ++i) {
            t_batch_request request;
            if (!(manifest >> std::quoted(request.input) >> std::quoted(request.output) >> request.objective)
                || request.input.empty() || request.output.empty()
                || request.input == request.output || !outputs.insert(request.output).second
                || (request.objective != "weighted_soft" && request.objective != "weighted_capacity"
                    && request.objective != "physical_soft" && request.objective != "physical_capacity"))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid native joint batch entry %zu", i);
            requests.push_back(std::move(request));
        }
        std::string trailing;
        if (manifest >> trailing)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unexpected native joint batch suffix");
        for (const auto& request : requests) {
            if (outputs.count(request.input))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Joint batch output aliases a request input");
        }
        for (const auto& request : requests)
            run(net_list, opts, is_flat, request.input.c_str(), request.output.c_str(), request.objective);
        VTR_LOG("JOINT_NATIVE_BATCH completed=%zu original_state_restored=1\n", requests.size());
        return;
    }
    if (!input || !*input) return;
    const char* output = std::getenv("VPR_JOINT_NATIVE_OUTPUT");
    const char* objective = std::getenv("VPR_JOINT_NATIVE_OBJECTIVE");
    run(net_list, opts, is_flat, input, output, objective ? objective : "weighted_soft");
}
'''
assert needle in s and 'inline void run(' in s;s=s.replace(needle,extra+'\n'+needle);p.write_text(s)
p=dst/'vpr/src/timing/h3d_native_sta_frontier.h';s=p.read_text();old='                               bool is_flat) {\n    const char* path = std::getenv("VPR_H3D_FINAL_STA_TRACE");';new='                               bool is_flat, const char* explicit_path = nullptr) {\n    const char* path = explicit_path ? explicit_path : std::getenv("VPR_H3D_FINAL_STA_TRACE");';assert old in s;s=s.replace(old,new);s=s.replace(' * not a separate shortest-path model. No routing/timing state is modified.',' * not a separate shortest-path model. No routing/timing state is modified.\n * An explicit path supports independent post-batch restoration validation.');p.write_text(s)
p=dst/'vpr/src/base/vpr_api.cpp';s=p.read_text();needle='        h3d_joint_native_repair::run_if_requested(net_list, vpr_setup.RouterOpts, is_flat);';assert s.count(needle)==1
s=s.replace(needle,needle+r'''
        // Optional validation only: reconstruct native delays and STA after all
        // independent requests, instead of trusting a pre-request STA snapshot.
        const char* batch_post_sta = std::getenv("VPR_JOINT_NATIVE_BATCH_POST_STA");
        if (batch_post_sta && *batch_post_sta) {
            const char* batch_request = std::getenv("VPR_JOINT_NATIVE_BATCH");
            VTR_ASSERT(batch_request && *batch_request);
            NetPinsMatrix<float> restored_delay = make_net_pins_matrix<float>(net_list);
            load_net_delay_from_routing(net_list, restored_delay);
            for (ParentNetId net : net_list.nets()) {
                for (ParentPinId pin : net_list.net_pins(net)) {
                    int index = net_list.pin_net_index(pin);
                    float before = net_delay[net][index];
                    float after = restored_delay[net][index];
                    VTR_ASSERT(before == after || (std::isnan(before) && std::isnan(after)));
                }
            }
            auto restored_calc = std::make_shared<AnalysisDelayCalculator>(atom_ctx.netlist(), atom_ctx.lookup(), restored_delay, vpr_setup.RouterOpts.flat_routing);
            auto restored_timing = make_setup_hold_timing_info(restored_calc, vpr_setup.AnalysisOpts.timing_update_type);
            restored_timing->update();
            h3d_native_sta_frontier::write_if_requested(net_list, restored_delay, *restored_timing, is_flat, batch_post_sta);
        }
''');p.write_text(s)
changed=['vpr/src/base/vpr_api.cpp','vpr/src/route/h3d_joint_native_repair.h','vpr/src/timing/h3d_native_sta_frontier.h']
write(D/'native_batch_implementation_01.json',dict(workspace=str(dst),base='timing_cone_stage_03',changed=changed,source_sha256={n:sha(dst/n) for n in changed},qualification='Independent static-state batch engineering branch; no reservation combination or current queue changes. Native build and equivalence/restoration regression pending.'))
print('Created independent batch workspace')
