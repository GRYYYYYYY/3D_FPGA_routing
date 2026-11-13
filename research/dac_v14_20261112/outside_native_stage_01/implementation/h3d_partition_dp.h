#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>
#include <vector>

#include "vtr_assert.h"

/** @brief A verified candidate's sink-side cost in the planning surrogate. */
struct t_h3d_candidate_cost {
    size_t channel;     ///< Index in the planner's candidate table, not an RR node id.
    double branch_cost; ///< Nonnegative sink-side surrogate cost; not final RC timing.
};

/** @brief One remote terminal and its individually reachable candidate channels. */
struct t_h3d_plan_leaf {
    int pin;                                      ///< Net pin index, unique among the leaves.
    int x;                                        ///< Sink x coordinate for deterministic spatial hierarchy.
    int y;                                        ///< Sink y coordinate for deterministic spatial hierarchy.
    std::vector<t_h3d_candidate_cost> candidates; ///< Sorted by channel, with no duplicate channels.
};

/** @brief Optimal plan within a fixed hierarchy and finite candidate sets. */
struct t_h3d_partition_plan {
    double cost = std::numeric_limits<double>::infinity(); ///< Surrogate objective, including each selected group opening.
    std::vector<std::pair<int, size_t>> assignment;        ///< Net pin to preferred physical-channel table index.
    size_t groups = 0;                                     ///< Number of shared groups in the hierarchical partition.
};

namespace h3d_detail {

/** @brief A subtree optimum and costs if all of its leaves share each common candidate. */
struct t_partial_plan {
    t_h3d_partition_plan best;                      ///< Shared-versus-split optimum.
    std::vector<t_h3d_candidate_cost> common_costs; ///< Sum of branch costs over all leaves for each common candidate.
};

/** @brief Recursively compare one shared crossing with the two child plans.
 *
 * Leaves are split by median along the wider coordinate range. The recurrence
 * is exact only for this fixed hierarchy and the supplied additive surrogate:
 * D(v) = min(min_c(open[c] + sum_{i in v} branch[i,c]), D(left)+D(right)).
 * Each shared candidate must be present in every descendant leaf's feasible set.
 * Neither arbitrary subset partitions nor joint detailed routing are optimized.
 */
inline t_partial_plan solve_partition(std::vector<t_h3d_plan_leaf> leaves,
                                      const std::vector<double>& opening_cost) {
    VTR_ASSERT(!leaves.empty());
    t_partial_plan result;
    if (leaves.size() == 1) {
        result.common_costs = leaves.front().candidates;
    } else {
        int xmin = leaves.front().x;
        int xmax = xmin;
        int ymin = leaves.front().y;
        int ymax = ymin;
        for (const auto& leaf : leaves) {
            xmin = std::min(xmin, leaf.x);
            xmax = std::max(xmax, leaf.x);
            ymin = std::min(ymin, leaf.y);
            ymax = std::max(ymax, leaf.y);
        }
        bool split_x = xmax - xmin >= ymax - ymin;
        std::stable_sort(leaves.begin(), leaves.end(), [split_x](const auto& lhs, const auto& rhs) {
            if (split_x && lhs.x != rhs.x)
                return lhs.x < rhs.x;
            if (!split_x && lhs.y != rhs.y)
                return lhs.y < rhs.y;
            return lhs.pin < rhs.pin;
        });
        auto midpoint = leaves.begin() + leaves.size() / 2;
        t_partial_plan left = solve_partition({leaves.begin(), midpoint}, opening_cost);
        t_partial_plan right = solve_partition({midpoint, leaves.end()}, opening_cost);

        result.best.cost = left.best.cost + right.best.cost;
        if (std::isfinite(result.best.cost)) {
            result.best.assignment = std::move(left.best.assignment);
            result.best.assignment.insert(result.best.assignment.end(), right.best.assignment.begin(), right.best.assignment.end());
            result.best.groups = left.best.groups + right.best.groups;
        }

        // Only intersect verified sets. A missing candidate is infeasible for
        // this subtree; geometric proximity is never a connectivity proof.
        size_t i = 0;
        size_t j = 0;
        while (i < left.common_costs.size() && j < right.common_costs.size()) {
            const auto& a = left.common_costs[i];
            const auto& b = right.common_costs[j];
            if (a.channel < b.channel) {
                ++i;
            } else if (a.channel > b.channel) {
                ++j;
            } else {
                result.common_costs.push_back({a.channel, a.branch_cost + b.branch_cost});
                ++i;
                ++j;
            }
        }
    }

    for (const auto& candidate : result.common_costs) {
        VTR_ASSERT(candidate.channel < opening_cost.size());
        double shared_cost = opening_cost[candidate.channel] + candidate.branch_cost;
        // Prefer a shared group on a tie, then the lower candidate index.
        if (shared_cost < result.best.cost || (shared_cost == result.best.cost && result.best.groups > 1)) {
            result.best.cost = shared_cost;
            result.best.groups = 1;
            result.best.assignment.clear();
            for (const auto& leaf : leaves)
                result.best.assignment.emplace_back(leaf.pin, candidate.channel);
        }
    }
    return result;
}

} // namespace h3d_detail

