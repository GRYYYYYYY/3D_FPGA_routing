#include "h3d_routing.h"

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <chrono>
#include <memory>
#include <numeric>
#include <set>
#include <string>
#include <unordered_map>

#include "globals.h"
#include "h3d_partition_dp.h"
#include "h3d_fast_plan.h"
#include "h3d_crossing.h"
#include "route_common.h"
#include "route_tree.h"
#include "vpr_error.h"
#include "vtr_log.h"

namespace {

/** @brief Strictly parse a finite nonnegative experiment setting. */
float read_number(const char* name, float default_value) {
    const char* text = std::getenv(name);
    if (!text)
        return default_value;
    errno = 0;
    char* end = nullptr;
    float parsed = std::strtof(text, &end);
    if (errno || end == text || *end || !std::isfinite(parsed) || parsed < 0.f)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "%s must be finite and nonnegative, got '%s'", name, text);
    return parsed;
}

/** @brief Explicit experimental modes; the detailed connection search is always VPR's. */
enum class e_h3d_mode { OFF,
                        CANDIDATES,
                        STATIC,
                        DYNAMIC,
                        DYNAMIC_WHOLE,
                        DYNAMIC_SUBTREE };

/** @brief Immutable per-process settings, recorded at the first routing iteration. */
struct t_settings {
    bool use_scc = false;              ///< Exact SCC reachability with geometric costs instead of full BFS distances.
    e_h3d_mode mode = e_h3d_mode::OFF; ///< Candidate-planning ablation.
    size_t candidates = 8;             ///< Diverse preferred candidates per remote terminal.
    float miss_weight = 2.f;           ///< Additional relative CHANZ cost outside the preference set.
    float opening_weight = 8.f;        ///< Channel-opening weight in hop-cost planning units.
    bool delay_cost = false;
    size_t delay_budget = 4096;
    float min_criticality = 0.f;
    bool edge_encoding = false;       ///< Prefer actual crossing-edge sources in imported single-layer-node graphs.
};

