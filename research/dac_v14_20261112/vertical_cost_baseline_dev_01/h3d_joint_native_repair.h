#pragma once
/** @file Native restoration of a precisely specified joint repair transaction. */
#include <map>
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <functional>
#include <exception>
#include <set>
#include <unordered_set>
#include <memory>
#include "h3d_current_sta_native_control.h"

namespace h3d_joint_native_repair {
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

/** @brief Recover copied trees with native searches, preserving original global trees.
 * The input explicitly specifies pruned sink sets, optional fixed target paths,
 * and query order. Occupancy follows every partial replacement; failed complete
 * transactions are never submitted as candidate routes. Output trees still
 * require independent FULL/STA and the selected acceptance policy. The opt-in
 * failure-release mode relaxes only a failed net domain before any tree update;
 * capacity and the complete transaction gates remain mandatory.
 */
inline void run_if_requested(const Netlist<>& net_list, const t_router_opts& opts, bool is_flat,
                             const std::function<void()>& candidate_observer = {}) {
    const char* input = std::getenv("VPR_JOINT_NATIVE_REQUEST");
    if (!input || !*input) return;
    VTR_ASSERT(!is_flat);
    const char* output = std::getenv("VPR_JOINT_NATIVE_OUTPUT");
    VTR_ASSERT(output && *output);
    std::ifstream in(input);
    std::ofstream out(output);
    VTR_ASSERT(in.good() && out.good());
    out << std::setprecision(17);
    const char* objective_text = std::getenv("VPR_JOINT_NATIVE_OBJECTIVE");
    const std::string objective = objective_text ? objective_text : "weighted_soft";
    VTR_ASSERT(objective == "weighted_soft" || objective == "weighted_capacity"
               || objective == "physical_soft" || objective == "physical_capacity");
    const bool physical = objective == "physical_soft" || objective == "physical_capacity";
    const bool hard_capacity = objective == "weighted_capacity" || objective == "physical_capacity";
    // Independent simple baseline: congestion preference only, never Tdel.
    const char* vertical_cost_text = std::getenv("VPR_JOINT_NATIVE_VERTICAL_COST_WEIGHT");
    float vertical_cost_weight = 0.f;
    if (vertical_cost_text && *vertical_cost_text) {
        char* end = nullptr;
        errno = 0;
        vertical_cost_weight = std::strtof(vertical_cost_text, &end);
        if (errno || end == vertical_cost_text || *end || !std::isfinite(vertical_cost_weight)
            || !(vertical_cost_weight == 0.f || vertical_cost_weight == .5f
                 || vertical_cost_weight == 1.f || vertical_cost_weight == 2.f))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unregistered vertical cost weight");
    }
    if (vertical_cost_weight > 0.f && physical)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Vertical cost baseline requires weighted objective");
    t_h3d_connection_guide vertical_cost_guide;
    vertical_cost_guide.edge_encoding = true;
    vertical_cost_guide.miss_weight = vertical_cost_weight;
    // Empty preferred set charges every configurable crossing in edge encoding.
    // Defaults leave timing penalty, bounded-critical behavior and domains off.

    out << "MODE " << objective << '\n';
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
    }
    auto started = std::chrono::steady_clock::now();
    auto& routing = g_vpr_ctx.mutable_routing();
    const auto& device = g_vpr_ctx.device();
    const auto& graph = device.rr_graph;
    std::unordered_set<ParentNetId> vertical_domain_nets;
    std::ofstream vertical_trace;
    const char* vertical_file = std::getenv("VPR_JOINT_NATIVE_REUSE_CROSSINGS");
    if (vertical_file && *vertical_file) {
        std::ifstream selected(vertical_file);
        size_t count;
        if (!(selected >> count) || count == 0) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Empty vertical-domain net list");
        for (size_t i = 0; i < count; ++i) {
            size_t number;
            if (!(selected >> number) || number >= net_list.nets().size()
                || !vertical_domain_nets.insert(ParentNetId(number)).second) {
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid or duplicate vertical-domain net");
            }
        }
        std::string extra;
        if (selected >> extra) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Trailing vertical-domain net list fields");
        const char* trace_path = std::getenv("VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE");
        if (!trace_path || !*trace_path) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Vertical-domain trace path required");
        vertical_trace.open(trace_path);
        if (!vertical_trace) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot open vertical-domain trace");
    }
    const char* release_text = std::getenv("VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE");
    const bool release_failed_domain = release_text && std::string(release_text) == "1";
    if (release_text && *release_text && std::string(release_text) != "0"
        && std::string(release_text) != "1") {
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid domain-failure-release flag");
    }
    // Optional whole-net crossing-source restriction, independent of retained-tree reuse.
    std::map<ParentNetId, std::unordered_set<RRNodeId>> explicit_crossing_sources;
    const char* explicit_file = std::getenv("VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS");
    if (explicit_file && *explicit_file) {
        if (vertical_domain_nets.empty() || release_failed_domain)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Explicit crossing sources require selected nets and no failure release");
        std::ifstream selected(explicit_file);
        size_t count;
        if (!(selected >> count) || count != vertical_domain_nets.size())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Explicit crossing net count mismatch");
        for (size_t i = 0; i < count; ++i) {
            size_t number, nodes;
            if (!(selected >> number >> nodes) || number >= net_list.nets().size() || nodes == 0
                || !vertical_domain_nets.count(ParentNetId(number)) || explicit_crossing_sources.count(ParentNetId(number)))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid explicit crossing net");
            auto& allowed = explicit_crossing_sources[ParentNetId(number)];
            for (size_t j = 0; j < nodes; ++j) {
                size_t source;
                if (!(selected >> source) || source >= graph.num_nodes() || !allowed.insert(RRNodeId(source)).second)
                    VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Invalid explicit crossing source");
            }
        }
        std::string extra;
        if (selected >> extra) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Trailing explicit crossing fields");
    }
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
    if (!vertical_domain_nets.empty() && presets != 0) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Crossing reuse requires free native paths, without presets");
    for (ParentNetId net : vertical_domain_nets) {
        if (!trees.count(net)) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Vertical-domain net is outside transaction scope");
    }
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
        // A null guide at zero keeps the original arithmetic and control path.
        if (vertical_cost_weight > 0.f) costs.h3d_guide = &vertical_cost_guide;
        if (physical) {
            costs.criticality = 1.f;
            costs.bend_cost = 0.f;
        }
        RouterStats stats;
        const std::unordered_map<RRNodeId, int> no_choke_points;
        ConnectionParameters params(net, pin, false, no_choke_points);
        params.repair_seed_order_ = seed_order_code;
        params.repair_seed_trace_ = seed_trace.is_open() ? &seed_trace : nullptr;
        std::unordered_set<RRNodeId> allowed_crossing_sources;
        if (vertical_domain_nets.count(net)) {
            if (explicit_crossing_sources.count(net)) {
                allowed_crossing_sources = explicit_crossing_sources.at(net);
            } else {
            for (const auto& node : tree.all_nodes()) {
                if (node.parent() && graph.node_layer_low(node.parent()->inode) != graph.node_layer_low(node.inode)) {
                    allowed_crossing_sources.insert(node.parent()->inode);
                }
            }
            }
            params.repair_allowed_crossing_sources_ = &allowed_crossing_sources;
            vertical_trace << "ALLOW " << number << ' ' << pin << ' ' << allowed_crossing_sources.size();
            std::set<RRNodeId> ordered(allowed_crossing_sources.begin(), allowed_crossing_sources.end());
            for (RRNodeId source : ordered) vertical_trace << ' ' << size_t(source);
            vertical_trace << '\n';
        }
        std::vector<uint8_t> forbidden;
        if (hard_capacity) {
            forbidden.resize(graph.num_nodes(), 0);
            for (RRNodeId node : graph.nodes()) {
                forbidden[size_t(node)] = retained.count(node)
                    || routing.rr_node_route_inf[node].occ() >= graph.node_capacity(node);
            }
            params.repair_forbidden_nodes_ = &forbidden;
        }
        RTExploredNode end;
        bool found = false, retry = false, feasible = false;
        router->clear_modified_rr_node_info();
        // Failed searches have not committed a branch or changed occupancy.
        // Retry only this net without its domain, preserving prior restorations.
        const int search_passes = release_failed_domain && params.repair_allowed_crossing_sources_ ? 2 : 1;
        for (int pass = 0; pass < search_passes; ++pass) {
            if (pass) {
                router->reset_path_costs();
                router->clear_modified_rr_node_info();
                params.repair_allowed_crossing_sources_ = nullptr;
                const size_t erased = vertical_domain_nets.erase(net);
                VTR_ASSERT(erased == 1);
                vertical_trace << "RELEASE " << number << ' ' << pin << " domain_search_infeasible\n";
                out << "DOMAIN_RELEASE " << number << ' ' << pin << '\n';
            }
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
            if (search_trace.is_open()) {
                // The returned RTExploredNode intentionally omits cost fields.
                // Read the real sink labels before reset_path_costs clears them.
                search_trace << "COST " << number << ' ' << pin << ' ' << seed_order_code
                    << ' ' << pass << ' ' << pressure << ' ' << found << ' ' << feasible
                    << ' ' << routing.rr_node_route_inf[sink].path_cost
                    << ' ' << routing.rr_node_route_inf[sink].backward_path_cost
                    << ' ' << costs.criticality << ' ' << costs.astar_fac << '\n';
            }
            out << "ATTEMPT " << number << ' ' << pin << ' ' << pressure << ' ' << found << ' ' << feasible << '\n';
            if (feasible || !found || physical || hard_capacity || pressure >= 1.e8f || std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count() > 120.) break;
            router->reset_path_costs();
            router->clear_modified_rr_node_info();
        }
            if (feasible) break;
        }
        if (!feasible) {
            out << "FAIL_TARGET " << number << ' ' << pin << ' ' << size_t(sink) << ' ' << costs.pres_fac << '\n';
            if (found) {
                RRNodeId node = sink;
                RREdgeId edge = end.prev_edge;
                std::unordered_set<RRNodeId> seen;
                while (!retained.count(node)) {
                    VTR_ASSERT(edge && seen.insert(node).second);
                    RRNodeId parent = graph.edge_src_node(edge);
                    auto index = graph.node_cost_index(node);
                    out << "FAIL_EDGE " << size_t(parent) << ' ' << size_t(node) << ' '
                        << size_t(graph.rr_nodes().edge_switch(edge)) << ' '
                        << routing.rr_node_route_inf[node].occ() << ' ' << graph.node_capacity(node) << ' '
                        << device.rr_indexed_data[index].base_cost << ' ' << routing.rr_node_route_inf[node].acc_cost << ' '
                        << get_rr_cong_cost(node, costs.pres_fac) << '\n';
                    node = parent;
                    edge = routing.rr_node_route_inf[node].prev_edge;
                }
            }
            for (RRNodeId node : graph.nodes()) {
                int occ = routing.rr_node_route_inf[node].occ();
                if (occ) out << "OCC " << size_t(node) << ' ' << occ << '\n';
            }
        }
        if (feasible) {
            pathfinder_update_cost_from_route_tree(tree.root(), -1);
            tree.update_from_heap(&end, pin, nullptr, false);
            pathfinder_update_cost_from_route_tree(tree.root(), 1);
            feasible = capacity_valid();
            if (params.repair_allowed_crossing_sources_) {
                for (const auto& node : tree.all_nodes()) {
                    if (node.parent() && graph.node_layer_low(node.parent()->inode) != graph.node_layer_low(node.inode)
                        && !allowed_crossing_sources.count(node.parent()->inode)) {
                        feasible = false;
                    }
                }
                vertical_trace << "CHECK " << number << ' ' << pin << ' ' << feasible << '\n';
            }
        }
        router->reset_path_costs();
        out << "QUERY " << number << ' ' << pin << ' ' << feasible << ' ' << costs.criticality << ' '
            << stats.heap_pushes << ' ' << stats.heap_pops << ' '
            << std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count() << '\n';
        if (!feasible) { transaction_ok = false; break; }
        ++finished;
    }
    {
        for (const auto& [net, tree] : trees) {
            if (transaction_ok) VTR_ASSERT(tree->get_remaining_isinks().empty());
            for (const auto& node : tree->all_nodes())
                out << "NODE " << size_t(net) << ' ' << size_t(node.inode) << ' '
                    << (node.parent() ? int(size_t(node.parent()->inode)) : -1) << ' '
                    << (node.parent() ? int(size_t(node.parent_switch)) : -1) << ' '
                    << node.net_pin_index << ' ' << node.Tdel << ' ' << node.re_expand << '\n';
        }
    }
    std::exception_ptr candidate_error;
    if (transaction_ok && candidate_observer) {
        try {
            ScopedCandidateTrees installed;
            installed.install(trees);
            candidate_observer();
        } catch (...) {
            candidate_error = std::current_exception();
        }
    }
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(tree->root(), -1);
    for (const auto& [net, tree] : trees) pathfinder_update_cost_from_route_tree(routing.route_trees[net]->root(), 1);
    for (RRNodeId node : graph.nodes()) VTR_ASSERT(routing.rr_node_route_inf[node].occ() == original_occ[size_t(node)]);
    out << "COMPLETE " << transaction_ok << ' ' << finished << ' ' << nqueries << ' '
        << std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count() << " occupancy_restored\n";
    if (vertical_trace.is_open()) vertical_trace << "COMPLETE " << transaction_ok << " occupancy_restored\n";
    VTR_LOG("JOINT_NATIVE_REPAIR complete=%d restored=%zu/%zu occupancy_restored=1\n", transaction_ok, finished, nqueries);
    if (candidate_error) std::rethrow_exception(candidate_error);
}
} // namespace h3d_joint_native_repair
