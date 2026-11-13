#pragma once

#include <vector>
#include "netlist_fwd.h"
#include "rr_graph_fwd.h"

/** @brief Static XY guidance, projected onto all layers; never a physical route. */
struct t_h3d_planar_guide {
    int xmin = 0;                 ///< Left edge of the net's XY box.
    int ymin = 0;                 ///< Bottom edge of the net's XY box.
    int width = 0;                ///< Number of stored X coordinates.
    int height = 0;               ///< Number of stored Y coordinates.
    float beta = 0.f;             ///< Maximum fractional congestion discount.
    std::vector<float> potential; ///< Normalized [0,1] soft preference per XY cell.
    std::vector<double> benefit;  ///< Shared-trunk proxy for each real terminal.
};

/** @brief Initialize opt-in literature-inspired controls and their explicit LUTs. */
void h3d_control_iteration(int iteration, bool is_flat);
/** @brief Compute one FLUTE topology per selected net on its first routing attempt. */
void h3d_control_prepare(ParentNetId net);
/** @brief Read the static field; nullptr means original VPR cost. */
const t_h3d_planar_guide* h3d_control_guide(ParentNetId net);
/** @brief Apply the documented sharing/criticality order only for the field control. */
void h3d_control_sort(ParentNetId net, std::vector<size_t>& pins, const std::vector<float>& criticality);
/** @brief Congestion multiplier in [1-beta,1], sampled at the resource midpoint. */
float h3d_control_multiplier(const t_h3d_planar_guide& guide, RRNodeId node);
/** @brief Report all preprocessing time, retained cells and explicit fallbacks. */
void h3d_control_log();