/** @brief Parse modes exactly; misspellings must not silently run the baseline. */
const t_settings& settings() {
    static const t_settings value = [] {
        t_settings result;
        const char* env = std::getenv("VPR_H3D_MODE");
        std::string mode = env ? env : "off";
        if (mode == "off")
            result.mode = e_h3d_mode::OFF;
        else if (mode == "candidates")
            result.mode = e_h3d_mode::CANDIDATES;
        else if (mode == "static")
            result.mode = e_h3d_mode::STATIC;
        else if (mode == "dynamic")
            result.mode = e_h3d_mode::DYNAMIC;
        else if (mode == "dynamic_whole")
            result.mode = e_h3d_mode::DYNAMIC_WHOLE;
        else if (mode == "dynamic_subtree")
            result.mode = e_h3d_mode::DYNAMIC_SUBTREE;
        else
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unknown VPR_H3D_MODE '%s'", mode.c_str());
        float candidates = read_number("VPR_H3D_CANDIDATES", 8.f);
        if (candidates < 1.f || candidates > 64.f || std::floor(candidates) != candidates)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CANDIDATES must be an integer in [1,64]");
        result.candidates = static_cast<size_t>(candidates);
        result.miss_weight = read_number("VPR_H3D_MISS_WEIGHT", 2.f);
        result.opening_weight = read_number("VPR_H3D_OPENING_WEIGHT", 8.f);
        const char* search = std::getenv("VPR_H3D_REACHABILITY");
        std::string reachability = search ? search : "bfs";
        if (reachability != "bfs" && reachability != "scc")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_REACHABILITY must be bfs or scc");
        result.use_scc = reachability == "scc";
        const char* encoding_env = std::getenv("VPR_H3D_GRAPH_ENCODING");
        std::string encoding = encoding_env ? encoding_env : "native";
        if (encoding != "native" && encoding != "edge")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_GRAPH_ENCODING must be native or edge");
        result.edge_encoding = encoding == "edge";
        if (result.edge_encoding && !result.use_scc)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Edge encoding requires SCC planning");
        const char* score = std::getenv("VPR_H3D_CANDIDATE_COST");
        std::string cost = score ? score : "geometry";
        if (cost != "geometry" && cost != "delay")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CANDIDATE_COST must be geometry or delay");
        result.delay_cost = cost == "delay";
        float budget = read_number("VPR_H3D_DELAY_BUDGET", 4096.f);
        if (budget < 1.f || budget > 1000000.f || std::floor(budget) != budget)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DELAY_BUDGET must be an integer in [1,1000000]");
        result.delay_budget = size_t(budget);
        result.min_criticality = read_number("VPR_H3D_MIN_CRITICALITY", 0.f);
        if (result.min_criticality > 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_MIN_CRITICALITY must be in [0,1]");
        if ((result.delay_cost || result.min_criticality > 0.f) && !result.use_scc)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Delay scoring and critical selection require SCC planning");
        return result;
    }();
    return value;
}

/** @brief Persistent exact reachability caches and per-net surrogate plans.
 *
 * Searches stay on the starting die and stop on first entering CHANZ. A forward
 * source search and reverse sink search therefore certify a real single-crossing
 * walk. Congestion never removes candidates. Reverse CSR is only an auxiliary
 * index of the unchanged RRG; it does not create legal reverse routing edges.
 */
class H3dPlanner {
  public:
    /** @brief Build a reverse-edge CSR and identify native physical channels. */
    H3dPlanner() {
        auto start = std::chrono::steady_clock::now();
        const auto& graph = g_vpr_ctx.device().rr_graph;
        size_t count = graph.num_nodes();
        z_index_.resize(count, -1);
        for (RRNodeId node : graph.nodes()) {
            if (settings().edge_encoding ? h3d_crossing_entry(graph, node) : graph.node_type(node) == e_rr_type::CHANZ) {
                z_index_[node] = channels_.size();
                channels_.push_back(node);
            }
        }
        if (settings().use_scc) {
            fast_plan_ = std::make_unique<H3dFastPlan>(graph, settings().delay_cost, settings().delay_budget, settings().edge_encoding);
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            VTR_LOG("H3D_INIT reachability=scc channels=%zu init_seconds=%.6f\n", channels_.size(), planning_seconds_);
            VTR_LOG("H3D_CONFIG candidate_cost=%s min_criticality=%g delay_budget=%zu\n",
                    settings().delay_cost ? "delay" : "geometry", settings().min_criticality, settings().delay_budget);
            VTR_LOG("H3D_GRAPH_ENCODING %s graph_unchanged=1\n", settings().edge_encoding ? "edge" : "native");
            return;
        }
        reverse_start_.resize(count, 0);
        reverse_count_.resize(count, 0);
        distance_.resize(count, -1);
        for (RRNodeId node : graph.nodes())
            for (auto edge : graph.node_out_edges(node))
                ++reverse_count_[graph.edge_sink_node(node, edge)];
        size_t total = 0;
        for (RRNodeId node : graph.nodes()) {
            reverse_start_[node] = total;
            total += reverse_count_[node];
        }
        reverse_edges_.resize(total);
        auto cursor = reverse_start_;
        for (RRNodeId node : graph.nodes())
            for (auto edge : graph.node_out_edges(node))
                reverse_edges_[cursor[graph.edge_sink_node(node, edge)]++] = node;
        if (channels_.empty())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes require native CHANZ; legacy encodings need an explicit adapter");
        planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        VTR_LOG("H3D_INIT channels=%zu reverse_edges=%zu candidates=%zu miss_weight=%g opening_weight=%g init_seconds=%.6f\n",
                channels_.size(), total, settings().candidates, settings().miss_weight, settings().opening_weight, planning_seconds_);
    }

    /** @brief Save old channels so replanning does not discard already used choices. */
    void capture(ParentNetId net) {
        current_channels_.clear();
        const auto& tree = g_vpr_ctx.routing().route_trees[net];
        if (tree)
            for (const auto& node : tree->all_nodes())
                if (z_index_[node.inode] >= 0)
                    current_channels_.insert(z_index_[node.inode]);
    }

    /** @brief Build source/sink feasible sets, then rank independently or solve the hierarchy. */
    void plan(ParentNetId net, float pres_fac, const std::vector<float>& criticality) {
        if (settings().mode == e_h3d_mode::STATIC && guides_.contains(net))
            return;
        auto start = std::chrono::steady_clock::now();
        if (fast_plan_) {
            std::vector<RRNodeId> previous;
            for (size_t c : current_channels_)
                previous.push_back(channels_[c]);
            auto result = fast_plan_->plan(net, criticality, previous, pres_fac, settings().candidates,
                                           settings().opening_weight, settings().miss_weight,
                                           settings().mode != e_h3d_mode::CANDIDATES, settings().min_criticality);
            ++plans_;
            groups_ += result.groups;
            no_candidate_ += result.no_candidate;
            guides_[net] = std::move(result.guides);
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            return;
        }
        const auto& graph = g_vpr_ctx.device().rr_graph;
        const auto& terminals = g_vpr_ctx.routing().net_rr_terminals[net];
        RRNodeId source = terminals[0];
        auto& guides = guides_[net];
        guides.assign(terminals.size(), {});
        std::vector<int> remote_pins;
        for (size_t pin = 1; pin < terminals.size(); ++pin)
            if (graph.node_layer_low(source) != graph.node_layer_low(terminals[pin]))
                remote_pins.push_back(pin);
        if (remote_pins.empty()) {
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            return;
        }
        ++plans_;
        const auto& from_source = distances_(source, false);
        std::set<size_t> pool;
        std::vector<double> opening(channels_.size(), 0.);
        for (size_t c = 0; c < channels_.size(); ++c) {
            RRNodeId node = channels_[c];
            float base = g_vpr_ctx.device().rr_indexed_data[graph.node_cost_index(node)].base_cost;
            double congestion = get_rr_cong_cost(node, pres_fac) / std::max(base, 1.e-20f);
            opening[c] = std::max(0, from_source[c]) + settings().opening_weight * congestion;
        }
        for (int pin : remote_pins) {
            const auto& to_sink = distances_(terminals[pin], true);
            std::vector<std::pair<double, size_t>> ranked;
            for (size_t c = 0; c < channels_.size(); ++c) {
                if (from_source[c] < 0 || to_sink[c] < 0)
                    continue;
                double branch = to_sink[c] * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * from_source[c];
                ranked.emplace_back(opening[c] + branch, c);
            }
            std::sort(ranked.begin(), ranked.end());
            std::set<size_t> chosen;
            if (!ranked.empty()) {
                chosen.insert(ranked.front().second);
                // Retain cost quality while spreading the alternatives across
                // distinct XY sites. Channels at one site can still differ in
                // directed access and are kept when fewer sites are available.
                size_t shortlist = std::min(ranked.size(), settings().candidates * 8);
                while (chosen.size() < settings().candidates && chosen.size() < ranked.size()) {
                    double best_score = -1.;
                    size_t best = ranked.front().second;
                    for (size_t i = 0; i < shortlist; ++i) {
                        size_t c = ranked[i].second;
                        if (chosen.contains(c)) continue;
                        int spread = std::numeric_limits<int>::max();
                        for (size_t previous : chosen) {
                            int distance = std::abs(graph.node_xlow(channels_[c]) - graph.node_xlow(channels_[previous]))
                                           + std::abs(graph.node_ylow(channels_[c]) - graph.node_ylow(channels_[previous]));
                            spread = std::min(spread, distance);
                        }
                        double score = (1. + spread) / (1. + ranked[i].first - ranked.front().first);
                        if (score > best_score) {
                            best_score = score;
                            best = c;
                        }
                    }
                    if (best_score < 0.) break;
                    chosen.insert(best);
                }
            }
            for (size_t c : current_channels_)
                if (from_source[c] >= 0 && to_sink[c] >= 0)
                    chosen.insert(c);
            if (chosen.empty()) {
                ++no_candidate_;
                continue;
            }
            pool.insert(chosen.begin(), chosen.end());
            for (size_t c : chosen)
                guides[pin].preferred.push_back(channels_[c]);
            guides[pin].miss_weight = settings().miss_weight;
        }
        if (settings().mode != e_h3d_mode::CANDIDATES) {
            std::vector<t_h3d_plan_leaf> leaves;
            for (int pin : remote_pins) {
                if (guides[pin].preferred.empty()) continue;
                RRNodeId sink = terminals[pin];
                const auto& to_sink = distances_(sink, true);
                t_h3d_plan_leaf leaf{pin, graph.node_xlow(sink), graph.node_ylow(sink), {}};
                for (size_t c : pool)
                    if (from_source[c] >= 0 && to_sink[c] >= 0)
                        leaf.candidates.push_back({c, to_sink[c] * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * from_source[c]});
                leaves.push_back(std::move(leaf));
            }
            auto result = h3d_plan_partition(leaves, opening);
            if (std::isfinite(result.cost)) {
                groups_ += result.groups;
                for (const auto& [pin, channel] : result.assignment)
                    guides[pin].preferred = {channels_[channel]};
            }
        }
        for (auto& guide : guides)
            std::sort(guide.preferred.begin(), guide.preferred.end());
        planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    }

    /** @brief Read the stable guide storage while a net's sink searches execute. */
    const t_h3d_connection_guide* guide(ParentNetId net, int pin) const {
        auto found = guides_.find(net);
        if (found == guides_.end() || found->second.at(pin).preferred.empty())
            return nullptr;
        return &found->second[pin];
    }

    /** @brief Report cumulative preprocessing/search overhead separately from native A*. */
    void log() const {
        VTR_LOG("H3D_PLAN plans=%zu groups=%zu bfs_nodes=%zu cache_entries=%zu no_candidate=%zu fallback=%zu planning_seconds=%.6f\n",
                plans_, groups_, bfs_nodes_, forward_cache_.size() + reverse_cache_.size(), no_candidate_, fallbacks_, planning_seconds_);
        VTR_LOG("H3D_TREE guided_paths=%zu preferred_paths=%zu rollbacks=%zu\n", guided_observations_, preferred_observations_, rollbacks_);
        if (fast_plan_) fast_plan_->log();
    }

    /** @brief Count an explicit fallback retry. */
    void fallback() { ++fallbacks_; }

    /** @brief Measure preferences on each actual source-to-sink route-tree path. */
    void observe(ParentNetId net) {
        auto found = guides_.find(net);
        const auto& tree = g_vpr_ctx.routing().route_trees[net];
        if (found == guides_.end() || !tree) return;
        for (size_t pin = 1; pin < found->second.size(); ++pin) {
            const auto& preferred = found->second[pin].preferred;
            if (preferred.empty()) continue;
            auto node = tree->find_by_isink(pin);
            if (!node) continue;
            ++guided_observations_;
            while (node) {
                auto parent = node->parent();
                const auto& graph = g_vpr_ctx.device().rr_graph;
                bool eligible = !settings().edge_encoding || (parent && h3d_crosses_layers(graph, parent->inode, node->inode));
                RRNodeId identity = settings().edge_encoding && parent ? parent->inode : node->inode;
                if (eligible && std::binary_search(preferred.begin(), preferred.end(), identity)) {
                    ++preferred_observations_;
                    break;
                }
                node = node->parent();
            }
        }
    }

    /** @brief Count restoration of a complete prior tree and its bookkeeping. */
    void rollback() { ++rollbacks_; }

  private:
    /** @brief Cache directed same-die BFS distances to every first-crossing channel. */
    const std::vector<int>& distances_(RRNodeId terminal, bool reverse) {
        auto& cache = reverse ? reverse_cache_ : forward_cache_;
        auto found = cache.find(terminal);
        if (found != cache.end()) return found->second;
        const auto& graph = g_vpr_ctx.device().rr_graph;
        int layer = graph.node_layer_low(terminal);
        std::fill(distance_.begin(), distance_.end(), -1);
        std::vector<RRNodeId> queue{terminal};
        distance_[terminal] = 0;
        std::vector<int> result(channels_.size(), -1);
        for (size_t head = 0; head < queue.size(); ++head) {
            RRNodeId current = queue[head];
            ++bfs_nodes_;
            auto visit = [&](RRNodeId next) {
                if (distance_[next] >= 0) return;
                if (z_index_[next] >= 0) {
                    distance_[next] = distance_[current] + 1;
                    result[z_index_[next]] = distance_[next];
                } else if (graph.node_layer_low(next) == layer && graph.node_layer_high(next) == layer) {
                    distance_[next] = distance_[current] + 1;
                    queue.push_back(next);
                }
            };
            if (reverse) {
                size_t end = reverse_start_[current] + reverse_count_[current];
                for (size_t edge = reverse_start_[current]; edge < end; ++edge)
                    visit(reverse_edges_[edge]);
            } else {
                for (auto edge : graph.node_out_edges(current))
                    visit(graph.edge_sink_node(current, edge));
            }
        }
        return cache.emplace(terminal, std::move(result)).first->second;
    }

    std::vector<RRNodeId> channels_;                                              ///< Candidate index to native physical RR resource.
    std::unique_ptr<H3dFastPlan> fast_plan_;                                      ///< Optional SCC index with geometric surrogate planning.
    vtr::vector<RRNodeId, int> z_index_;                                          ///< RR resource to candidate index, -1 for planar resources.
    vtr::vector<RRNodeId, size_t> reverse_start_;                                 ///< Reverse CSR offset per resource.
    vtr::vector<RRNodeId, size_t> reverse_count_;                                 ///< Reverse CSR length per resource.
    std::vector<RRNodeId> reverse_edges_;                                         ///< Sources of original incoming directed edges.
    vtr::vector<RRNodeId, int> distance_;                                         ///< Reusable per-search BFS distance scratch.
    std::unordered_map<RRNodeId, std::vector<int>> forward_cache_;                ///< Source-to-channel distances.
    std::unordered_map<RRNodeId, std::vector<int>> reverse_cache_;                ///< Channel-to-sink distances.
    std::unordered_map<ParentNetId, std::vector<t_h3d_connection_guide>> guides_; ///< Guides indexed by net and terminal.
    std::set<size_t> current_channels_;                                           ///< Previous tree channels included before pruning.
    size_t plans_ = 0;                                                            ///< Completed planning events.
    size_t groups_ = 0;                                                           ///< Shared groups selected cumulatively.
    size_t bfs_nodes_ = 0;                                                        ///< BFS node expansions, separate from A* statistics.
    size_t no_candidate_ = 0;                                                     ///< Connections delegated to unmodified search.
    size_t fallbacks_ = 0;                                                        ///< Guided search failures retried without preferences.
    double planning_seconds_ = 0.;                                                ///< Includes reverse-index build and all cache/search/DP work.
    size_t guided_observations_ = 0;                                              ///< Cumulative routed sink paths with preferences.
    size_t preferred_observations_ = 0;                                           ///< Cumulative preferred-channel matches on those paths.
    size_t rollbacks_ = 0;                                                        ///< Fully restored failed/rejected signal-net transactions.
};

std::unique_ptr<H3dPlanner> planner; ///< Serial-router-owned experimental planner.

} // namespace

