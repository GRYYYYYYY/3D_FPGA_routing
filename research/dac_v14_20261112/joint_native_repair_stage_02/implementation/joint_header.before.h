#pragma once
/** @file Native restoration of a precisely specified joint repair transaction. */
#include <map>
#include <memory>
#include "h3d_current_sta_native_control.h"

namespace h3d_joint_native_repair {
/** @brief Recover copied trees with native searches, preserving original global trees.
 * The input explicitly specifies pruned sink sets, optional fixed target paths,
 * and query order. Occupancy follows every partial replacement; failed complete
 * transactions are never submitted as candidate routes. Output trees still
 * require independent FULL/STA and the selected acceptance policy.
 */
inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat) {
    const char* input = std::getenv("VPR_JOINT_NATIVE_REQUEST");
    if (!input || !*input) return;
    VTR_ASSERT(!is_flat);
    const char* output = std::getenv("VPR_JOINT_NATIVE_OUTPUT");
    VTR_ASSERT(output && *output);
    std::ifstream in(input);
    std::ofstream out(output);
    VTR_ASSERT(in.good() && out.good());
    out << std::setprecision(17);
    auto started = std::chrono::steady_clock::now();
    auto& routing = g_vpr_ctx.mutable_routing();
    const auto& device = g_vpr_ctx.device();
    const auto& graph = device.rr_graph;
    std::vector<int> original_occ;
    for (RRNodeId node : graph.nodes()) original_occ.push_back(routing.rr_node_route_inf[node].occ());
    std::map<ParentNetId, std::unique_ptr<RouteTree>> trees;
    CBRR connections(net_list, routing.net_rr_terminals, false);
    size_t ntrees;
    in >> ntrees;
    for (size_t i = 0; i < ntrees; ++i) {
        size_t number, npins;
        in >> number >> npins;
        ParentNetId net(number);
        VTR_ASSERT(routing.route_trees[net] && !trees.count(net));
        VTR_ASSERT(!net_list.net_is_global(net) && !net_list.net_is_ignored(net));
        auto tree = std::make_unique<RouteTree>(routing.route_trees[net].value(), net);
        for (size_t j = 0; j < npins; ++j) {
            int pin;
            in >> pin;
            VTR_ASSERT(pin > 0 && size_t(pin) < routing.net_rr_terminals[net].size());
            connections.restore_force_reroute_connection(net, routing.net_rr_terminals[net][pin]);
        }
        auto usage = tree->get_non_config_node_set_usage();
        if (!tree->prune(connections, &usage)) tree = std::make_unique<RouteTree>(net);
        connections.clear_force_reroute_for_net(net);
        tree->reload_timing();
        for (const auto& node : tree->all_nodes())
            out << "KEEP " << number << ' ' << size_t(node.inode) << ' ' << node.Tdel << ' ' << node.re_expand << '\n';
        trees.emplace(net, std::move(tree));
    }
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(routing.route_trees[net]->root(), -1);
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(tree->root(), 1);
    auto capacity_valid = [&]() {
        for (RRNodeId node : graph.nodes())
            if (routing.rr_node_route_inf[node].occ() > graph.node_capacity(node)) return false;
        return true;
    };
    VTR_ASSERT(capacity_valid());
    size_t presets;
    in >> presets;
    for (size_t i = 0; i < presets; ++i) {
        size_t number, nedges;
        int pin;
        in >> number >> pin >> nedges;
        ParentNetId net(number);
        auto& tree = *trees.at(net);
        RTExploredNode end;
        std::vector<RRNodeId> touched;
        for (size_t j = 0; j < nedges; ++j) {
            size_t u, v, sw;
            in >> u >> v >> sw;
            RREdgeId found = RREdgeId::INVALID();
            for (RREdgeId edge : graph.edge_range(RRNodeId(u)))
                if (graph.edge_sink_node(edge) == RRNodeId(v) && size_t(graph.rr_nodes().edge_switch(edge)) == sw) { found = edge; break; }
            VTR_ASSERT(found);
            if (!j) VTR_ASSERT(tree.find_by_rr_id(RRNodeId(u)));
            VTR_ASSERT(!tree.find_by_rr_id(RRNodeId(v)));
            routing.rr_node_route_inf[RRNodeId(v)].prev_edge = found;
            touched.push_back(RRNodeId(v));
            end.index = RRNodeId(v);
            end.prev_edge = found;
        }
        VTR_ASSERT(end.index == routing.net_rr_terminals[net][pin]);
        pathfinder_update_cost_from_route_tree(tree.root(), -1);
        tree.update_from_heap(&end, pin, nullptr, false);
        pathfinder_update_cost_from_route_tree(tree.root(), 1);
        for (RRNodeId node : touched) routing.rr_node_route_inf[node].prev_edge = RREdgeId::INVALID();
        VTR_ASSERT(capacity_valid());
    }
    NoOpLookahead lookahead;
    auto router = make_serial_connection_router(e_heap_type::FOUR_ARY_HEAP, device.grid, lookahead,
        graph.rr_nodes(), &graph, device.rr_rc_data, graph.rr_switch(), routing.rr_node_route_inf, false, 0);
    t_bb box;
    box.xmin = box.ymin = box.layer_min = 0;
    box.xmax = device.grid.width() - 1;
    box.ymax = device.grid.height() - 1;
    box.layer_max = device.grid.get_num_layers() - 1;
    size_t nqueries, finished = 0;
    in >> nqueries;
    bool transaction_ok = true;
    for (size_t i = 0; i < nqueries; ++i) {
        size_t number;
        int pin;
        float raw;
        in >> number >> pin >> raw;
        VTR_ASSERT(in.good());
        ParentNetId net(number);
        auto& tree = *trees.at(net);
        RRNodeId sink = routing.net_rr_terminals[net][pin];
        VTR_ASSERT(!tree.find_by_rr_id(sink));
        std::unordered_set<RRNodeId> retained;
        for (const auto& node : tree.all_nodes()) retained.insert(node.inode);
        auto begin = std::chrono::steady_clock::now();
        t_conn_cost_params costs;
        costs.criticality = std::min(opts.max_criticality, float(std::pow(std::max(double(raw) - (1.0 - opts.max_criticality), 0.0), opts.criticality_exp)));
        costs.astar_fac = costs.astar_offset = costs.post_target_prune_offset = 0.f;
        costs.post_target_prune_fac = 1.f;
        costs.bend_cost = opts.bend_cost;
        RouterStats stats;
        ConnectionParameters params(net, pin, false, std::unordered_map<RRNodeId, int>());
        RTExploredNode end;
        bool found = false, retry = false, feasible = false;
        router->clear_modified_rr_node_info();
        for (float pressure = 1.f; pressure <= 1.e8f; pressure *= 10.f) {
            costs.pres_fac = pressure;
            std::tie(found, retry, end) = router->timing_driven_route_connection_from_route_tree(tree.root(), sink, costs, box, stats, params);
            feasible = found;
            if (found) {
                RRNodeId node = sink;
                RREdgeId edge = end.prev_edge;
                std::unordered_set<RRNodeId> seen;
                while (!retained.count(node)) {
                    VTR_ASSERT(edge && seen.insert(node).second);
                    if (routing.rr_node_route_inf[node].occ() + 1 > graph.node_capacity(node)) feasible = false;
                    node = graph.edge_src_node(edge);
                    edge = routing.rr_node_route_inf[node].prev_edge;
                }
            }
            out << "ATTEMPT " << number << ' ' << pin << ' ' << pressure << ' ' << found << ' ' << feasible << '\n';
            if (feasible || !found || pressure >= 1.e8f || std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count() > 120.) break;
            router->reset_path_costs();
            router->clear_modified_rr_node_info();
        }
        if (feasible) {
            pathfinder_update_cost_from_route_tree(tree.root(), -1);
            tree.update_from_heap(&end, pin, nullptr, false);
            pathfinder_update_cost_from_route_tree(tree.root(), 1);
            feasible = capacity_valid();
        }
        router->reset_path_costs();
        out << "QUERY " << number << ' ' << pin << ' ' << feasible << ' ' << costs.criticality << ' '
            << stats.heap_pushes << ' ' << stats.heap_pops << ' '
            << std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count() << '\n';
        if (!feasible) { transaction_ok = false; break; }
        ++finished;
    }
    if (transaction_ok) {
        for (const auto& [net, tree] : trees) {
            VTR_ASSERT(tree->get_remaining_isinks().empty());
            for (const auto& node : tree->all_nodes())
                out << "NODE " << size_t(net) << ' ' << size_t(node.inode) << ' '
                    << (node.parent() ? int(size_t(node.parent()->inode)) : -1) << ' '
                    << (node.parent() ? int(size_t(node.parent_switch)) : -1) << ' '
                    << node.net_pin_index << ' ' << node.Tdel << '\n';
        }
    }
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(tree->root(), -1);
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(routing.route_trees[net]->root(), 1);
    for (RRNodeId node : graph.nodes()) VTR_ASSERT(routing.rr_node_route_inf[node].occ() == original_occ[size_t(node)]);
    out << "COMPLETE " << transaction_ok << ' ' << finished << ' ' << nqueries << ' '
        << std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count() << " occupancy_restored\n";
    VTR_LOG("JOINT_NATIVE_REPAIR complete=%d restored=%zu/%zu occupancy_restored=1\n", transaction_ok, finished, nqueries);
}
} // namespace h3d_joint_native_repair
