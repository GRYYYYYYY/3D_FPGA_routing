#pragma once
#include "h3d_candidate_path.h"
#include <map>
#include <set>

/** @brief A bounded physical one-preferred-cross walk with a seed-prefix floor. */
struct TreePreferredQueryAnswer {
    H3dCandidatePath::Result result; ///< Physical costs include the restored common floor.
    double seed_floor; ///< Removed only from virtual terminal edges during the query.
    size_t admissible_seeds; ///< Eligible actual seeds admitted by the same BB predicate.
};

/** @brief Query a preferred-satisfied extension with optional inherited ancestry and fixed-tree terminals.
 * Reverse callbacks expose physical incoming edges. Only the engine's pending-g
 * frontier certifies a bound; order_distance may be an inadmissible heuristic.
 * This is a physical walk model, not the full native routing-cost objective.
 */
template<typename Layer, typename Inside, typename Reverse, typename OrderDistance>
TreePreferredQueryAnswer query_tree_preferred(size_t node_count, size_t sink,
                                    const std::vector<std::pair<size_t,double>>& input_seeds,
                                    const std::set<size_t>& preferred,
                                    const std::set<size_t>& tree,
                                    const std::set<size_t>& inherited,
                                    bool allow_inherited, bool terminal_tree,
                                    Layer layer, Inside inside, Reverse reverse,
                                    OrderDistance order_distance, bool spatial, bool factor_prefix,
                                    size_t budget, size_t labels=16384, size_t heap=65536,
                                    const std::vector<std::tuple<size_t,size_t,double>>& crossings={},
                                    bool target_crossing=false) {
    std::map<size_t,double> seeds;
    for (auto [node, delay] : input_seeds) {
        if (node >= node_count || !std::isfinite(delay) || delay < 0.)
            throw std::invalid_argument("invalid actual seed");
        if (!inside(node)) continue;
        if (layer(node)==layer(sink) && !(allow_inherited && inherited.count(node))) continue;
        auto found=seeds.find(node);
        if (found==seeds.end() || delay<found->second) seeds[node]=delay;
    }
    double floor=0.;
    if (factor_prefix && !seeds.empty()) {
        floor=std::numeric_limits<double>::infinity();
        for (auto [node, delay] : seeds) floor=std::min(floor,delay);
    }
    auto expand=[&](size_t node, auto visit) {
        if (node==node_count) return;
        auto seed=seeds.find(node);
        if (seed!=seeds.end()) visit(node_count, seed->second-floor, 0.);
        // A fixed-tree extension attaches once. A tree node is either an
        // eligible actual seed goal or a dead end; never traverse through it.
        if (terminal_tree && tree.count(node)) return;
        reverse(node,[&](size_t from, double delay) {
            if (!inside(from)) return;
            if (layer(from)==layer(node)
                || (layer(node)==layer(sink) && layer(from)!=layer(sink) && preferred.count(from)))
                visit(from,delay,0.);
        });
    };
    // Mandatory-crossing geometry is an ordering estimate, never a lower bound.
    std::vector<std::pair<size_t,double>> suffix_targets;
    if (target_crossing) {
        for (auto [from,to,delay] : crossings) {
            if (!preferred.count(from) || !inside(from) || !inside(to)
                || layer(from)==layer(sink) || layer(to)!=layer(sink)) continue;
            double prefix=std::numeric_limits<double>::infinity();
            for (auto [seed,seed_delay] : seeds)
                if (layer(seed)==layer(from))
                    prefix=std::min(prefix,seed_delay-floor+order_distance(from,seed));
            if (std::isfinite(prefix)) suffix_targets.emplace_back(to,delay+prefix);
        }
    }
    auto heuristic=[&](size_t node) {
        if (!spatial || node==node_count || seeds.empty()) return 0.;
        double estimate=std::numeric_limits<double>::infinity();
        if (target_crossing && layer(node)==layer(sink)) {
            for (auto [head,prefix] : suffix_targets)
                estimate=std::min(estimate,prefix+order_distance(node,head));
            // A sink-layer seed can already satisfy the preferred crossing
            // through its retained root-to-seed ancestry, with no new crossing.
            if (allow_inherited)
                for (auto [seed,delay] : seeds)
                    if (layer(seed)==layer(sink))
                        estimate=std::min(estimate,delay-floor+order_distance(node,seed));
            return std::isfinite(estimate) ? estimate : 0.;
        }

        for (auto [seed,delay] : seeds)
            estimate=std::min(estimate,delay-floor+order_distance(node,seed));
        return estimate;
    };
    auto result=H3dCandidatePath::query(sink,node_count,budget,labels,heap,expand,heuristic,true);
    if (result.priced_upper_seconds) *result.priced_upper_seconds+=floor;
    if (result.physical_path_seconds) *result.physical_path_seconds+=floor;
    if (result.lower_seconds) *result.lower_seconds+=floor;
    return {std::move(result),floor,seeds.size()};
}
