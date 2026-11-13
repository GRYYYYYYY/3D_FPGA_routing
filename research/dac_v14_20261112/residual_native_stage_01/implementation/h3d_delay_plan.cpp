#include "h3d_delay_plan.h"
#include "h3d_crossing.h"
#include "h3d_bidirectional_delay.h"
#include "h3d_compact_witness.h"

#include "globals.h"
#include "vtr_log.h"
#include "vpr_error.h"
#include "route_common.h"
#include <cstdlib>

H3dDelayPlan::H3dDelayPlan(const RRGraphView& graph, size_t budget, bool edge_encoding)
    : graph_(graph), budget_(budget), edge_encoding_(edge_encoding) {
    if (const char* value = std::getenv("VPR_H3D_TRACE_PATH_WITNESS")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_PATH_WITNESS must be 0 or 1");
        trace_paths_ = std::string(value) == "1";
        const char* targeted = std::getenv("VPR_H3D_TARGET_DELAY");
        const char* prefix = std::getenv("VPR_H3D_TRACE_RETAINED_PREFIX");
        if (trace_paths_ && (!edge_encoding_ || (targeted && std::string(targeted) == "1")
                            || !prefix || std::string(prefix) != "1"))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Path-witness diagnostics require edge encoding, retained-prefix tracing and non-targeted queries");
    }
    cache_paths_ = trace_paths_;
    if (const char* value = std::getenv("VPR_H3D_CANDIDATE_PATH_CAPTURE")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CANDIDATE_PATH_CAPTURE must be 0 or 1");
        cache_paths_ |= std::string(value) == "1";
    }
    if (cache_paths_) {
        const char* targeted = std::getenv("VPR_H3D_TARGET_DELAY");
        if (!edge_encoding_ || (targeted && std::string(targeted) == "1"))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cached path capture requires legacy edge-encoding distance queries");
    }
    if(const char* value=std::getenv("VPR_H3D_CANDIDATE_PATH_COMPACT")) {
        if(std::string(value)!="0" && std::string(value)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_CANDIDATE_PATH_COMPACT must be 0 or 1");
        compact_paths_=std::string(value)=="1";
        if(compact_paths_ && !cache_paths_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Compact witnesses require path capture");
    }
    if (const char* value = std::getenv("VPR_H3D_TARGET_FRONTIER")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TARGET_FRONTIER must be 0 or 1");
        persistent_frontier_ = std::string(value) == "1";
        const char* targeted = std::getenv("VPR_H3D_TARGET_DELAY");
        if (persistent_frontier_ && (!targeted || std::string(targeted) != "1" || !edge_encoding_))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Persistent frontiers require targeted edge-encoding queries");
    }
    if (const char* value = std::getenv("VPR_H3D_FRONTIER_SLOTS")) {
        char* end = nullptr;
        auto slots = std::strtoull(value, &end, 10);
        if (end == value || *end || value[0] == '-' || slots < 1 || slots > 64)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_FRONTIER_SLOTS must be an integer in [1,64]");
        frontier_slots_ = slots;
    }
    if (const char* value = std::getenv("VPR_H3D_FRONTIER_RETAIN")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_FRONTIER_RETAIN must be 0 or 1");
        frontier_retain_ = std::string(value) == "1";
        if (!frontier_retain_ && !persistent_frontier_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Retention ablation requires universal-terminal frontier queries");
    }
    if (const char* value = std::getenv("VPR_H3D_TRACE_DELAY_BOUND")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_DELAY_BOUND must be 0 or 1");
        trace_bounds_ = std::string(value) == "1";
        if (trace_bounds_ && !persistent_frontier_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Delay-bound diagnostics require universal-terminal frontier queries");
    }
    if (const char* value = std::getenv("VPR_H3D_BOUND_CLAMP")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_BOUND_CLAMP must be 0 or 1");
        clamp_bounds_ = std::string(value) == "1";
        if (clamp_bounds_ && !persistent_frontier_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Bound-clamped estimates require universal-terminal frontier queries");
    }
    if (const char* value = std::getenv("VPR_H3D_TARGET_REUSE")) {
        if (std::string(value) != "0" && std::string(value) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TARGET_REUSE must be 0 or 1");
        targeted_reuse_ = std::string(value) == "1";
        const char* targeted = std::getenv("VPR_H3D_TARGET_DELAY");
        if (targeted_reuse_ && (!targeted || std::string(targeted) != "1" || !edge_encoding_))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Target reuse requires targeted edge-encoding delay queries");
    }
    if (persistent_frontier_ && targeted_reuse_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Persistent universal-terminal queries and one-shot incidental reuse are separate experimental strategies");
    if (const char* value = std::getenv("VPR_H3D_TARGET_QUOTA")) {
        char* end = nullptr;
        unsigned long long quota = std::strtoull(value, &end, 10);
        if (end == value || *end || value[0] == '-' || quota > budget_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TARGET_QUOTA must be an integer in [0, endpoint budget]");
        targeted_quota_ = quota;
    }
    double total = 0.;
    size_t positive = 0;
    for (const auto& sw : graph_.rr_switch()) {
        supported_ &= sw.R == 0.f && sw.Cin == 0.f && sw.Cout == 0.f && sw.Cinternal == 0.f
                      && std::isfinite(sw.Tdel) && sw.Tdel >= 0.f;
        if (sw.Tdel > 0.f) { total += sw.Tdel; ++positive; }
    }
    for (RRNodeId node : graph_.nodes()) {
        supported_ &= graph_.node_R(node) == 0.f && graph_.node_C(node) == 0.f;
    }
    if (!supported_) {
        VTR_LOG("H3D_DELAY unsupported_nonzero_RC_or_invalid_delay; geometric fallback\n");
        return;
    }
    if (positive) delay_unit_ = total / positive;
    reverse_start_.assign(graph_.num_nodes() + 1, 0);
    for (RRNodeId node : graph_.nodes())
        for (auto edge : graph_.node_out_edges(node))
            ++reverse_start_[size_t(graph_.edge_sink_node(node, edge)) + 1];
    for (size_t i = 1; i < reverse_start_.size(); ++i) reverse_start_[i] += reverse_start_[i-1];
    predecessors_.resize(reverse_start_.back());
    auto cursor = reverse_start_;
    for (RRNodeId node : graph_.nodes())
        for (auto edge : graph_.node_out_edges(node)) {
            auto sink = graph_.edge_sink_node(node, edge);
            predecessors_[cursor[size_t(sink)]++] = {node, graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel};
        }
    if (edge_encoding_) {
        edge_source_index_.resize(graph_.num_nodes(), -1);
        for (RRNodeId node : graph_.nodes()) {
            if (!h3d_crossing_entry(graph_, node)) continue;
            edge_source_index_[node] = edge_sources_.size();
            edge_sources_.push_back(node);
        }
    }
    // Synthetic terminal indices exist in the distance query only. They are
    // never inserted into VPR's RR graph or exposed to its detailed router.
    search_ = std::make_unique<H3dDelaySearch>(graph_.num_nodes() + edge_sources_.size());
    VTR_LOG("H3D_DELAY_INIT budget=%zu unit_seconds=%.12g reverse_edges=%zu zero_rc=1\n",
            budget_, delay_unit_, predecessors_.size());
}

const H3dDelayPlan::Distances& H3dDelayPlan::distances(RRNodeId endpoint, bool reverse) {
    if (!supported_) return empty_;
    auto& cache = reverse ? reverse_ : forward_;
    auto found = cache.find(endpoint);
    if (found != cache.end()) { ++hits_; return found->second; }
    int layer = graph_.node_layer_low(endpoint);
    auto terminal = [&](size_t node) { return edge_encoding_ ? node >= graph_.num_nodes()
                                                           : graph_.node_type(RRNodeId(node)) == e_rr_type::CHANZ; };
    auto expand = [&](size_t node, auto visit) {
        if (edge_encoding_) {
            auto current = RRNodeId(node);
            if (!reverse && edge_source_index_[current] >= 0)
                visit(graph_.num_nodes() + edge_source_index_[current], 0.);
            if (reverse) {
                for (size_t i = reverse_start_[node]; i < reverse_start_[node+1]; ++i) {
                    const auto& pred = predecessors_[i];
                    if (h3d_crosses_layers(graph_, pred.node, current)) {
                        VTR_ASSERT(edge_source_index_[pred.node] >= 0);
                        visit(graph_.num_nodes() + edge_source_index_[pred.node], pred.delay);
                    } else if (graph_.node_layer_low(pred.node) == layer) {
                        visit(size_t(pred.node), pred.delay);
                    }
                }
            } else {
                for (auto edge : graph_.node_out_edges(current)) {
                    RRNodeId next = graph_.edge_sink_node(current, edge);
                    if (graph_.node_layer_low(next) == layer)
                        visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(current, edge))].Tdel);
                }
            }
            return;
        }
        auto accept = [&](RRNodeId next, double delay) {
            if (terminal(size_t(next)) || (graph_.node_layer_low(next) == layer && graph_.node_layer_high(next) == layer))
                visit(size_t(next), delay);
        };
        if (reverse) {
            for (size_t i = reverse_start_[node]; i < reverse_start_[node+1]; ++i)
                accept(predecessors_[i].node, predecessors_[i].delay);
        } else {
            auto current = RRNodeId(node);
            for (auto edge : graph_.node_out_edges(current))
                accept(graph_.edge_sink_node(current, edge), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(current, edge))].Tdel);
        }
    };
    auto result = search_->query(size_t(endpoint), budget_, terminal, expand, cache_paths_);
    if (cache_paths_) {
        if(compact_paths_) {
            witness_full_records_+=result.witness.size();
            result.witness=h3d_compact_witness(result);
            witness_compact_records_+=result.witness.size();
        }
        if (result.witness.size() <= witness_record_limit_ - witness_records_) {
            auto& forest = (reverse ? reverse_witness_ : forward_witness_)[endpoint];
            forest.reserve(result.witness.size());
            for (const auto& step : result.witness) forest.emplace(step.node, step);
            witness_records_ += result.witness.size();
        } else {
            ++witness_cache_skips_; // Exact distances remain available and unchanged.
        }
    }
    ++queries_; settled_ += result.settled; truncated_ += result.budget_exhausted;
    Distances distances;
    for (auto [node, delay] : result.terminals)
        distances.emplace(edge_encoding_ ? edge_sources_.at(node-graph_.num_nodes()) : RRNodeId(node), delay);
    // Opt-in oracle: an unbounded Dijkstra over actual same-layer nodes,
    // collecting crossing costs directly, independently of synthetic terminals.
    static const bool validate = std::getenv("VPR_H3D_VALIDATE_DELAY") != nullptr;
    if (validate && edge_encoding_ && validation_queries_ < 8) {
        ++validation_queries_;
        Distances reference;
        std::vector<double> best(graph_.num_nodes(), std::numeric_limits<double>::infinity());
        using Item = std::pair<double, size_t>;
        std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;
        best[size_t(endpoint)] = 0.; queue.emplace(0., size_t(endpoint));
        auto record = [&](RRNodeId identity, double cost) {
            auto found = reference.find(identity);
            if (found == reference.end() || cost < found->second) reference[identity] = cost;
        };
        while (!queue.empty()) {
            auto [cost, raw] = queue.top(); queue.pop();
            if (cost != best[raw]) continue;
            RRNodeId node(raw);
            auto relax = [&](RRNodeId next, double weight) {
                if (graph_.node_layer_low(next) != layer) return;
                double candidate = cost + weight;
                if (candidate < best[size_t(next)]) {
                    best[size_t(next)] = candidate; queue.emplace(candidate, size_t(next));
                }
            };
            if (reverse) {
                for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                    const auto& p = predecessors_[i];
                    if (h3d_crosses_layers(graph_, p.node, node)) record(p.node, cost + p.delay);
                    else relax(p.node, p.delay);
                }
            } else {
                for (auto edge : graph_.node_out_edges(node)) {
                    RRNodeId next = graph_.edge_sink_node(node, edge);
                    if (h3d_crosses_layers(graph_, node, next)) record(node, cost);
                    else relax(next, graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel);
                }
            }
        }
        for (auto [identity, measured] : distances) {
            auto truth = reference.find(identity);
            if (truth == reference.end() || std::abs(truth->second-measured) > 1.e-18)
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Crossing delay oracle mismatch at endpoint %zu resource %zu", size_t(endpoint), size_t(identity));
        }
        if (!result.budget_exhausted && distances.size() != reference.size())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Completed crossing search missed reference terminals");
        VTR_LOG("H3D_EDGE_DELAY_VALIDATED reverse=%d returned=%zu reference=%zu budget_exhausted=%d\n",
                reverse, distances.size(), reference.size(), result.budget_exhausted);
    }
    return cache.emplace(endpoint, std::move(distances)).first->second;
}

size_t H3dDelayPlan::remaining_work(RRNodeId endpoint, bool reverse) const {
    const auto& work = reverse ? reverse_work_ : forward_work_;
    auto found = work.find(endpoint);
    size_t used = found == work.end() ? 0 : found->second;
    VTR_ASSERT(used <= budget_);
    return budget_ - used;
}

const H3dDelayPlan::Distances& H3dDelayPlan::targeted_distances(RRNodeId endpoint, bool reverse, const std::vector<RRNodeId>& targets, size_t remaining_users) {
    if (!supported_) return empty_;
    VTR_ASSERT(edge_encoding_);
    VTR_ASSERT(remaining_users > 0);
    size_t call_end = budget_;
    if (remaining_users > 1) {
        size_t remaining = remaining_work(endpoint, reverse);
        // Quotient/remainder avoids overflow in a ceiling-division numerator.
        size_t share = remaining / remaining_users + (remaining % remaining_users != 0);
        call_end = budget_ - remaining + share;
    }
    VTR_ASSERT(call_end <= budget_);
    if (persistent_frontier_) return persistent_distances_(endpoint, reverse, targets, call_end);
    auto& cache = reverse ? reverse_ : forward_;
    auto& work = reverse ? reverse_work_ : forward_work_;
    auto& values = cache[endpoint];
    auto& used = work[endpoint];
    int layer = graph_.node_layer_low(endpoint);
    const size_t goal = graph_.num_nodes(); // One ephemeral synthetic goal, never a physical RR node.
    for (RRNodeId candidate : targets) {
        VTR_ASSERT(edge_source_index_[candidate] >= 0);
        if (values.contains(candidate)) { ++targeted_hits_; continue; }
        if (used >= call_end) { ++targeted_unknown_; continue; }
        auto outgoing = [&](size_t raw, auto visit) {
            if (raw == goal) return;
            RRNodeId node(raw);
            if (!reverse && node == candidate) visit(goal, 0.);
            if (reverse) {
                for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                    const auto& p = predecessors_[i];
                    if (h3d_crosses_layers(graph_, p.node, node)) {
                        if (p.node == candidate) visit(goal, p.delay);
                    } else if (graph_.node_layer_low(p.node) == layer) visit(size_t(p.node), p.delay);
                }
            } else {
                for (auto edge : graph_.node_out_edges(node)) {
                    RRNodeId next = graph_.edge_sink_node(node, edge);
                    if (graph_.node_layer_low(next) == layer)
                        visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel);
                }
            }
        };
        auto incoming = [&](size_t raw, auto visit) {
            if (raw == goal) {
                if (!reverse) visit(size_t(candidate), 0.);
                else for (auto edge : graph_.node_out_edges(candidate)) {
                    RRNodeId next = graph_.edge_sink_node(candidate, edge);
                    if (h3d_crosses_layers(graph_, candidate, next) && graph_.node_layer_low(next) == layer)
                        visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(candidate, edge))].Tdel);
                }
                return;
            }
            RRNodeId node(raw);
            if (reverse) {
                for (auto edge : graph_.node_out_edges(node)) {
                    RRNodeId next = graph_.edge_sink_node(node, edge);
                    if (graph_.node_layer_low(next) == layer)
                        visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel);
                }
            } else {
                for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                    const auto& p = predecessors_[i];
                    if (graph_.node_layer_low(p.node) == layer) visit(size_t(p.node), p.delay);
                }
            }
        };
        size_t remaining = call_end - used;
        size_t allowance = targeted_quota_ ? std::min(targeted_quota_, remaining) : remaining;
        auto answer = H3dBidirectionalDelay::query(size_t(endpoint), goal, allowance,
                                                   200000, 500000, outgoing, incoming, targeted_reuse_);
        ++targeted_queries_;
        targeted_quota_stops_ += allowance < remaining && answer.stop == H3dBidirectionalDelay::Stop::WORK_LIMIT;
        size_t charged = answer.forward_settled + answer.reverse_settled;
        used += charged; targeted_settled_ += charged;
        VTR_ASSERT(used <= call_end && used <= budget_);
        if (answer.exact) {values[candidate] = *answer.exact; ++targeted_exact_;}
        else {++targeted_unknown_; targeted_memory_stops_ += answer.stop == H3dBidirectionalDelay::Stop::MEMORY_LIMIT;}
        if (targeted_reuse_) {
            Distances incidental;
            for (auto [raw, distance] : answer.forward_distances) {
                if (raw == goal) continue;
                ++reuse_labels_;
                RRNodeId node(raw);
                if (!reverse) {
                    if (edge_source_index_[node] >= 0) incidental.emplace(node, distance);
                } else {
                    for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                        const auto& p = predecessors_[i];
                        if (!h3d_crosses_layers(graph_, p.node, node)) continue;
                        double value = distance + p.delay;
                        // Another crossing child may be unsettled. Its distance
                        // is at least the endpoint frontier bound and its switch
                        // delay is nonnegative. An unproved upper bound is never
                        // promoted to a measured crossing-resource distance.
                        if (value > answer.forward_lower_bound) { ++reuse_uncertified_; continue; }
                        auto found = incidental.find(p.node);
                        if (found == incidental.end() || value < found->second) incidental[p.node] = value;
                    }
                }
            }
            // Stable insertion order makes the bounded optional cache reproducible.
            std::vector<std::pair<RRNodeId, double>> ordered(incidental.begin(), incidental.end());
            std::sort(ordered.begin(), ordered.end());
            for (auto [identity, distance] : ordered) {
                auto found = values.find(identity);
                if (found != values.end()) {
                    ++reuse_duplicates_;
                    if (std::abs(found->second - distance) > 1.e-18)
                        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Conflicting certified target-reuse distances");
                } else if (values.size() < 200000) {
                    values.emplace(identity, distance); ++reuse_inserted_;
                } else ++reuse_capacity_stops_;
            }
        }
    }
    return values;
}