bool h3d_enabled() { return settings().mode != e_h3d_mode::OFF; }

bool h3d_force_whole_net() { return settings().mode == e_h3d_mode::DYNAMIC_WHOLE; }

bool h3d_force_subtree() { return settings().mode == e_h3d_mode::DYNAMIC_SUBTREE; }

bool h3d_transactional() { return h3d_force_whole_net() || h3d_force_subtree(); }

void h3d_observe_net(ParentNetId net) {
    if (planner) planner->observe(net);
}

void h3d_record_rollback() {
    VTR_ASSERT(planner);
    planner->rollback();
}

bool h3d_test_rollback_once() {
    static const bool enabled = std::getenv("VPR_H3D_TEST_ROLLBACK_ONCE") != nullptr;
    static bool used = false;
    if (enabled && !used) {
        used = true;
        VTR_LOG("H3D_TEST rejecting one completed replacement to exercise full rollback\n");
        return true;
    }
    return false;
}

void h3d_prepare_iteration(int iteration, bool is_flat) {
    if (!h3d_enabled()) return;
    if (iteration == 1) {
        const auto& device = g_vpr_ctx.device();
        if (is_flat || device.grid.get_num_layers() != 2 || device.grid.has_interposer_cuts() || !device.rr_bus_muxes.empty())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes currently require clustered routing, two stacked layers, no interposer cuts and no bus-mux sharing");
        planner = std::make_unique<H3dPlanner>();
    }
}

