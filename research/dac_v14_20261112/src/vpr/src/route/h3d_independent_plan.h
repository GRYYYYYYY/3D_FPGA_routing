#pragma once

#include "h3d_partition_dp.h"

/** @brief Independent top-1 control over exactly the shared solver's finite table.
 * Empty leaves return an unavailable plan, preserving the shared fallback.
 * Candidate order is ascending; ties keep the smaller table index.
 */
inline t_h3d_partition_plan h3d_plan_independent(const std::vector<t_h3d_plan_leaf>& leaves,
                                               const std::vector<double>& opening) {
    t_h3d_partition_plan result{0., {}, 0};
    for (const auto& leaf : leaves) {
        double best = std::numeric_limits<double>::infinity();
        size_t chosen = 0;
        for (const auto& candidate : leaf.candidates) {
            VTR_ASSERT(candidate.channel < opening.size());
            double cost = opening[candidate.channel] + candidate.branch_cost;
            if (cost < best) {
                best = cost;
                chosen = candidate.channel;
            }
        }
        if(leaf.outside_cost<best) {best=leaf.outside_cost;chosen=opening.size();}
        if (!std::isfinite(best)) return {};
        result.cost += best;
        result.assignment.emplace_back(leaf.pin, chosen);
        if(chosen==opening.size())++result.outside_leaves;else ++result.groups;
    }
    std::sort(result.assignment.begin(), result.assignment.end());
    return result;
}