const H3dDelayPlan::Distances& H3dDelayPlan::persistent_distances_(RRNodeId endpoint, bool reverse, const std::vector<RRNodeId>& targets, size_t call_end) {
    auto& values = (reverse ? reverse_ : forward_)[endpoint];
    auto& used = (reverse ? reverse_work_ : forward_work_)[endpoint];
    int layer = graph_.node_layer_low(endpoint);
    size_t nodes = graph_.num_nodes();
    auto terminal = [&](size_t raw) { return raw >= nodes; };
    auto outgoing = [&](size_t raw, auto visit) {
        if (terminal(raw)) return;
        RRNodeId node(raw);
        if (!reverse && edge_source_index_[node] >= 0)
            visit(nodes + edge_source_index_[node], 0.);
        if (reverse) {
            for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                const auto& p = predecessors_[i];
                if (h3d_crosses_layers(graph_, p.node, node))
                    visit(nodes + edge_source_index_[p.node], p.delay);
                else if (graph_.node_layer_low(p.node) == layer) visit(size_t(p.node), p.delay);
            }
        } else {
            for (auto edge : graph_.node_out_edges(node)) {
                RRNodeId next = graph_.edge_sink_node(node, edge);
                if (graph_.node_layer_low(next) == layer)
                    visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel);
            }
        }
    };
    auto incoming = [&](size_t raw, auto visit) {
        if (terminal(raw)) {
            RRNodeId entry = edge_sources_.at(raw - nodes);
            if (!reverse) visit(size_t(entry), 0.);
            else for (auto edge : graph_.node_out_edges(entry)) {
                RRNodeId next = graph_.edge_sink_node(entry, edge);
                if (h3d_crosses_layers(graph_, entry, next) && graph_.node_layer_low(next) == layer)
                    visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(entry, edge))].Tdel);
            }
        } else if (reverse) {
            RRNodeId node(raw);
            for (auto edge : graph_.node_out_edges(node)) {
                RRNodeId next = graph_.edge_sink_node(node, edge);
                if (graph_.node_layer_low(next) == layer)
                    visit(size_t(next), graph_.rr_switch()[RRSwitchId(graph_.edge_switch(node, edge))].Tdel);
            }
        } else {
            for (size_t i = reverse_start_[raw]; i < reverse_start_[raw+1]; ++i) {
                const auto& p = predecessors_[i];
                if (graph_.node_layer_low(p.node) == layer) visit(size_t(p.node), p.delay);
            }
        }
    };
    for (RRNodeId candidate : targets) {
        if (values.contains(candidate)) { ++targeted_hits_; continue; }
        if (used >= call_end) { ++targeted_unknown_; continue; }
        auto key = std::make_pair(endpoint, reverse);
        auto state = frontiers_.find(key);
        if (state == frontiers_.end()) {
            if (frontiers_.size() >= frontier_slots_) {
                auto victim = std::min_element(frontiers_.begin(), frontiers_.end(),
                    [](const auto& a, const auto& b) { return a.second.used < b.second.used; });
                frontiers_.erase(victim); ++frontier_evictions_;
            }
            frontier_restarts_ += used > 0;
            state = frontiers_.emplace(key, FrontierState{std::make_unique<H3dPersistentBidirectional>(size_t(endpoint)), 0}).first;
            frontier_peak_states_ = std::max(frontier_peak_states_, frontiers_.size());
        }
        state->second.used = ++frontier_clock_;
        size_t remaining = call_end - used;
        size_t allowance = targeted_quota_ ? std::min(targeted_quota_, remaining) : remaining;
        VTR_ASSERT(edge_source_index_[candidate] >= 0);
        auto answer = state->second.search->query(nodes + edge_source_index_[candidate], allowance,
                                                  200000, 500000, terminal, outgoing, incoming);
        ++targeted_queries_;
        size_t charged = answer.forward_settled + answer.reverse_settled;
        used += charged; targeted_settled_ += charged;
        frontier_forward_work_ += answer.forward_settled;
        frontier_reverse_work_ += answer.reverse_settled;
        VTR_ASSERT(used <= call_end && used <= budget_);
        targeted_quota_stops_ += allowance < remaining && answer.stop == H3dPersistentBidirectional::Stop::WORK_LIMIT;
        for (auto [raw, distance] : answer.new_terminals) {
            RRNodeId identity = edge_sources_.at(raw - nodes);
            auto old = values.find(identity);
            if (old != values.end() && std::abs(old->second-distance) > 1.e-18)
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Conflicting persistent terminal distances");
            values.emplace(identity, distance); ++frontier_terminals_;
        }
        if (answer.exact) { values[candidate] = *answer.exact; ++targeted_exact_; }
        else { ++targeted_unknown_; targeted_memory_stops_ += answer.stop == H3dPersistentBidirectional::Stop::MEMORY_LIMIT; }
        if (trace_bounds_ || clamp_bounds_) {
            auto bound = state->second.search->unsettled_lower_bound();
            if (bound && std::isfinite(*bound)) {
                auto& saved = (reverse ? reverse_bounds_ : forward_bounds_)[endpoint];
                if (*bound > saved) { saved = *bound; ++bound_updates_; }
            }
        }
        if (!frontier_retain_) {
            // The lifetime endpoint work ledger and exact-answer map above
            // survive. Rebuilding the endpoint frontier is charged normally.
            frontiers_.erase(state);
            ++frontier_discards_;
        }
    }
    return values;
}

