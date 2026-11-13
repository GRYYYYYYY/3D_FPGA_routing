#pragma once

#include "router_stats.h"
#include "rr_graph_fwd.h"
#include <vector>
#include <algorithm>
#include <utility>

/** @brief Soft channel preference for a connection; other channels remain legal. */
struct t_h3d_connection_guide {
    std::vector<RRNodeId> preferred; ///< Sorted, individually reachable native CHANZ resources.
    float timing_miss_penalty = 0.f; ///< Search-only seconds, excluded from Tdel and STA.
    bool timing_regret = false; ///< Use only certified two-sided alternatives; absent entries carry no timing preference.
    std::vector<std::pair<RRNodeId, float>> timing_alternatives; ///< Sorted sparse crossing IDs and bounded search-only seconds.
    float miss_weight = 0.f;         ///< Additional relative congestion charge for other CHANZ nodes.
    bool edge_encoding = false;      ///< Preferred IDs identify crossing-edge sources, not CHANZ nodes.
    bool bounded_critical = false; ///< Replace extra crossing cost on actual critical setup searches.
    bool bounded_cap_only = false; ///< Preserve old operation unless its extra exceeds the bound.
    double bounded_reliability = 0.,bounded_unit_seconds = 0.,bounded_beta = 0.;
    float bounded_penalty_seconds = 0.f; ///< Search-only seconds, excluded from physical Tdel and STA.

    /** @brief Return an alternative-specific search preference without changing physical delay. */
    float timing_penalty(RRNodeId crossing) const {
        if (!timing_regret) return timing_miss_penalty;
        auto found = std::lower_bound(timing_alternatives.begin(), timing_alternatives.end(), crossing,
                                     [](const auto& item, RRNodeId node) { return item.first < node; });
        return found != timing_alternatives.end() && found->first == crossing ? found->second : 0.f;
    }
};

/** Read-only serial search diagnostics, separate from physical costs/state. */
bool h3d_trace_guide_influence();
struct t_bb;
bool h3d_trace_search_domain();
void h3d_domain_reset();
void h3d_domain_seed(RRNodeId node,float delay,float backward,float total,bool rcv);
void h3d_domain_search(RRNodeId sink,float criticality,const t_h3d_connection_guide* guide,const t_bb& bb,bool rcv);
bool h3d_bounded_critical_stage_active();
void h3d_influence_begin(ParentNetId net, int pin, RRNodeId sink, bool high_fanout,
                        float criticality, const t_h3d_connection_guide* guide);
void h3d_influence_edge(ParentNetId net, int pin, RRNodeId from, RRNodeId to, int sw,
                       bool configurable, float criticality, float before, float after,
                       float physical_delay, float timing_penalty, bool rcv,
                       const t_h3d_connection_guide& guide, bool bounded_applied=false,
                       float unbounded_congestion=0.f);

/** @brief Whether finite candidate planning is explicitly enabled. */
bool h3d_enabled();

/** @brief Explicit A4 whole-net/subtree ablations; other modes keep VPR's policy. */
bool h3d_force_whole_net();
bool h3d_force_subtree();

/** @brief Whether failed signal-net replacements must restore their prior complete tree. */
bool h3d_transactional();

/** @brief Observe whether each routed sink actually used its preferred crossing. */
void h3d_observe_net(ParentNetId net);

/** @brief Reject one completed replacement when an explicit test-only setting is enabled. */
bool h3d_test_rollback_once();

/** @brief Count a fully restored transaction. */
void h3d_record_rollback();

/** @brief Initialize graph indices for serial clustered routing, once per fixed-width trial. */
void h3d_prepare_iteration(int iteration, bool is_flat);

/** @brief Save this net's existing channels before VPR prunes/rips up its tree. */
void h3d_capture_net(ParentNetId net);

/** @brief Compute or reuse a finite candidate plan using real directed RRG reachability. */
void h3d_prepare_net(ParentNetId net, int iteration, float pres_fac, const std::vector<float>& criticality, const std::vector<size_t>& remaining_targets);

/** @brief Return a net's connection preference, or nullptr for unrestricted search. */
const t_h3d_connection_guide* h3d_connection_guide(ParentNetId net, int pin);

/** @brief Count an explicit no-guide search retry. */
void h3d_record_fallback();

/** @brief Read a nonnegative experimental CHANZ congestion-cost multiplier.
 * Zero (the default) leaves arithmetic on the baseline path unchanged.
 * This is an additional resource preference, not a replacement delay model.
 */
float h3d_vertical_weight();

/** @brief Emit optional per-iteration physical vertical occupancy and search work. */
void h3d_log_iteration(int iteration, float pres_fac, const RouterStats& stats);

/** @brief Bind guide state to VPR's selected best routing for final observation. */
void h3d_save_best_guides();
/** @brief Optionally release soft preferences after native legal convergence. */
void h3d_enter_legal_refinement(int iteration);
/** @brief Write optional per-connection trace against restored final route trees. */
void h3d_report_final_guides(bool success);
