#!/usr/bin/env python3
"""Independent opt-in native resource census plus fixed per-pool seed policy identity."""
import shutil
import subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

source=D/'repair_seed_order_workspace_01'
out=D/'native_resource_census_workspace_01'
assert not out.exists() and shutil.disk_usage(D).free >= 80*1024**3
base=read(D/'repair_seed_order_stage_01/binding.json')
assert all(sha(source/name)==digest for name,digest in base['source_sha256'].items())
assert read(D/'repair_seed_order_eltwise_01/completion.json')['passed']
assert read(D/'fused_preset_tiny_01/completion.json')['passed']
subprocess.run(['cp','-a','--reflink=auto',str(source),str(out)],check=True)
if(out/'build').exists():shutil.rmtree(out/'build')
header=out/'vpr/src/timing/h3d_native_resource_census.h'
header.write_text(r'''#pragma once
/** @file Opt-in actual routed resources; this is a native census, not an independent audit. */
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <unordered_set>
#include "globals.h"
#include "h3d_native_sta_frontier.h"
#include "route_tree.h"
#include "vpr_error.h"
#include "vtr_log.h"

namespace h3d_native_resource_census {
/** @brief Count actual per-net wire and globally occupied SB/CB resources after real native FULL/STA.
 * The supported edge-encoded graph has single-layer RR nodes and two adjacent layers.
 * Node multiplicities within each serialized branch are counted once per net;
 * CB sources and directed SB pairs are deduplicated by the same source RR IDs
 * used by the independent physical auditor. Timing and route trees are read-only.
 */
inline void write_if_requested(const Netlist<>& net_list, bool is_flat, const char* state_kind) {
    const char* flag = std::getenv("VPR_H3D_RESOURCE_CENSUS");
    if (!flag || !*flag || std::string(flag) == "0") return;
    if (std::string(flag) != "1") VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Invalid native resource census flag");
    const char* trace = std::getenv("VPR_H3D_FINAL_STA_TRACE");
    if (!trace || !*trace) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Resource census requires a dedicated native frontier output");
    const auto started = std::chrono::steady_clock::now();
    const auto& routing = g_vpr_ctx.routing();
    const auto& device = g_vpr_ctx.device();
    const auto& graph = device.rr_graph;
    if (is_flat || device.grid.get_num_layers() != 2)
        VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Native resource census supports nonflat two-layer edge encoding only");
    std::set<RRNodeId> sb, cb;
    std::map<std::string, size_t> crossing_edges;
    size_t wirelength = 0, sb_net_occupancy = 0, cb_net_occupancy = 0, trees = 0;
    for (ParentNetId net : net_list.nets()) {
        if (net_list.net_is_global(net) || !routing.route_trees[net]) continue;
        ++trees;
        std::unordered_set<RRNodeId> used, sb_net, cb_net;
        for (const RouteTreeNode& node : routing.route_trees[net]->all_nodes()) {
            const RRNodeId id = node.inode;
            if (graph.node_layer_low(id) != graph.node_layer_high(id))
                VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Resource census cannot count multilayer RR nodes");
            if (used.insert(id).second) {
                const e_rr_type type = graph.node_type(id);
                if ((type == e_rr_type::CHANX || type == e_rr_type::CHANY)
                    && graph.node_direction(id) != Direction::NONE) {
                    wirelength += 1 + std::abs(graph.node_xhigh(id) - graph.node_xlow(id))
                        + std::abs(graph.node_yhigh(id) - graph.node_ylow(id));
                }
            }
            if (!node.parent()) continue;
            const RRNodeId parent = node.parent()->inode;
            if (graph.node_layer_low(parent) == graph.node_layer_low(id)) continue;
            if (std::abs(int(graph.node_layer_low(parent)) - int(graph.node_layer_low(id))) != 1)
                VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Resource census cannot count nonadjacent crossings");
            ++crossing_edges[std::string(graph.node_type_string(parent)) + "->" + graph.node_type_string(id)];
            if (graph.node_type(parent) == e_rr_type::OPIN) cb_net.insert(parent);
            else {
                if (graph.node_type(parent) != e_rr_type::CHANX || graph.node_direction(parent) != Direction::NONE)
                    VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Resource census encountered an unknown vertical-resource encoding");
                sb_net.insert(parent);
            }
        }
        sb.insert(sb_net.begin(), sb_net.end());
        cb.insert(cb_net.begin(), cb_net.end());
        sb_net_occupancy += sb_net.size();
        cb_net_occupancy += cb_net.size();
    }
    const std::string path = std::string(trace) + ".resources.json";
    const std::string temporary = path + ".tmp";
    std::ofstream output(temporary);
    output << "{\"schema_version\":1,\"assurance_kind\":\"native_actual_route_tree_census\",\"state_kind\":";
    h3d_native_sta_frontier::string(output, state_kind);
    output << ",\"native_routing_id\":";
    h3d_native_sta_frontier::string(output, routing.routing_id);
    output << ",\"routed_net_trees\":" << trees << ",\"physical_metrics\":{"
        << "\"planar_wirelength_excluding_sb_half_nodes\":" << wirelength
        << ",\"sb_pairs_used\":" << sb.size() << ",\"sb_pair_net_occupancy\":" << sb_net_occupancy
        << ",\"cb_crossing_output_sources_used\":" << cb.size()
        << ",\"cb_crossing_output_source_net_occupancy\":" << cb_net_occupancy
        << ",\"actual_crossing_edge_traversals\":{";
    bool first = true;
    for (const auto& [kind, count] : crossing_edges) {
        if (!first) output << ',';
        first = false;
        h3d_native_sta_frontier::string(output, kind);
        output << ':' << count;
    }
    output << "}}}\n";
    output.close();
    if (!output) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot write actual native resource census");
    std::error_code error;
    std::filesystem::rename(temporary, path, error);
    if (error) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot publish actual native resource census");
    VTR_LOG("H3D_RESOURCE_CENSUS kind=%s wire=%zu SB=%zu CB=%zu seconds=%.9f\n", state_kind,
        wirelength, sb.size(), cb.size(), std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count());
}
} // namespace h3d_native_resource_census
''')
api=out/'vpr/src/base/vpr_api.cpp'
s=api.read_text()
needle='#include "h3d_candidate_observer.h"'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n#include "h3d_native_resource_census.h"')
needle='        h3d_native_sta_frontier::write_if_requested(net_list, net_delay, *timing_info, is_flat);'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n        h3d_native_resource_census::write_if_requested(net_list, is_flat, "input");')
needle='            h3d_native_sta_frontier::write_if_requested(net_list, current_delay, *current_timing, is_flat);'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n            h3d_native_resource_census::write_if_requested(net_list, is_flat, kind);')
api.write_text(s)
pool=D/'seed_census_analysis_pool.py'
assert not pool.exists()
s=(D/'export_policy_analysis_pool.py').read_text()
s=s.replace('memory_bytes=64*1024**3):','memory_bytes=64*1024**3, seed_order="native", native_census=False):')
s=s.replace('        self.started=time.monotonic();', '        assert seed_order in ["native","rr_id","delay_rr_id"] and isinstance(native_census,bool)\n        self.seed_order=seed_order;self.native_census=native_census\n        self.started=time.monotonic();',1)
needle="        self.environment.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n        self.environment.update(VPR_JOINT_NATIVE_SEED_ORDER=self.seed_order,VPR_H3D_RESOURCE_CENSUS='1' if self.native_census else '0')")
s=s.replace("static_input_stat_identity=self.input_stats,runtime_libraries_resolved_before_start=True", "native_seed_order=self.seed_order,native_resource_census=self.native_census,static_input_stat_identity=self.input_stats,runtime_libraries_resolved_before_start=True")
s=s.replace('options = dict(operation=operation, inputs=input_hashes,','options = dict(operation=operation, inputs=input_hashes, seed_order=self.seed_order if repair else None, native_resource_census=self.native_census,')
s=s.replace("        stdout=(native/'stdout.log').read_text()", "        if self.native_census:paths.append(native/'native_sta_frontier.jsonl.resources.json')\n        stdout=(native/'stdout.log').read_text()")
s=s.replace("restored_files = [restored/n for n in ['routed.route'", "restored_files = ([restored/'native_sta_frontier.jsonl.resources.json'] if self.native_census else [])+[restored/n for n in ['routed.route'")
s=s.replace("candidate_files = [actual/n for n in ['routed.route'", "candidate_files = ([actual/'native_sta_frontier.jsonl.resources.json'] if self.native_census else [])+[actual/n for n in ['routed.route'")
s=s.replace('full_timing_echo_requested=bool(echo),native_options=options', 'full_timing_echo_requested=bool(echo),native_resource_census_requested=self.native_census,native_seed_order=self.seed_order,native_options=options')
pool.write_text(s)
files=[Path(__file__).resolve(),header,api,pool,D/'repair_seed_order_stage_01/binding.json',
    D/'repair_seed_order_eltwise_01/completion.json',D/'fused_preset_tiny_01/completion.json',
    D/'BNN_extended_native_menu_01.json',D.parents[1]/'scripts/flatland_benchmark.py',D/'resource_opportunity_census.py']
write(D/'native_resource_census_preparation_01.json',dict(passed=True,workspace=str(out),modified=['vpr/src/timing/h3d_native_resource_census.h','vpr/src/base/vpr_api.cpp'],
    source_sha256={str(path):sha(path) for path in files},
    question='Can a separately labeled actual native SB/CB/wire census match the independent auditor exactly, enabling later removal of repeated Python reconstruction/audit overhead while keeping actual FULL/STA and explicit final independent validation?',
    qualification='New independent source. Counter opt-in0 preserves old behavior. Per-pool seed policy/census flag are immutable environment identity and request/cache options, never silently inherited or changed mid-run. Counter is native assurance, never named an independent physical audit. Current cohort untouched; build and counter/default/policy/client binding checks pending. Fast acceptance consumer not implemented yet.'))
print(out,flush=True)