double H3dDelayPlan::lower_bound_seconds(RRNodeId endpoint, bool reverse) const {
    const auto& bounds = reverse ? reverse_bounds_ : forward_bounds_;
    auto found = bounds.find(endpoint);
    return found == bounds.end() ? 0. : found->second;
}

double H3dDelayPlan::adjust_estimate_units(RRNodeId endpoint, bool reverse, double estimate) const {
    return clamp_bounds_ ? std::max(estimate, lower_bound_seconds(endpoint, reverse) / delay_unit_) : estimate;
}

H3dCandidatePath::Result H3dDelayPlan::probe_reverse_candidate(RRNodeId sink, RRNodeId entry, size_t work,
        double heuristic_per_grid_seconds, double toll_weight, float pres_fac,
        const std::unordered_set<RRNodeId>& owned) {
    VTR_ASSERT(supported_ && edge_encoding_ && heuristic_per_grid_seconds >= 0. && toll_weight >= 0.);
    const int layer=graph_.node_layer_low(sink);
    const auto key=std::make_pair(entry,layer);
    auto cached=candidate_boxes_.find(key);
    if (cached==candidate_boxes_.end()) {
        CandidateBox box{std::numeric_limits<int>::max(),std::numeric_limits<int>::min(),
                         std::numeric_limits<int>::max(),std::numeric_limits<int>::min()};
        for (auto edge:graph_.node_out_edges(entry)) {
            RRNodeId next=graph_.edge_sink_node(entry,edge);
            if (!h3d_crosses_layers(graph_,entry,next) || graph_.node_layer_low(next)!=layer) continue;
            box.xmin=std::min(box.xmin,int(graph_.node_xlow(next)));box.xmax=std::max(box.xmax,int(graph_.node_xhigh(next)));
            box.ymin=std::min(box.ymin,int(graph_.node_ylow(next)));box.ymax=std::max(box.ymax,int(graph_.node_yhigh(next)));
        }
        VTR_ASSERT(box.xmin<=box.xmax && box.ymin<=box.ymax);
        cached=candidate_boxes_.emplace(key,box).first;
    }
    const auto box=cached->second;
    const auto& routing=g_vpr_ctx.routing();
    auto heuristic=[&](size_t raw) {
        RRNodeId node(raw);
        int dx=std::max({0,box.xmin-int(graph_.node_xhigh(node)),int(graph_.node_xlow(node))-box.xmax});
        int dy=std::max({0,box.ymin-int(graph_.node_yhigh(node)),int(graph_.node_ylow(node))-box.ymax});
        return heuristic_per_grid_seconds*(double(dx)+double(dy));
    };
    auto expand=[&](size_t raw,auto visit) {
        RRNodeId current(raw);double toll=0.;auto type=graph_.node_type(current);
        if (toll_weight>0. && (type==e_rr_type::CHANX || type==e_rr_type::CHANY) && !owned.contains(current)) {
            const auto& info=routing.rr_node_route_inf[current];
            double price=double(info.acc_cost)*(1.+double(pres_fac)*std::max(0,info.occ()+1-graph_.node_capacity(current)));
            double bounded=std::isfinite(price) ? std::max(0.,price-1.)/std::max(1.,price) : 1.;
            toll=toll_weight*delay_unit_*bounded;
        }
        for (size_t i=reverse_start_[raw];i<reverse_start_[raw+1];++i) {
            const auto& pred=predecessors_[i];
            if (h3d_crosses_layers(graph_,pred.node,current)) {
                if (pred.node==entry) visit(graph_.num_nodes(),double(pred.delay),toll);
            } else if (graph_.node_layer_low(pred.node)==layer) {
                visit(size_t(pred.node),double(pred.delay),toll);
            }
        }
    };
    return H3dCandidatePath::query(size_t(sink),graph_.num_nodes(),work,16384,65536,expand,heuristic);
}

