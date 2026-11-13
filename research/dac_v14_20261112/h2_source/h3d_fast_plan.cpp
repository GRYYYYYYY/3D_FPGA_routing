#include "h3d_fast_plan.h"
#include "h3d_crossing.h"
#include "h3d_calibrated_cost.h"
#include "h3d_independent_plan.h"

#include <cmath>
#include <bit>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <set>

#include "globals.h"
#include "h3d_partition_dp.h"
#include "route_common.h"
#include "route_tree.h"
#include "vtr_log.h"
#include "vpr_error.h"

namespace {

/** @brief Pack nonnegative integer XY coordinates into a collision-free key. */
unsigned long long site_key(int x, int y) {
    return (static_cast<unsigned long long>(static_cast<unsigned>(x)) << 32) | static_cast<unsigned>(y);
}

/** @brief Whether two sorted component-id lists have a common member. */
bool intersects(const std::vector<int>& a, const std::vector<int>& b) {
    // Crossing-entry lists are often singletons, while their reachable closure
    // can contain hundreds of thousands of SB half-node components.
    if (a.size() > 8 * b.size()) {
        for (int value : b)
            if (std::binary_search(a.begin(), a.end(), value)) return true;
        return false;
    }
    if (b.size() > 8 * a.size()) return intersects(b, a);
    size_t i = 0, j = 0;
    while (i < a.size() && j < b.size()) {
        if (a[i] == b[j]) return true;
        if (a[i] < b[j])
            ++i;
        else
            ++j;
    }
    return false;
}

/** @brief Sort and deduplicate a small component list. */
void unique_components(std::vector<int>& values) {
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
}

} // namespace

