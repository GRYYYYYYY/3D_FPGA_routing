#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <optional>
#include <queue>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/** @brief Candidate-specific directed shortest path with one shared work cap.
 * Forward and reverse adapters must describe exactly the same immutable graph.
 * Costs must be finite and nonnegative. A meeting path is only an upper bound;
 * it becomes a measurement after the two frontier lower bounds prove optimality.
 * This one-shot prototype deliberately exposes no partially completed state.
 */
class H3dBidirectionalDelay {
  public:
    enum class Stop { EXACT, UNREACHABLE, WORK_LIMIT, MEMORY_LIMIT };
    struct Result {
        Stop stop;
        std::optional<double> exact;
        size_t forward_settled, reverse_settled, peak_labels, peak_heap;
    };

    template<typename Forward, typename Reverse>
    static Result query(size_t source, size_t target, size_t budget,
                        size_t label_limit, size_t heap_limit,
                        Forward forward, Reverse reverse) {
        if (label_limit < 2 || heap_limit < 2)
            throw std::invalid_argument("bidirectional storage limits must admit two roots");
        if (source == target) return {Stop::EXACT, 0., 0, 0, 0, 0};
        Side a(source), b(target);
        double best = std::numeric_limits<double>::infinity();
        size_t peak_labels = 2, peak_heap = 2;
        bool memory_hit = false;
        auto result = [&](Stop stop) {
            return Result{stop, stop == Stop::EXACT ? std::optional<double>(best) : std::nullopt,
                          a.settled.size(), b.settled.size(), peak_labels, peak_heap};
        };
        auto meet = [&](size_t node, double value, const Side& other) {
            auto opposite = other.distance.find(node);
            if (opposite != other.distance.end()) best = std::min(best, value + opposite->second);
        };
        auto step = [&](Side& active, const Side& other, auto expand) {
            auto [cost, node] = active.heap.top(); active.heap.pop();
            active.settled.insert(node);
            meet(node, cost, other);
            expand(node, [&](size_t next, double delay) {
                if (!std::isfinite(delay) || delay < 0.)
                    throw std::invalid_argument("finite nonnegative delay required");
                if (memory_hit || active.settled.contains(next)) return;
                double value = cost + delay;
                if (!std::isfinite(value)) throw std::overflow_error("delay sum overflow");
                auto old = active.distance.find(next);
                if (old != active.distance.end() && old->second <= value) return;
                if ((old == active.distance.end() && a.distance.size() + b.distance.size() >= label_limit)
                    || a.heap.size() + b.heap.size() >= heap_limit) {
                    memory_hit = true; return;
                }
                active.distance[next] = value;
                active.heap.emplace(value, next);
                meet(next, value, other);
                peak_labels = std::max(peak_labels, a.distance.size() + b.distance.size());
                peak_heap = std::max(peak_heap, a.heap.size() + b.heap.size());
            });
        };
        while (true) {
            a.clean(); b.clean();
            if (memory_hit) return result(Stop::MEMORY_LIMIT);
            if (a.heap.empty() || b.heap.empty())
                return result(std::isfinite(best) ? Stop::EXACT : Stop::UNREACHABLE);
            double lo_a = a.heap.top().first, lo_b = b.heap.top().first;
            if (std::isfinite(best) && lo_a + lo_b >= best) return result(Stop::EXACT);
            if (a.settled.size() + b.settled.size() >= budget) return result(Stop::WORK_LIMIT);
            if (lo_a < lo_b || (lo_a == lo_b && a.settled.size() <= b.settled.size()))
                step(a, b, forward);
            else step(b, a, reverse);
        }
    }

  private:
    struct Side {
        using Item = std::pair<double,size_t>;
        std::unordered_map<size_t,double> distance;
        std::unordered_set<size_t> settled;
        std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;
        explicit Side(size_t root) {distance[root] = 0.; heap.emplace(0., root);}
        void clean() {
            while (!heap.empty()) {
                auto [cost,node] = heap.top();
                if (!settled.contains(node) && cost == distance.at(node)) break;
                heap.pop();
            }
        }
    };
};
