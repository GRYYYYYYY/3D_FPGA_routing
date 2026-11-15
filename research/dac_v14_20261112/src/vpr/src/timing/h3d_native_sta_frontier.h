#pragma once

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>

#include "globals.h"
#include "route_tree.h"
#include "timing_info.h"
#include "vpr_utils.h"
#include "vpr_net_pins_matrix.h"
#include "tatum/TimingGraph.hpp"
#include "tatum/echo_writer.hpp"

/** @brief Read-only final STA exporter; it never selects or changes routes. */
namespace h3d_native_sta_frontier {

/** @brief Write a JSON string, including control-character escaping. */
inline void string(std::ostream& out, const std::string& value) {
    constexpr char hex[] = "0123456789abcdef";
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u00" << hex[c >> 4] << hex[c & 15];
        else out << c;
    }
    out << '"';
}

/** @brief Preserve nonfinite values explicitly without invalid JSON numbers. */
inline void number(std::ostream& out, double value) {
    if (std::isfinite(value)) out << value;
    else if (std::isnan(value)) out << "\"nan\"";
    else out << (value > 0 ? "\"+inf\"" : "\"-inf\"");
}

/** @brief Write typed IDs; null means unavailable, never ID zero. */
template<typename Id>
inline void id(std::ostream& out, Id value) {
    if (value) out << size_t(value);
    else out << "null";
}

/** @brief Preserve every launch/capture domain slack tag for a mapped node. */
inline void tags(std::ostream& out, const tatum::TimingTags::tag_range values) {
    out << '[';
    bool first = true;
    for (const auto& tag : values) {
        if (!first) out << ',';
        first = false;
        out << "{\"launch\":";
        id(out, tag.launch_clock_domain());
        out << ",\"capture\":";
        id(out, tag.capture_clock_domain());
        out << ",\"slack_s\":";
        number(out, tag.time().value());
        out << '}';
    }
    out << ']';
}

/** @brief Export exact atom endpoints and untransformed native timing values. */
inline void atom(std::ostream& out, AtomPinId pin, const SetupHoldTimingInfo& timing) {
    const auto& context = g_vpr_ctx.atom();
    tatum::NodeId node = context.lookup().atom_pin_tnode(pin);
    out << "{\"id\":";
    id(out, pin);
    out << ",\"name\":";
    string(out, context.netlist().pin_name(pin));
    out << ",\"net\":";
    id(out, context.netlist().pin_net(pin));
    out << ",\"tnode_external\":";
    id(out, node);
    out << ",\"setup_slack_s\":";
    number(out, timing.setup_pin_slack(pin));
    out << ",\"setup_criticality_raw\":";
    number(out, timing.setup_pin_criticality(pin));
    out << ",\"hold_slack_s\":";
    number(out, timing.hold_pin_slack(pin));
    out << ",\"hold_criticality_raw\":";
    number(out, timing.hold_pin_criticality(pin));
    out << ",\"setup_tags\":";
    if (node) tags(out, timing.setup_analyzer()->setup_slacks(node));
    else out << "[]";
    out << ",\"hold_tags\":";
    if (node) tags(out, timing.hold_analyzer()->hold_slacks(node));
    else out << "[]";
    out << '}';
}

/**
 * @brief Export every routed-netlist pin after final native STA, when requested.
 *
 * VPR_H3D_FINAL_STA_TRACE names an output JSONL file. An unset/empty variable
 * returns before constructing lookups. Drivers, ignored/global nets, unmapped
 * pins and missing route trees are explicit. Raw criticality is not the router's
 * exponentiated/clamped criticality. Delay values come from native net_delay,
 * not a separate shortest-path model. No routing/timing state is modified.
 */