H3dFastPlan::H3dFastPlan(const RRGraphView& graph, bool delay_cost, size_t delay_budget, bool edge_encoding)
    : graph_(graph), edge_encoding_(edge_encoding) {
    const char* mixed = std::getenv("VPR_H3D_MIXED_DELAY");
    if (mixed && std::string(mixed) != "0" && std::string(mixed) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_MIXED_DELAY must be 0 or 1");
    mixed_delay_ = mixed && std::string(mixed) == "1";
    const char* timing = std::getenv("VPR_H3D_TIMING_GUIDE");
    if (timing) {
        char* end = nullptr;
        timing_guide_weight_ = std::strtod(timing, &end);
        if (end == timing || *end || !std::isfinite(timing_guide_weight_) || timing_guide_weight_ < 0. || timing_guide_weight_ > 1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TIMING_GUIDE must be in [0,1]");
    }
    const char* assignment = std::getenv("VPR_H3D_ASSIGNMENT");
    std::string solver = assignment ? assignment : "shared";
    if (solver != "shared" && solver != "independent")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_ASSIGNMENT must be shared or independent");
    independent_ = solver == "independent";
    VTR_LOG("H3D_EXPERIMENT mixed_delay=%d timing_guide=%g assignment=%s\n", mixed_delay_, timing_guide_weight_, solver.c_str());
    channel_index_.resize(graph_.num_nodes(), -1);
    size_t planar_count = 0;
    double planar_length = 0.;
    std::vector<std::pair<size_t, size_t>> planar_edges;
    for (RRNodeId node : graph_.nodes()) {
        if (edge_encoding_ && graph_.node_type(node) == e_rr_type::CHANZ)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Edge encoding requires single-layer RR nodes; mixed CHANZ encoding is unsupported");
        if (edge_encoding_ ? h3d_crossing_entry(graph_, node) : graph_.node_type(node) == e_rr_type::CHANZ) {
            if (edge_encoding_ && graph_.node_type(node) != e_rr_type::OPIN
                && !(graph_.node_type(node) == e_rr_type::CHANX && graph_.node_direction(node) == Direction::NONE))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unsupported crossing source %zu; expected OPIN or SB half-node", size_t(node));
            channel_index_[node] = channels_.size();
            sites_[site_key(graph_.node_xlow(node), graph_.node_ylow(node))].push_back(channels_.size());
            channels_.push_back(node);
            if (!edge_encoding_) continue;
        }
        if ((graph_.node_type(node) == e_rr_type::CHANX || graph_.node_type(node) == e_rr_type::CHANY)
            && (!edge_encoding_ || graph_.node_direction(node) != Direction::NONE)) {
            ++planar_count;
            planar_length += 1 + graph_.node_xhigh(node) - graph_.node_xlow(node)
                             + graph_.node_yhigh(node) - graph_.node_ylow(node);
        }
        for (auto edge : graph_.node_out_edges(node)) {
            RRNodeId sink = graph_.edge_sink_node(node, edge);
            if (graph_.node_type(sink) != e_rr_type::CHANZ
                && graph_.node_layer_low(node) == graph_.node_layer_high(node)
                && graph_.node_layer_low(sink) == graph_.node_layer_high(sink)
                && graph_.node_layer_low(node) == graph_.node_layer_low(sink))
                planar_edges.emplace_back(size_t(node), size_t(sink));
        }
    }
    if (planar_count) mean_span_ = planar_length / planar_count;
    reachability_ = std::make_unique<H3dReachabilityIndex>(graph_.num_nodes(), planar_edges);
    entries_.resize(channels_.size());
    exits_.resize(channels_.size());
    for (RRNodeId node : graph_.nodes()) {
        for (auto edge : graph_.node_out_edges(node)) {
            RRNodeId sink = graph_.edge_sink_node(node, edge);
            int source_z = channel_index_[node];
            int sink_z = channel_index_[sink];
            if (edge_encoding_) {
                if (h3d_crosses_layers(graph_, node, sink)) {
                    VTR_ASSERT(source_z >= 0);
                    entries_[source_z].push_back(reachability_->component(size_t(node)));
                    exits_[source_z].push_back(reachability_->component(size_t(sink)));
                }
                continue;
            }
            if (source_z < 0 && sink_z >= 0)
                entries_[sink_z].push_back(reachability_->component(size_t(node)));
            if (source_z >= 0 && sink_z < 0)
                exits_[source_z].push_back(reachability_->component(size_t(sink)));
        }
    }
    std::vector<int> all_entries, all_exits;
    for (size_t c = 0; c < channels_.size(); ++c) {
        unique_components(entries_[c]);
        unique_components(exits_[c]);
        all_entries.insert(all_entries.end(), entries_[c].begin(), entries_[c].end());
        all_exits.insert(all_exits.end(), exits_[c].begin(), exits_[c].end());
    }
    forward_allowed_ = reachability_->mark(all_entries, true);
    reverse_allowed_ = reachability_->mark(all_exits, false);
    VTR_LOG("H3D_SCC_INIT components=%zu planar_edges=%zu channels=%zu mean_planar_span=%g\n",
            reachability_->num_components(), planar_edges.size(), channels_.size(), mean_span_);
    if (std::getenv("VPR_H3D_VALIDATE_SCC")) validate_against_bfs();
    if (channels_.empty() && !edge_encoding_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "No CHANZ candidates; select an explicit supported graph encoding");
    if (delay_cost) delay_plan_ = std::make_unique<H3dDelayPlan>(graph_, delay_budget, edge_encoding_);
}

void H3dFastPlan::validate_against_bfs() {
    std::vector<std::vector<RRNodeId>> predecessors(graph_.num_nodes());
    for (RRNodeId node : graph_.nodes())
        for (auto edge : graph_.node_out_edges(node))
            predecessors[size_t(graph_.edge_sink_node(node, edge))].push_back(node);
    auto bfs = [&](RRNodeId endpoint, bool backwards) {
        std::vector<bool> seen(graph_.num_nodes(), false), result(channels_.size(), false);
        std::vector<RRNodeId> frontier{endpoint};
        seen[size_t(endpoint)] = true;
        int layer = graph_.node_layer_low(endpoint);
        for (size_t i = 0; i < frontier.size(); ++i) {
            if (edge_encoding_) {
                RRNodeId current = frontier[i];
                if (!backwards && channel_index_[current] >= 0)
                    result[channel_index_[current]] = true;
                auto visit_edge = [&](RRNodeId next) {
                    if (backwards && h3d_crosses_layers(graph_, next, current)) {
                        VTR_ASSERT(channel_index_[next] >= 0);
                        result[channel_index_[next]] = true;
                    } else if (graph_.node_layer_low(next) == layer && !seen[size_t(next)]) {
                        seen[size_t(next)] = true;
                        frontier.push_back(next);
                    }
                };
                if (backwards) {
                    for (RRNodeId next : predecessors[size_t(current)]) visit_edge(next);
                } else {
                    for (auto edge : graph_.node_out_edges(current)) visit_edge(graph_.edge_sink_node(current, edge));
                }
                continue;
            }
            auto visit = [&](RRNodeId next) {
                if (seen[size_t(next)]) return;
                int z = channel_index_[next];
                if (z >= 0) {
                    seen[size_t(next)] = true;
                    result[z] = true;
                } else if (graph_.node_layer_low(next) == layer && graph_.node_layer_high(next) == layer) {
                    seen[size_t(next)] = true;
                    frontier.push_back(next);
                }
            };
            RRNodeId node = frontier[i];
            if (backwards) {
                for (RRNodeId next : predecessors[size_t(node)])
                    visit(next);
            } else {
                for (auto edge : graph_.node_out_edges(node))
                    visit(graph_.edge_sink_node(node, edge));
            }
        }
        return result;
    };
    size_t connections = 0, comparisons = 0, reachable = 0;
    for (const auto& terminals : g_vpr_ctx.routing().net_rr_terminals) {
        if (terminals.size() < 2 || terminals[0] == RRNodeId::INVALID()) continue;
        RRNodeId source = terminals[0];
        for (size_t pin = 1; pin < terminals.size() && connections < 32; ++pin) {
            RRNodeId sink = terminals[pin];
            if (sink == RRNodeId::INVALID() || graph_.node_layer_low(source) == graph_.node_layer_low(sink)) continue;
            auto from = bfs(source, false), to = bfs(sink, true);
            for (size_t c = 0; c < channels_.size(); ++c) {
                bool expected = from[c] && to[c];
                if (feasible_(source, c, sink) != expected)
                    VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "SCC/BFS mismatch for source %zu channel %zu sink %zu", size_t(source), size_t(channels_[c]), size_t(sink));
                ++comparisons;
                reachable += expected;
            }
            ++connections;
        }
        if (connections == 32) break;
    }
    VTR_LOG("H3D_SCC_VALIDATED connections=%zu channel_comparisons=%zu reachable=%zu\n", connections, comparisons, reachable);
}

const std::vector<int>& H3dFastPlan::reach_(RRNodeId endpoint, bool reverse) {
    auto& cache = reverse ? sink_cache_ : source_cache_;
    auto found = cache.find(endpoint);
    if (found != cache.end()) return found->second;
    auto result = reachability_->relevant_components(size_t(endpoint), reverse, reverse ? reverse_allowed_ : forward_allowed_, edge_encoding_);
    return cache.emplace(endpoint, std::move(result)).first->second;
}

bool H3dFastPlan::feasible_(RRNodeId source, size_t channel, RRNodeId sink) {
    ++queries_;
    return intersects(reach_(source, false), entries_[channel]) && intersects(reach_(sink, true), exits_[channel]);
}

double H3dFastPlan::proxy_(RRNodeId endpoint, size_t channel) const {
    RRNodeId z = channels_[channel];
    int distance = std::abs(graph_.node_xlow(endpoint) - graph_.node_xlow(z))
                   + std::abs(graph_.node_ylow(endpoint) - graph_.node_ylow(z));
    return 2. + distance / mean_span_;
}

std::vector<size_t> H3dFastPlan::nearby_(RRNodeId source, RRNodeId sink, int center_x, int center_y, size_t target) const {
    int sx = graph_.node_xlow(source), sy = graph_.node_ylow(source);
    int tx = graph_.node_xlow(sink), ty = graph_.node_ylow(sink);
    std::vector<std::pair<int, int>> points{{sx, sy}, {tx, ty}, {(sx + tx) / 2, (sy + ty) / 2}, {(3 * sx + tx) / 4, (3 * sy + ty) / 4}, {(sx + 3 * tx) / 4, (sy + 3 * ty) / 4}, {sx, ty}, {tx, sy}, {center_x, center_y}};
    std::set<size_t> selected;
    for (int radius = 0; radius <= 3 && selected.size() < target; ++radius) {
        for (const auto& [x, y] : points)
            for (int dx = -radius; dx <= radius; ++dx)
                for (int dy = -radius; dy <= radius; ++dy) {
                    if (std::max(std::abs(dx), std::abs(dy)) != radius || x + dx < 0 || y + dy < 0) continue;
                    auto site = sites_.find(site_key(x + dx, y + dy));
                    if (site != sites_.end()) selected.insert(site->second.begin(), site->second.end());
                }
    }
    return {selected.begin(), selected.end()};
}

std::vector<size_t> H3dFastPlan::diversify_(const std::vector<std::pair<double, size_t>>& ranked, size_t count) const {
    if (ranked.empty()) return {};
    std::vector<size_t> chosen{ranked.front().second};
    size_t shortlist = std::min(ranked.size(), count * 8);
    while (chosen.size() < count && chosen.size() < shortlist) {
        double best_score = -1.;
        size_t best = chosen.front();
        for (size_t i = 0; i < shortlist; ++i) {
            size_t c = ranked[i].second;
            if (std::find(chosen.begin(), chosen.end(), c) != chosen.end()) continue;
            int spread = std::numeric_limits<int>::max();
            for (size_t prior : chosen)
                spread = std::min(spread, std::abs(graph_.node_xlow(channels_[c]) - graph_.node_xlow(channels_[prior]))
                                              + std::abs(graph_.node_ylow(channels_[c]) - graph_.node_ylow(channels_[prior])));
            double score = (1. + spread) / (1. + ranked[i].first - ranked.front().first);
            if (score > best_score) {
                best_score = score;
                best = c;
            }
        }
        if (best_score < 0.) break;
        chosen.push_back(best);
    }
    return chosen;
}

t_h3d_fast_plan H3dFastPlan::plan(ParentNetId net, const std::vector<float>& criticality, const std::vector<RRNodeId>& previous_channels, float pres_fac, size_t candidate_count, float opening_weight, float miss_weight, bool use_tree, float min_criticality) {
    const auto& routing = g_vpr_ctx.routing();
    const auto& terminals = routing.net_rr_terminals[net];
    RRNodeId source = terminals[0];
    t_h3d_fast_plan result;
    result.guides.resize(terminals.size());
    for (auto& guide : result.guides) guide.edge_encoding = edge_encoding_;
    std::vector<int> pins;
    int center_x = 0, center_y = 0;
    for (size_t pin = 1; pin < terminals.size(); ++pin)
        if (graph_.node_layer_low(source) != graph_.node_layer_low(terminals[pin])) {
            if (criticality[pin] < min_criticality) { ++skipped_pins_; continue; }
            ++eligible_pins_;
            pins.push_back(pin);
            center_x += graph_.node_xlow(terminals[pin]);
            center_y += graph_.node_ylow(terminals[pin]);
        }
    if (pins.empty()) return result;
    center_x /= pins.size();
    center_y /= pins.size();
    const H3dDelayPlan::Distances* forward = nullptr;
    if (delay_plan_ && delay_plan_->supported()) forward = &delay_plan_->distances(source, false);
    std::unordered_map<int, const H3dDelayPlan::Distances*> reverse;
    std::set<int> timed;
    // Normalize observed delay by the same physical unit before fitting a
    // robust endpoint-local scale. Unknown distance is not infeasibility.
    auto calibrate = [&](RRNodeId endpoint, const H3dDelayPlan::Distances& distances) {
        std::vector<double> ratios;
        for (const auto& [node, delay] : distances) {
            int c = channel_index_[node];
            if (c >= 0) ratios.push_back(delay / delay_plan_->delay_unit() / proxy_(endpoint, c));
        }
        return h3d_calibrated_scale(std::move(ratios));
    };
    const bool mixed = mixed_delay_ && forward;
    const double source_scale = mixed ? calibrate(source, *forward) : 1.;
    std::unordered_map<int, double> sink_scales;
    auto source_cost = [&](size_t c) {
        if (forward) {
            auto found = forward->find(channels_[c]);
            if (found != forward->end()) return found->second / delay_plan_->delay_unit();
        }
        return source_scale * proxy_(source, c);
    };
    std::set<RRNodeId> owned;
    if (routing.route_trees[net])
        for (const auto& node : routing.route_trees[net]->all_nodes())
            if (channel_index_[node.inode] >= 0) owned.insert(node.inode);
    auto opening = [&](size_t c) {
        RRNodeId node = channels_[c];
        const auto& info = routing.rr_node_route_inf[node];
        int demand = info.occ() + (owned.contains(node) ? 0 : 1);
        // Additional demand is zero for a retained channel of this net.
        double negotiated = info.acc_cost * (1. + pres_fac * std::max(0, demand - graph_.node_capacity(node)));
        return source_cost(c) + opening_weight * negotiated;
    };
    auto branch = [&](int pin, size_t c) {
        if (mixed) {
            double sink_cost = proxy_(terminals[pin], c);
            auto back = reverse.find(pin);
            if (back != reverse.end()) {
                auto found = back->second->find(channels_[c]);
                sink_cost = found != back->second->end() ? found->second / delay_plan_->delay_unit()
                                                       : sink_cost * sink_scales.at(pin);
            }
            return sink_cost * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * source_cost(c);
        }
        if (timed.contains(pin)) {
            const auto& distances = *reverse.at(pin);
            auto found = distances.find(channels_[c]);
            if (found == distances.end() || !forward->contains(channels_[c]))
                return std::numeric_limits<double>::infinity();
            return found->second / delay_plan_->delay_unit() * (1. + 4. * criticality[pin])
                   + 4. * criticality[pin] * source_cost(c);
        }
        return proxy_(terminals[pin], c) * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * proxy_(source, c);
    };
    std::set<size_t> pool;
    for (int pin : pins) {
        auto candidates = nearby_(source, terminals[pin], center_x, center_y, candidate_count * 8);
        for (RRNodeId node : previous_channels)
            if (channel_index_[node] >= 0) candidates.push_back(channel_index_[node]);
        std::sort(candidates.begin(), candidates.end());
        candidates.erase(std::unique(candidates.begin(), candidates.end()), candidates.end());
        spatial_candidates_ += candidates.size();
        std::vector<std::pair<double, size_t>> ranked;
        for (size_t c : candidates)
            if (feasible_(source, c, terminals[pin])) ranked.emplace_back(opening(c) + branch(pin, c), c);
        // Spatial sampling failure is not infeasibility. Search the full
        // candidate table until a usable fallback set is found.
        if (ranked.empty())
            for (size_t c = 0; c < channels_.size() && ranked.size() < candidate_count * 8; ++c)
                if (feasible_(source, c, terminals[pin])) ranked.emplace_back(opening(c) + branch(pin, c), c);
        if (mixed && !ranked.empty()) {
            // Unlike the legacy all-or-nothing rule, reverse-only measurements
            // are useful even when the bounded source query found no candidate.
            const auto& back = delay_plan_->distances(terminals[pin], true);
            reverse[pin] = &back;
            sink_scales[pin] = calibrate(terminals[pin], back);
            ++mixed_pins_;
            size_t measured = 0;
            for (auto& [cost, c] : ranked) {
                bool from = forward->contains(channels_[c]);
                bool to = back.contains(channels_[c]);
                measured += from || to;
                mixed_both_ += from && to;
                mixed_source_only_ += from && !to;
                mixed_sink_only_ += !from && to;
                mixed_estimated_ += !from && !to;
                cost = opening(c) + branch(pin, c);
            }
            mixed_informed_pins_ += measured > 0;
        } else if (forward && !forward->empty() && !ranked.empty()) {
            const auto& back = delay_plan_->distances(terminals[pin], true);
            reverse[pin] = &back;
            std::vector<size_t> covered;
            for (auto [cost, c] : ranked)
                if (forward->contains(channels_[c]) && back.contains(channels_[c])) covered.push_back(c);
            // Preserve K alternatives when possible; a bounded search miss is
            // not a failed reachability proof and does not remove router edges.
            if (covered.size() >= std::min(candidate_count, ranked.size())) {
                timed.insert(pin);
                ranked.clear();
                for (size_t c : covered) ranked.emplace_back(opening(c) + branch(pin, c), c);
                ++measured_pins_;
            } else ++unmeasured_pins_;
        } else if (delay_plan_) ++unmeasured_pins_;
        std::sort(ranked.begin(), ranked.end());
        auto selected = diversify_(ranked, candidate_count);
        for (RRNodeId node : previous_channels) {
            int c = channel_index_[node];
            if (c >= 0 && feasible_(source, c, terminals[pin])) selected.push_back(c);
        }
        std::sort(selected.begin(), selected.end());
        selected.erase(std::unique(selected.begin(), selected.end()), selected.end());
        if (selected.empty()) ++result.no_candidate;
        for (size_t c : selected) {
            result.guides[pin].preferred.push_back(channels_[c]);
            pool.insert(c);
        }
        result.guides[pin].miss_weight = miss_weight;
    }
    // Keep pathological high-fanout work linear in the connection count.
    // This explicit fallback is counted and does not claim a tree optimum.
    if (use_tree && pins.size() > 128) {
        ++high_fanout_fallbacks_;
        use_tree = false;
    }
    if (use_tree && !pool.empty()) {
        std::vector<size_t> table(pool.begin(), pool.end());
        std::vector<double> openings;
        for (size_t c : table)
            openings.push_back(opening(c));
        std::vector<t_h3d_plan_leaf> leaves;
        for (int pin : pins) {
            if (result.guides[pin].preferred.empty()) continue;
            RRNodeId sink = terminals[pin];
            t_h3d_plan_leaf leaf{pin, graph_.node_xlow(sink), graph_.node_ylow(sink), {}};
            for (size_t i = 0; i < table.size(); ++i) {
                if (!feasible_(source, table[i], sink)) continue;
                double cost = branch(pin, table[i]);
                // A delay-scored leaf may not have measured a candidate
                // contributed by another leaf. The finite DP model omits
                // that entry; this never removes an edge from detailed routing.
                if (std::isfinite(cost)) leaf.candidates.push_back({i, cost});
            }
            leaves.push_back(std::move(leaf));
        }
        // Diagnostic-only exact-cost fingerprint, before either solver.
        static const bool trace_table = std::getenv("VPR_H3D_TRACE_TABLE") != nullptr;
        if (trace_table) {
            uint64_t fingerprint = 14695981039346656037ull;
            auto mix = [&](uint64_t word) {
                for (int i = 0; i < 8; ++i) {
                    fingerprint ^= word & 255;
                    fingerprint *= 1099511628211ull;
                    word >>= 8;
                }
            };
            mix(table.size());
            for (size_t i = 0; i < table.size(); ++i) {
                mix(size_t(channels_[table[i]]));
                mix(std::bit_cast<uint64_t>(openings[i]));
            }
            mix(leaves.size());
            for (const auto& leaf : leaves) {
                mix(leaf.pin); mix(leaf.x); mix(leaf.y); mix(leaf.candidates.size());
                for (const auto& c : leaf.candidates) {
                    mix(c.channel); mix(std::bit_cast<uint64_t>(c.branch_cost));
                }
            }
            VTR_LOG("H3D_TABLE net=%zu fingerprint=%016llx candidates=%zu leaves=%zu\n",
                    size_t(net), static_cast<unsigned long long>(fingerprint), table.size(), leaves.size());
        }
        auto planned = independent_ ? h3d_plan_independent(leaves, openings) : h3d_plan_partition(leaves, openings);
        if (std::isfinite(planned.cost)) {
            result.groups = planned.groups;
            for (const auto& [pin, c] : planned.assignment)
                result.guides[pin].preferred = {channels_[table[c]]};
        }
    }
    for (int pin : pins) {
        auto& guide = result.guides[pin];
        std::sort(guide.preferred.begin(), guide.preferred.end());
        if (timing_guide_weight_ > 0. && forward && !guide.preferred.empty()) {
            // Confidence is measured-side coverage of the selected preference,
            // not whole-query coverage. No measurements => no timing penalty.
            double reliability = 0.;
            for (RRNodeId node : guide.preferred) {
                reliability += .5 * forward->contains(node);
                auto back = reverse.find(pin);
                if (back != reverse.end()) reliability += .5 * back->second->contains(node);
            }
            reliability /= guide.preferred.size();
            // At most one graph delay unit per mismatching crossing. This is
            // a search preference only, never part of physical Tdel or STA.
            guide.timing_miss_penalty = timing_guide_weight_ * reliability * delay_plan_->delay_unit();
            timing_guides_ += guide.timing_miss_penalty > 0.f;
        }
    }
    return result;
}

void H3dFastPlan::log() const {
    VTR_LOG("H3D_SCC queries=%zu endpoint_cache=%zu sampled_candidates=%zu high_fanout_fallbacks=%zu\n",
            queries_, source_cache_.size() + sink_cache_.size(), spatial_candidates_, high_fanout_fallbacks_);
    VTR_LOG("H3D_SCORE eligible=%zu skipped=%zu delay_scored=%zu unmeasured=%zu\n",
            eligible_pins_, skipped_pins_, measured_pins_, unmeasured_pins_);
    VTR_LOG("H3D_MIXED pins=%zu informed_pins=%zu both=%zu source_only=%zu sink_only=%zu estimated=%zu\n",
            mixed_pins_, mixed_informed_pins_, mixed_both_, mixed_source_only_, mixed_sink_only_, mixed_estimated_);
    VTR_LOG("H3D_TIMING_GUIDE nonzero_guides=%zu weight=%g\n", timing_guides_, timing_guide_weight_);
    if (delay_plan_) delay_plan_->log();
}