/** @brief Plan shared or split vertical channels using a finite hierarchical DP.
 *
 * Opening costs include the source-side access and one channel charge. Branch
 * costs are counted for each terminal, so downstream shared wires/RC loads are
 * not modeled exactly. A non-finite optimum means this restricted candidate
 * problem has no plan; it is never proof that the RRG is unroutable.
 */
inline t_h3d_partition_plan h3d_plan_partition(const std::vector<t_h3d_plan_leaf>& leaves,
                                               const std::vector<double>& opening_cost) {
    if (leaves.empty())
        return {0., {}, 0};
    for (double cost : opening_cost)
        VTR_ASSERT(std::isfinite(cost) && cost >= 0.);
    for (const auto& leaf : leaves) {
        for (size_t i = 0; i < leaf.candidates.size(); ++i) {
            const auto& candidate = leaf.candidates[i];
            VTR_ASSERT(candidate.channel < opening_cost.size());
            VTR_ASSERT(std::isfinite(candidate.branch_cost) && candidate.branch_cost >= 0.);
            VTR_ASSERT(i == 0 || leaf.candidates[i - 1].channel < candidate.channel);
        }
    }
    t_h3d_partition_plan result = h3d_detail::solve_partition(leaves, opening_cost).best;
    std::sort(result.assignment.begin(), result.assignment.end());
    return result;
}

/** @brief Evaluate a fixed pin assignment under the same deterministic hierarchy.
 * A maximal subtree assigned one candidate pays its opening once; a split
 * subtree pays each child. Missing/nonfinite assignments are unavailable.
 */
inline double h3d_assignment_cost(std::vector<t_h3d_plan_leaf> leaves,
                                  const std::vector<double>& opening,
                                  const std::vector<std::pair<int, size_t>>& assignment) {
    if (leaves.empty()) return 0.;
    size_t shared = opening.size();
    bool common = true;
    double branches = 0.;
    for (const auto& leaf : leaves) {
        auto found = std::find_if(assignment.begin(), assignment.end(), [&](const auto& a) { return a.first == leaf.pin; });
        if (found == assignment.end()) return std::numeric_limits<double>::infinity();
        auto candidate = std::find_if(leaf.candidates.begin(), leaf.candidates.end(), [&](const auto& c) { return c.channel == found->second; });
        if (candidate == leaf.candidates.end()) return std::numeric_limits<double>::infinity();
        if (shared == opening.size()) shared = found->second;
        common &= shared == found->second;
        branches += candidate->branch_cost;
    }
    if (common) return opening.at(shared) + branches;
    int xmin = leaves.front().x, xmax = xmin, ymin = leaves.front().y, ymax = ymin;
    for (const auto& leaf : leaves) {
        xmin = std::min(xmin, leaf.x); xmax = std::max(xmax, leaf.x);
        ymin = std::min(ymin, leaf.y); ymax = std::max(ymax, leaf.y);
    }
    bool split_x = xmax - xmin >= ymax - ymin;
    std::stable_sort(leaves.begin(), leaves.end(), [split_x](const auto& a, const auto& b) {
        if (split_x && a.x != b.x) return a.x < b.x;
        if (!split_x && a.y != b.y) return a.y < b.y;
        return a.pin < b.pin;
    });
    auto middle = leaves.begin() + leaves.size() / 2;
    return h3d_assignment_cost({leaves.begin(), middle}, opening, assignment)
           + h3d_assignment_cost({middle, leaves.end()}, opening, assignment);
}