H3dDelayPlan::PathWitness H3dDelayPlan::path_witness(RRNodeId endpoint, bool reverse, RRNodeId entry) const {
    if (!cache_paths_) return {"disabled", 0., {}, {}};
    const auto& distances = reverse ? reverse_ : forward_;
    auto values = distances.find(endpoint);
    if (values == distances.end() || !values->second.contains(entry)) return {"unmeasured", 0., {}, {}};
    const auto& caches = reverse ? reverse_witness_ : forward_witness_;
    auto cached = caches.find(endpoint);
    if (cached == caches.end()) return {"cache_limit", 0., {}, {}};
    const auto& forest = cached->second;
    VTR_ASSERT(edge_source_index_[entry] >= 0);
    size_t current = graph_.num_nodes() + edge_source_index_[entry];
    std::vector<size_t> chain;
    std::vector<double> weights;
    while (current != size_t(endpoint)) {
        auto found = forest.find(current);
        VTR_ASSERT(found != forest.end() && chain.size() < forest.size());
        chain.push_back(current);
        weights.push_back(found->second.edge_weight);
        current = found->second.parent;
    }
    chain.push_back(size_t(endpoint));
    PathWitness answer{"measured", values->second.at(entry), {}, {}};
    if (reverse) {
        // The virtual terminal is the physical crossing entry. Its reverse
        // parent is the crossing destination; all subsequent edges lead to sink.
        chain.front() = size_t(entry);
        for (size_t node : chain) answer.nodes.push_back(RRNodeId(node));
        answer.edge_delays = std::move(weights);
    } else {
        // Remove the synthetic zero edge entry->terminal, then orient the
        // physical source-to-entry path in forward order.
        VTR_ASSERT(!weights.empty() && weights.front() == 0.);
        chain.erase(chain.begin());
        weights.erase(weights.begin());
        std::reverse(chain.begin(), chain.end());
        std::reverse(weights.begin(), weights.end());
        for (size_t node : chain) answer.nodes.push_back(RRNodeId(node));
        answer.edge_delays = std::move(weights);
    }
    VTR_ASSERT(answer.nodes.size() == answer.edge_delays.size() + 1);
    return answer;
}

