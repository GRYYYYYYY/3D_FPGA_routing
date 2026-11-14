#!/usr/bin/env python3
"""Isolated native seed-order intervention, scoped to explicit post-legal requests."""
import shutil
import subprocess
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

source = D/'export_policy_workspace_01'
out = D/'repair_seed_order_workspace_01'
assert not out.exists() and shutil.disk_usage(D).free >= 80*1024**3
binding = read(D/'export_policy_stage_01/binding.json')
assert all(sha(source/name)==digest for name,digest in binding['source_sha256'].items())
assert read(D/'export_policy_native_binding_01.json')['passed']
subprocess.run(['cp','-a','--reflink=auto',str(source),str(out)],check=True)
if (out/'build').exists():shutil.rmtree(out/'build')

def edit(name, old, new):
    path=out/name
    text=path.read_text()
    assert text.count(old)==1,(name,old)
    path.write_text(text.replace(old,new))

edit('vpr/src/route/router_stats.h','#include <cstdint>','#include <cstdint>\n#include <iosfwd>')
edit('vpr/src/route/router_stats.h',
    '    const std::vector<uint8_t>* repair_forbidden_nodes_ = nullptr;',
    '    int repair_seed_order_ = 0; ///< Explicit repair only: 0 native DFS, 1 RR ID, 2 (physical Tdel, RR ID).\n'
    '    std::ostream* repair_seed_trace_ = nullptr; ///< Optional actual serial seed insertion trace, owned by the repair caller.\n'
    '    const std::vector<uint8_t>* repair_forbidden_nodes_ = nullptr;')
edit('vpr/src/route/connection_router.tpp',
    '    add_route_tree_to_heap(rt_root, sink_node, cost_params, bounding_box);\n    heap_.build_heap();',
    '''    if (conn_params_->repair_seed_order_ == 0) {
        add_route_tree_to_heap(rt_root, sink_node, cost_params, bounding_box);
    } else {
        // Only explicit nonflat, non-RCV repair requests use this alternative.
        VTR_ASSERT(!is_flat_ && !rcv_path_manager.is_enabled());
        VTR_ASSERT(conn_params_->repair_seed_order_ == 1 || conn_params_->repair_seed_order_ == 2);
        std::vector<const RouteTreeNode*> pending{&rt_root};
        std::vector<const RouteTreeNode*> seeds;
        while (!pending.empty()) {
            const RouteTreeNode* node = pending.back();
            pending.pop_back();
            rcv_path_manager.mark_node_visited(node->inode);
            if (node->re_expand) seeds.push_back(node);
            for (const RouteTreeNode& child : node->child_nodes()) pending.push_back(&child);
        }
        const int order = conn_params_->repair_seed_order_;
        std::sort(seeds.begin(), seeds.end(), [order](const RouteTreeNode* a, const RouteTreeNode* b) {
            if (order == 2 && a->Tdel != b->Tdel) return a->Tdel < b->Tdel;
            return a->inode < b->inode;
        });
        for (const RouteTreeNode* seed : seeds)
            add_route_tree_node_to_heap(*seed, sink_node, cost_params, bounding_box);
    }
    heap_.build_heap();''')
edit('vpr/src/route/serial_connection_router.cpp','#include <algorithm>','#include <algorithm>\n#include <ostream>')
edit('vpr/src/route/serial_connection_router.cpp',
    '''    update_serial_router_stats(this->router_stats_,
                               /*is_push=*/true,
                               inode,''',
    '''    if (this->conn_params_ && this->conn_params_->repair_seed_trace_) {
        // Record actual inserted seeds, after the native bounding-box/cost checks.
        *this->conn_params_->repair_seed_trace_ << "SEED " << size_t(this->conn_params_->net_id_)
            << ' ' << this->conn_params_->target_pin_num_ << ' ' << this->conn_params_->repair_seed_order_
            << ' ' << cost_params.pres_fac << ' ' << size_t(inode) << ' ' << rt_node.Tdel
            << ' ' << this->rr_node_route_inf_[inode].path_cost
            << ' ' << this->rr_node_route_inf_[inode].backward_path_cost << '\\n';
    }
    update_serial_router_stats(this->router_stats_,
                               /*is_push=*/true,
                               inode,''')
