#pragma once

#include <cmath>
#include <functional>
#include <limits>
#include <optional>
#include <queue>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/** @brief One endpoint's bounded Dijkstra frontier, reusable across target requests.
 * The directed graph, edge weights, terminal predicate and endpoint must stay
 * immutable for this object's lifetime. Terminal nodes are never expanded.
 * A fixed lifetime settlement budget is shared by all calls. Only settled
 * terminal values are exposed; misses remain unknown, never infeasible.
 * This prototype bounds one frontier. A production endpoint-cache manager
 * must additionally bound aggregate memory across simultaneously retained states.
 */
class H3dResumableDelaySearch {
  public:
    enum class e_stop { TARGETS_MET, QUOTA, TOTAL_BUDGET, COMPLETE, MEMORY_LIMIT };
    struct Result {
        size_t newly_settled = 0; ///< Actual work charged to this request.
        size_t total_settled = 0; ///< Actual work charged over the endpoint lifetime.
        e_stop stop;             ///< Explicit stop condition; absent targets stay unknown.
    };

    /** @brief Start one fixed endpoint; limits count entries, not guessed byte usage. */
    H3dResumableDelaySearch(size_t source, size_t total_budget, size_t node_limit, size_t heap_limit)
        : budget_(total_budget), node_limit_(node_limit), heap_limit_(heap_limit) {
        if (!node_limit || !heap_limit) throw std::invalid_argument("nonzero state limits required");
        distance_[source] = 0.;
        frontier_.emplace(0., source);
    }

    /** @brief Return only an exact settled terminal distance, if one is known. */
    std::optional<double> terminal_distance(size_t node) const {
        auto found = terminals_.find(node);
        if (found == terminals_.end()) return std::nullopt;
        return found->second;
    }

    /** @brief Work only until all requested terminals are settled or a bound is hit. */
    template<typename Terminal, typename Expand>
    Result query(const std::vector<size_t>& targets, size_t quota, Terminal terminal, Expand expand) {
        std::unordered_set<size_t> pending;
        for (size_t node : targets) {
            if (!terminal(node)) throw std::invalid_argument("requested goal is not a terminal");
            if (!terminals_.contains(node)) pending.insert(node);
        }
        size_t newly = 0;
        auto finish = [&](e_stop stop) { return Result{newly, settled_.size(), stop}; };
        while (true) {
            if (pending.empty()) return finish(e_stop::TARGETS_MET);
            // Partial expansion on a memory limit cannot be resumed safely.
            // Previously settled distances remain exact; no later work is allowed.
            if (memory_halted_) return finish(e_stop::MEMORY_LIMIT);
            while (!frontier_.empty()) {
                auto [cost, node] = frontier_.top();
                if (!settled_.contains(node) && cost == distance_.at(node)) break;
                frontier_.pop();
            }
            if (frontier_.empty()) return finish(e_stop::COMPLETE);
            if (settled_.size() >= budget_) return finish(e_stop::TOTAL_BUDGET);
            if (newly >= quota) return finish(e_stop::QUOTA);
            auto [cost, node] = frontier_.top(); frontier_.pop();
            settled_.insert(node); ++newly;
            if (terminal(node)) { terminals_[node] = cost; pending.erase(node); continue; }
            expand(node, [&](size_t next, double weight) {
                if (!std::isfinite(weight) || weight < 0.)
                    throw std::invalid_argument("finite nonnegative delay required");
                if (memory_halted_ || settled_.contains(next)) return;
                double candidate = cost + weight;
                if (!std::isfinite(candidate)) throw std::overflow_error("delay sum overflow");
                auto old = distance_.find(next);
                if (old != distance_.end() && candidate >= old->second) return;
                if ((old == distance_.end() && distance_.size() >= node_limit_) || frontier_.size() >= heap_limit_) {
                    memory_halted_ = true;
                    return;
                }
                distance_[next] = candidate;
                frontier_.emplace(candidate, next);
            });
        }
    }

  private:
    using Item = std::pair<double, size_t>;
    size_t budget_, node_limit_, heap_limit_; ///< Immutable lifetime work and per-state storage limits.
    bool memory_halted_ = false;              ///< Partial-expansion terminal state, never silently resumed.
    std::unordered_map<size_t, double> distance_; ///< Tentative labels, never exposed as measurements.
    std::unordered_map<size_t, double> terminals_; ///< Exact settled crossing distances.
    std::unordered_set<size_t> settled_;         ///< Each resource charged once across all requests.
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> frontier_; ///< Pending deterministic labels.
};
