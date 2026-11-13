#pragma once

#include <algorithm>
#include <cstddef>
#include <numeric>
#include <utility>
#include <unordered_set>
#include <vector>

#include "vtr_assert.h"

/** @brief Exact directed reachability through a strongly connected component DAG.
 *
 * Vertex numbers here are generic graph indices. The VPR adapter supplies only
 * same-layer non-CHANZ edges, so SCC membership certifies a same-die walk without
 * inventing a reverse routing transition. No shortest-distance claim is made.
 */
class H3dReachabilityIndex {
  public:
    /** @brief Build SCCs iteratively (no deep recursion) and deduplicated DAGs. */
    H3dReachabilityIndex(size_t vertices, const std::vector<std::pair<size_t, size_t>>& edges) {
        std::vector<size_t> out_begin(vertices + 1, 0), in_begin(vertices + 1, 0);
        for (const auto& [source, sink] : edges) {
            VTR_ASSERT(source < vertices && sink < vertices);
            ++out_begin[source + 1];
            ++in_begin[sink + 1];
        }
        std::partial_sum(out_begin.begin(), out_begin.end(), out_begin.begin());
        std::partial_sum(in_begin.begin(), in_begin.end(), in_begin.begin());
        std::vector<size_t> successors(edges.size()), predecessors(edges.size());
        auto out_cursor = out_begin;
        auto in_cursor = in_begin;
        for (const auto& [source, sink] : edges) {
            successors[out_cursor[source]++] = sink;
            predecessors[in_cursor[sink]++] = source;
        }
        std::vector<bool> seen(vertices, false);
        std::vector<size_t> order;
        order.reserve(vertices);
        for (size_t root = 0; root < vertices; ++root) {
            if (seen[root]) continue;
            std::vector<std::pair<size_t, size_t>> stack{{root, out_begin[root]}};
            seen[root] = true;
            while (!stack.empty()) {
                auto& [node, cursor] = stack.back();
                if (cursor == out_begin[node + 1]) {
                    order.push_back(node);
                    stack.pop_back();
                } else {
                    size_t next = successors[cursor++];
                    if (!seen[next]) {
                        seen[next] = true;
                        stack.emplace_back(next, out_begin[next]);
                    }
                }
            }
        }
        components_.assign(vertices, -1);
        int component_count = 0;
        for (auto root = order.rbegin(); root != order.rend(); ++root) {
            if (components_[*root] >= 0) continue;
            std::vector<size_t> stack{*root};
            components_[*root] = component_count;
            while (!stack.empty()) {
                size_t node = stack.back();
                stack.pop_back();
                for (size_t edge = in_begin[node]; edge < in_begin[node + 1]; ++edge) {
                    size_t next = predecessors[edge];
                    if (components_[next] < 0) {
                        components_[next] = component_count;
                        stack.push_back(next);
                    }
                }
            }
            ++component_count;
        }
        forward_.resize(component_count);
        reverse_.resize(component_count);
        for (const auto& [source, sink] : edges) {
            int a = components_[source];
            int b = components_[sink];
            if (a != b) forward_[a].push_back(b);
        }
        for (int a = 0; a < component_count; ++a) {
            auto& outgoing = forward_[a];
            std::sort(outgoing.begin(), outgoing.end());
            outgoing.erase(std::unique(outgoing.begin(), outgoing.end()), outgoing.end());
            for (int b : outgoing)
                reverse_[b].push_back(a);
        }
    }

    /** @brief Map a graph vertex to its strongly connected component. */
    int component(size_t vertex) const { return components_.at(vertex); }

    /** @brief Number of components in the condensation graph. */
    size_t num_components() const { return forward_.size(); }

    /** @brief Mark components reachable from several seeds in a chosen direction. */
    std::vector<bool> mark(const std::vector<int>& seeds, bool backwards) const {
        const auto& adjacency = backwards ? reverse_ : forward_;
        std::vector<bool> result(adjacency.size(), false);
        std::vector<int> queue;
        for (int seed : seeds) {
            if (!result[seed]) {
                result[seed] = true;
                queue.push_back(seed);
            }
        }
        for (size_t i = 0; i < queue.size(); ++i)
            for (int next : adjacency[queue[i]])
                if (!result[next]) {
                    result[next] = true;
                    queue.push_back(next);
                }
        return result;
    }

    /** @brief Reach only relevant components; allowed must be closed toward the target seeds.
     *
     * For source-to-Z queries, allowed is the reverse reachability closure of
     * all Z-entry components; for Z-to-sink queries it is the forward closure
     * of all Z-exit components. This skips terminal dead ends without dropping
     * a valid route to/from a channel. Result is sorted for exact intersection.
     */
    std::vector<int> relevant_components(size_t vertex, bool backwards, const std::vector<bool>& allowed, bool large_closure = false) const {
        const auto& adjacency = backwards ? reverse_ : forward_;
        int root = component(vertex);
        if (!allowed[root]) return {};
        std::vector<int> visited{root};
        std::unordered_set<int> seen;
        if (large_closure) seen.insert(root);
        // Relevant pin-to-wire DAGs are small. Keeping the work set sparse
        // avoids clearing a device-sized bitmap for every endpoint query.
        for (size_t i = 0; i < visited.size(); ++i)
            for (int next : adjacency[visited[i]])
                if (allowed[next] && (large_closure ? seen.insert(next).second
                                                  : std::find(visited.begin(), visited.end(), next) == visited.end()))
                    visited.push_back(next);
        std::sort(visited.begin(), visited.end());
        return visited;
    }

  private:
    std::vector<int> components_;           ///< Component id for every generic input vertex.
    std::vector<std::vector<int>> forward_; ///< Deduplicated DAG successors.
    std::vector<std::vector<int>> reverse_; ///< DAG predecessors, used only for analysis.
};