edit('vpr/src/route/h3d_joint_native_repair.h',
    '    out << "MODE " << objective << \'\\n\';',
    '''    out << "MODE " << objective << '\\n';
    const char* order_text = std::getenv("VPR_JOINT_NATIVE_SEED_ORDER");
    const std::string seed_order = order_text && *order_text ? order_text : "native";
    int seed_order_code = 0;
    if (seed_order == "rr_id") seed_order_code = 1;
    else if (seed_order == "delay_rr_id") seed_order_code = 2;
    else if (seed_order != "native") VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid repair seed order: %s", seed_order.c_str());
    std::ofstream search_trace, seed_trace;
    const char* search_path = std::getenv("VPR_JOINT_NATIVE_SEARCH_TRACE");
    const char* seed_path = std::getenv("VPR_JOINT_NATIVE_SEED_TRACE");
    if (search_path && *search_path) {
        search_trace.open(search_path);
        if (!search_trace) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot open repair search-cost trace");
        search_trace << std::setprecision(17);
    }
    if (seed_path && *seed_path) {
        seed_trace.open(seed_path);
        if (!seed_trace) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot open actual repair seed trace");
        seed_trace << std::setprecision(17);
    }''')
edit('vpr/src/route/h3d_joint_native_repair.h',
    '        ConnectionParameters params(net, pin, false, no_choke_points);',
    '        ConnectionParameters params(net, pin, false, no_choke_points);\n'
    '        params.repair_seed_order_ = seed_order_code;\n'
    '        params.repair_seed_trace_ = seed_trace.is_open() ? &seed_trace : nullptr;')
edit('vpr/src/route/h3d_joint_native_repair.h',
    '            out << "ATTEMPT " << number',
    '''            if (search_trace.is_open()) {
                // The returned RTExploredNode intentionally omits cost fields.
                // Read the real sink labels before reset_path_costs clears them.
                search_trace << "COST " << number << ' ' << pin << ' ' << seed_order_code
                    << ' ' << pass << ' ' << pressure << ' ' << found << ' ' << feasible
                    << ' ' << routing.rr_node_route_inf[sink].path_cost
                    << ' ' << routing.rr_node_route_inf[sink].backward_path_cost
                    << ' ' << costs.criticality << ' ' << costs.astar_fac << '\\n';
            }
            out << "ATTEMPT " << number''')
edit('vpr/src/base/h3d_candidate_observer.h','#include <cstdlib>','#include <cstdlib>\n#include <filesystem>')
edit('vpr/src/base/h3d_candidate_observer.h',
    '        : route_id_(g_vpr_ctx.routing().routing_id) {',
    '''        : route_id_(g_vpr_ctx.routing().routing_id) {
        if (!std::filesystem::is_directory(directory))
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Actual candidate output directory must already exist: %s", directory.c_str());''')
task=out/'vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_repair_seed_order'
task.mkdir(parents=True)
(task/'run.py').write_text('''#!/usr/bin/env python3
"""Native integration regression on sealed small two-layer routing fixtures."""
import argparse, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--research-root',type=Path,required=True)
a=p.parse_args()
subprocess.run([sys.executable,str(a.research_root/'validate_repair_seed_order_tiny.py')],check=True)
''')
(task/'README.md').write_text('''# Explicit serial repair seed order

Run `python run.py --research-root <registered research directory>` using its
Python environment after building the independent stage from the repository root.
The fixture reuses existing packed/place/route data, with no synthesis/placement.
The regression checks native default compatibility, three seed policies, actual
candidate FULL/newSTA versus independent LOAD, failed transactions, invalid policy
isolation, and clear missing-directory rejection. Native FULL/physical delay,
domains, capacities, original-source recovery and endpoint precision stay required.
The source subset does not include the upstream VTR task driver; this standalone
strong regression entry calls the real serial VPR binary and emits a bound receipt.
''')
modified=['vpr/src/route/router_stats.h','vpr/src/route/connection_router.tpp',
    'vpr/src/route/serial_connection_router.cpp','vpr/src/route/h3d_joint_native_repair.h',
    'vpr/src/base/h3d_candidate_observer.h']
write(D/'repair_seed_order_preparation_01.json',dict(passed=True,workspace=str(out),modified=modified,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),D/'export_policy_stage_01/binding.json',D/'export_policy_native_binding_01.json',D/'fused_eltwise_order_mechanism_01.json',*[out/name for name in modified],task/'run.py',task/'README.md']},
    question='Does explicit serial repair seed ordering remove the causal serialization sensitivity while preserving seed membership, original native primary costs, legality, domains and FULL/STA?',
    qualification='New independent source only, current cohort untouched. Defaults retain native DFS. RR-ID and physical-delay/RR-ID policies change insertion order only, not physical Tdel or cost units. Actual seed and real sink cost traces are optional and separate from compatible primary transaction logs. Missing output directory now reports a clear native error. Build and real regression/paired source tests pending; no QoR claim.'))
print(out,flush=True)