void h3d_capture_net(ParentNetId net) {
    if (!h3d_enabled()) return;
    if (!planner)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes require the serial netlist router");
    planner->capture(net);
}

void h3d_prepare_net(ParentNetId net, int /*iteration*/, float pres_fac, const std::vector<float>& criticality) {
    if (h3d_enabled()) planner->plan(net, pres_fac, criticality);
}

const t_h3d_connection_guide* h3d_connection_guide(ParentNetId net, int pin) {
    return h3d_enabled() ? planner->guide(net, pin) : nullptr;
}

void h3d_record_fallback() {
    if (planner) planner->fallback();
}

float h3d_vertical_weight() {
    static const float value = [] {
        const char* text = std::getenv("VPR_H3D_VERTICAL_WEIGHT");
        if (!text)
            return 0.f;
        errno = 0;
        char* end = nullptr;
        float parsed = std::strtof(text, &end);
        if (errno || end == text || *end || !std::isfinite(parsed) || parsed < 0.f) {
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_VERTICAL_WEIGHT must be finite and nonnegative, got '%s'", text);
        }
        VTR_LOG("H3D vertical_weight=%g (additional congestion preference; native timing unchanged)\n", parsed);
        return parsed;
    }();
    return value;
}

void h3d_log_iteration(int iteration, float pres_fac, const RouterStats& stats) {
    static const bool enabled = std::getenv("VPR_H3D_STATS") != nullptr;
    if (!enabled && !h3d_enabled())
        return;
    const auto& graph = g_vpr_ctx.device().rr_graph;
    const auto& routing = g_vpr_ctx.routing();
    size_t vertical_used = 0;
    size_t vertical_occupancy = 0;
    size_t vertical_overused = 0;
    size_t vertical_total_overuse = 0;
    for (RRNodeId inode : graph.nodes()) {
        if (graph.node_type(inode) != e_rr_type::CHANZ)
            continue;
        int occ = routing.rr_node_route_inf[inode].occ();
        int capacity = graph.node_capacity(inode);
        vertical_used += occ > 0;
        vertical_occupancy += occ;
        vertical_overused += occ > capacity;
        vertical_total_overuse += std::max(0, occ - capacity);
    }
    VTR_LOG("H3D_ITER iter=%d pres=%g z_used=%zu z_net_occupancy=%zu z_overused=%zu z_excess=%zu nets_routed=%zu connections_routed=%zu heap_pushes=%zu heap_pops=%zu\n",
            iteration, pres_fac, vertical_used, vertical_occupancy, vertical_overused, vertical_total_overuse,
            stats.nets_routed, stats.connections_routed, stats.heap_pushes, stats.heap_pops);
    if (planner) planner->log();
    if (settings().edge_encoding) {
        std::unordered_map<RRNodeId, int> crossing_occupancy;
        for (const auto& tree : routing.route_trees) {
            if (!tree) continue;
            std::set<RRNodeId> used;
            for (const auto& node : tree->all_nodes()) {
                auto parent = node.parent();
                if (parent && h3d_crosses_layers(graph, parent->inode, node.inode)) used.insert(parent->inode);
            }
            for (auto node : used) ++crossing_occupancy[node];
        }
        size_t occupancy = 0, excess = 0;
        for (auto [node, count] : crossing_occupancy) {
            occupancy += count;
            excess += std::max(0, count - graph.node_capacity(node));
        }
        VTR_LOG("H3D_EDGE_ITER iter=%d crossing_sources_used=%zu crossing_source_net_occupancy=%zu crossing_source_excess=%zu\n",
                iteration, crossing_occupancy.size(), occupancy, excess);
    }
}