inline void write_if_requested(const Netlist<>& netlist,
                               const NetPinsMatrix<float>& net_delay,
                               const SetupHoldTimingInfo& timing,
                               bool is_flat) {
    const char* path = std::getenv("VPR_H3D_FINAL_STA_TRACE");
    if (!path || !*path) return;
    std::ofstream out(path);
    if (!out) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot open native STA frontier: %s", path);
    out << std::setprecision(std::numeric_limits<double>::max_digits10);
    out << "{\"type\":\"metadata\",\"schema\":1,\"time_unit\":\"seconds\",\"is_flat\":" << int(is_flat)
        << ",\"criticality\":\"native_raw_not_router_transformed\",\"nonfinite\":\"string_tokens\"}\n";
    const auto& route = g_vpr_ctx.routing();
    vtr::vector<ClusterPinId, std::vector<AtomPinId>> lookup;
    if (!is_flat) {
        const auto& atoms = g_vpr_ctx.atom();
        const auto& clustered = g_vpr_ctx.clustering().clb_nlist;
        lookup.resize(clustered.pins().size());
        for (ClusterNetId net : clustered.nets()) {
            AtomNetId atom_net = atoms.lookup().atom_net(net);
            if (!atom_net) continue;
            AtomPinId driver = atoms.netlist().net_driver(atom_net);
            ClusterPinId cluster_driver = clustered.net_driver(net);
            if (driver && cluster_driver) lookup[cluster_driver].push_back(driver);
        }
        // Final analysis follows pin-equivalence synchronization. Construct the
        // reverse mapping from atom sinks with the same remapping-aware helper
        // used by PostClusterDelayCalculator::atom_net_delay. The routing-time
        // ClusteredPinAtomPinsLookup assumes pre-synchronization pb_route pins.
        for (AtomPinId atom_pin : atoms.netlist().pins()) {
            if (atoms.netlist().pin_type(atom_pin) != PinType::SINK) continue;
            ClusterBlockId block = atoms.lookup().atom_clb(atoms.netlist().pin_block(atom_pin));
            const t_pb_graph_pin* graph_pin = atoms.lookup().atom_pin_pb_graph_pin(atom_pin);
            if (!block || !graph_pin) continue;
            const auto& pb_routes = clustered.block_pb(block)->pb_route;
            int pb_pin = graph_pin->pin_count_in_cluster;
            if (!pb_routes.count(pb_pin) || !pb_routes.at(pb_pin).atom_net_id) continue;
            ClusterNetId net;
            int logical_pin, net_pin;
            std::tie(net, logical_pin, net_pin) = find_pb_route_clb_input_net_pin(block, pb_pin);
            if (!net || net_pin < 0) continue;
            ClusterPinId pin = *(clustered.net_pins(net).begin() + net_pin);
            VTR_ASSERT(clustered.pin_block(pin) == block);
            VTR_ASSERT(atoms.lookup().atom_net(net) == atoms.netlist().pin_net(atom_pin));
            lookup[pin].push_back(atom_pin);
        }
    }
    for (tatum::DomainId domain : timing.timing_constraints()->clock_domains()) {
        out << "{\"type\":\"domain\",\"id\":";
        id(out, domain);
        out << ",\"name\":";
        string(out, timing.timing_constraints()->clock_domain_name(domain));
        out << "}\n";
    }
    size_t rows = 0;
    for (ParentNetId net : netlist.nets()) {
        bool has_tree = size_t(net) < route.route_trees.size() && route.route_trees[net].has_value();
        std::vector<RRNodeId> tree_pins(netlist.net_pins(net).size(), RRNodeId::INVALID());
        if (has_tree) {
            tree_pins[0] = route.route_trees[net]->root().inode;
            // Analysis-loaded trees need not have find_by_isink's optional
            // lookup. Read explicit pin indices, as load_net_delay does.
            for (const auto& node : route.route_trees[net]->all_nodes()) {
                if (node.net_pin_index <= 0) continue;
                VTR_ASSERT(size_t(node.net_pin_index) < tree_pins.size());
                VTR_ASSERT(!tree_pins[node.net_pin_index]);
                tree_pins[node.net_pin_index] = node.inode;
            }
        }
        for (ParentPinId pin : netlist.net_pins(net)) {
            int index = netlist.pin_net_index(pin);
            VTR_ASSERT(index >= 0);
            out << "{\"type\":\"pin\",\"net\":" << size_t(net) << ",\"pin\":" << index
                << ",\"pin_id\":" << size_t(pin) << ",\"net_name\":";
            string(out, netlist.net_name(net));
            out << ",\"pin_name\":";
            string(out, netlist.pin_name(pin));
            out << ",\"driver\":" << int(pin == netlist.net_driver(net))
                << ",\"ignored\":" << int(netlist.net_is_ignored(net))
                << ",\"global\":" << int(netlist.net_is_global(net))
                << ",\"native_net_delay_s\":";
            number(out, net_delay[net][index]);
            out << ",\"terminal_rr\":";
            if (size_t(net) < route.net_rr_terminals.size()
                && size_t(index) < route.net_rr_terminals[net].size()) id(out, route.net_rr_terminals[net][index]);
            else out << "null";
            out << ",\"route_tree_present\":" << int(has_tree) << ",\"tree_rr\":";
            id(out, tree_pins[index]);
            out << ",\"setup_criticality_raw\":";
            if (is_flat) number(out, timing.setup_pin_criticality(convert_to_atom_pin_id(pin)));
            else {
                float criticality = 0.;
                for (AtomPinId atom_pin : lookup[convert_to_cluster_pin_id(pin)])
                    criticality = std::max(criticality, timing.setup_pin_criticality(atom_pin));
                number(out, criticality);
            }
            out << ",\"setup_slack_s\":";
            if (is_flat) number(out, timing.setup_pin_slack(convert_to_atom_pin_id(pin)));
            else {
                float slack = std::numeric_limits<float>::infinity();
                for (AtomPinId atom_pin : lookup[convert_to_cluster_pin_id(pin)])
                    slack = std::min(slack, timing.setup_pin_slack(atom_pin));
                number(out, slack);
            }
            out << ",\"atoms\":[";
            bool first = true;
            if (is_flat) atom(out, convert_to_atom_pin_id(pin), timing);
            else for (AtomPinId atom_pin : lookup[convert_to_cluster_pin_id(pin)]) {
                if (!first) out << ',';
                first = false;
                atom(out, atom_pin, timing);
            }
            out << "]}\n";
            ++rows;
        }
    }
    size_t endpoints = 0;
    const auto& graph = *timing.timing_graph();
    for (tatum::NodeId node : graph.nodes()) {
        if (graph.node_type(node) != tatum::NodeType::SINK) continue;
        AtomPinId pin = g_vpr_ctx.atom().lookup().tnode_atom_pin(node);
        out << "{\"type\":\"endpoint\",\"node\":";
        id(out, node);
        out << ",\"atom_pin\":";
        id(out, pin);
        out << ",\"name\":";
        if (pin) string(out, g_vpr_ctx.atom().netlist().pin_name(pin));
        else out << "null";
        out << ",\"setup_tags\":";
        tags(out, timing.setup_analyzer()->setup_slacks(node));
        out << ",\"hold_tags\":";
        tags(out, timing.hold_analyzer()->hold_slacks(node));
        out << "}\n";
        ++endpoints;
    }
    auto least = timing.least_slack_critical_path();
    auto longest = timing.longest_critical_path();
    out << "{\"type\":\"timing_metrics\",\"least_slack_CPD_s\":";
    number(out, least.delay().value());
    out << ",\"least_slack_s\":";
    number(out, least.slack().value());
    out << ",\"longest_CPD_s\":";
    number(out, longest.delay().value());
    out << ",\"setup_TNS_s\":";
    number(out, timing.setup_total_negative_slack());
    out << ",\"hold_TNS_s\":";
    number(out, timing.hold_total_negative_slack());
    out << ",\"least_slack_launch_domain\":";
    id(out, least.launch_domain());
    out << ",\"least_slack_capture_domain\":";
    id(out, least.capture_domain());
    out << ",\"least_slack_endpoint\":";
    id(out, least.endpoint());
    out << "}\n";
    std::ofstream constraints(std::string(path) + ".constraints.echo");
    constraints << std::setprecision(std::numeric_limits<double>::max_digits10);
    tatum::write_timing_constraints(constraints, *timing.timing_constraints());
    constraints.close();
    if (!constraints) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot finish native STA constraint export: %s", path);
    out << "{\"type\":\"complete\",\"pin_rows\":" << rows << ",\"endpoint_rows\":" << endpoints << "}\n";
    out.close();
    if (!out) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot finish native STA frontier: %s", path);
    VTR_LOG("H3D_FINAL_STA_TRACE pins=%zu path=%s\n", rows, path);
}
} // namespace h3d_native_sta_frontier
