#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <limits>
#include <queue>
#include <stdexcept>
#include <utility>
#include <vector>

/** Bounded Dijkstra: only settled terminal distances are returned. A budget
 * exhaustion is an unknown result for absent terminals, never infeasibility.
 * The caller supplies directed edges; terminal nodes are not expanded. */
class H3dDelaySearch {
  public:
    struct Result {
        std::vector<std::pair<size_t, double>> terminals;
        size_t settled = 0;
        bool budget_exhausted = false;
    };
    explicit H3dDelaySearch(size_t nodes)
        : distance_(nodes), generation_(nodes, 0), settled_(nodes, 0) {}

    template<typename Terminal, typename Expand>
    Result query(size_t source, size_t budget, Terminal terminal, Expand expand) {
        if (++epoch_ == 0) {
            std::fill(generation_.begin(), generation_.end(), 0);
            std::fill(settled_.begin(), settled_.end(), 0);
            epoch_ = 1;
        }
        using Item = std::pair<double, size_t>;
        std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;
        distance_.at(source) = 0.;
        generation_[source] = epoch_;
        queue.emplace(0., source);
        Result result;
        while (!queue.empty() && result.settled < budget) {
            auto [cost, node] = queue.top();
            queue.pop();
            if (settled_[node] == epoch_ || cost != distance_[node]) continue;
            settled_[node] = epoch_;
            ++result.settled;
            if (terminal(node)) {
                result.terminals.emplace_back(node, cost);
                continue;
            }
            expand(node, [&](size_t next, double weight) {
                if (!std::isfinite(weight) || weight < 0.)
                    throw std::invalid_argument("H3D Dijkstra requires finite nonnegative weights");
                double candidate = cost + weight;
                if (generation_.at(next) != epoch_ || candidate < distance_[next]) {
                    generation_[next] = epoch_;
                    distance_[next] = candidate;
                    queue.emplace(candidate, next);
                }
            });
        }
        result.budget_exhausted = !queue.empty();
        return result;
    }

  private:
    std::vector<double> distance_;
    std::vector<uint32_t> generation_, settled_;
    uint32_t epoch_ = 0;
};