void H3dDelayPlan::log() const {
    if(compact_paths_)
        VTR_LOG("H3D_CANDIDATE_PATH_COMPACT full_records=%zu compact_records=%zu\n",
                witness_full_records_,witness_compact_records_);
    if (cache_paths_ && !trace_paths_)
        VTR_LOG("H3D_CANDIDATE_PATH_CAPTURE records=%zu record_limit=%zu skipped_queries=%zu forward_endpoints=%zu reverse_endpoints=%zu\n",
                witness_records_, witness_record_limit_, witness_cache_skips_, forward_witness_.size(), reverse_witness_.size());
    if (trace_paths_)
        VTR_LOG("H3D_PATH_CACHE records=%zu record_limit=%zu skipped_queries=%zu forward_endpoints=%zu reverse_endpoints=%zu\n",
                witness_records_, witness_record_limit_, witness_cache_skips_, forward_witness_.size(), reverse_witness_.size());
    VTR_LOG("H3D_DELAY_BOUNDS trace=%d updates=%zu forward_endpoints=%zu reverse_endpoints=%zu clamp=%d\n",
            trace_bounds_, bound_updates_, forward_bounds_.size(), reverse_bounds_.size(), clamp_bounds_);
    VTR_LOG("H3D_PERSISTENT_DELAY enabled=%d slots=%zu peak_states=%zu evictions=%zu restarts=%zu forward_settled=%zu reverse_settled=%zu terminal_certificates=%zu ledger_endpoints=%zu retain=%d discards=%zu live_states=%zu\n",
            persistent_frontier_, frontier_slots_, frontier_peak_states_, frontier_evictions_, frontier_restarts_, frontier_forward_work_, frontier_reverse_work_, frontier_terminals_, forward_work_.size()+reverse_work_.size(), frontier_retain_, frontier_discards_, frontiers_.size());
    VTR_LOG("H3D_TARGET_REUSE enabled=%d settled_labels=%zu inserted=%zu duplicates=%zu uncertified_edges=%zu capacity_stops=%zu endpoint_entry_cap=200000\n",
            targeted_reuse_, reuse_labels_, reuse_inserted_, reuse_duplicates_, reuse_uncertified_, reuse_capacity_stops_);
    VTR_LOG("H3D_TARGET_DELAY queries=%zu cache_hits=%zu exact=%zu unknown=%zu settled=%zu memory_stops=%zu endpoint_budget=%zu candidate_quota=%zu quota_stops=%zu\n",
            targeted_queries_, targeted_hits_, targeted_exact_, targeted_unknown_, targeted_settled_, targeted_memory_stops_, budget_, targeted_quota_, targeted_quota_stops_);
    VTR_LOG("H3D_DELAY queries=%zu settled=%zu truncated=%zu cache_hits=%zu cached_endpoints=%zu\n",
            queries_, settled_, truncated_, hits_, forward_.size()+reverse_.size());
}
