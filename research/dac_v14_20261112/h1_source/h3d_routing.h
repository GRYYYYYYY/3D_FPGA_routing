#pragma once

#include "router_stats.h"
#include "rr_graph_fwd.h"
#include <vector>

/** @brief Soft channel preference for a connection; other channels remain legal. */
struct t_h3d_connection_guide {
    std::vector<RRNodeId> preferred; ///< Sorted, individually reachable native CHANZ resources.
    float miss_weight = 0.f;         ///< Additional relative congestion charge for other CHANZ nodes.
    bool edge_encoding = false;      ///< Preferred IDs identify crossing-edge sources, not CHANZ nodes.
};

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
void h3d_prepare_net(ParentNetId net, int iteration, float pres_fac, const std::vector<float>& criticality);

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
