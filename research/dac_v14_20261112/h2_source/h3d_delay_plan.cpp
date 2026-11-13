#include "h3d_delay_plan.h"
#include "h3d_crossing.h"

#include "globals.h"
#include "vtr_log.h"
#include "vpr_error.h"
#include <cstdlib>

H3dDelayPlan::H3dDelayPlan(const RRGraphView& graph, size_t budget, bool edge_encoding)
    : graph_(graph), budget_(budget), edge_encoding_(edge_encoding) {
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
    auto result = search_->query(size_t(endpoint), budget_, terminal, expand);
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

void H3dDelayPlan::log() const {
    VTR_LOG("H3D_DELAY queries=%zu settled=%zu truncated=%zu cache_hits=%zu cached_endpoints=%zu\n",
            queries_, settled_, truncated_, hits_, forward_.size()+reverse_.size());
}
