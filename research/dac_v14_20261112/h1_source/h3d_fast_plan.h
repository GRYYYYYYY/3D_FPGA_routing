#pragma once

#include <memory>
#include <unordered_map>
#include <vector>

#include "h3d_reachability.h"
#include "h3d_routing.h"
#include "h3d_delay_plan.h"
#include "rr_graph_view.h"
#include "vtr_vector.h"

/** @brief SCC-backed finite candidate result; all costs remain planning proxies. */
struct t_h3d_fast_plan {
    std::vector<t_h3d_connection_guide> guides; ///< Per-terminal soft preferences.
    size_t groups = 0;                          ///< Groups in the hierarchical DP.
    size_t no_candidate = 0;                    ///< Remote terminals delegated to baseline search.
};

/** @brief Reuse exact planar SCC reachability with bounded spatial candidate sampling.
 *
 * This accelerates the reference all-channel BFS planner. Reachability stays
 * exact, while cost changes to a documented geometric hop proxy. It must be
 * reported as a separate ablation, not as identical shortest-path planning.
 */
class H3dFastPlan {
  public:
    /** @brief Index the fixed RRG's planar components and vertical access endpoints. */
    explicit H3dFastPlan(const RRGraphView& graph, bool delay_cost = false, size_t delay_budget = 4096, bool edge_encoding = false);

    /** @brief Generate diverse feasible candidates and optionally solve a finite shared/split DP. */
    t_h3d_fast_plan plan(ParentNetId net, const std::vector<float>& criticality, const std::vector<RRNodeId>& previous_channels, float pres_fac, size_t candidate_count, float opening_weight, float miss_weight, bool use_tree, float min_criticality = 0.f);

    /** @brief Report cache, candidate and high-fanout fallback counts. */
    void log() const;

    /** @brief Opt-in real-RRG adapter check against independent planar BFS. */
    void validate_against_bfs();

  private:
    /** @brief Reachable component set for one source or reverse sink query. */
    const std::vector<int>& reach_(RRNodeId endpoint, bool reverse);

    /** @brief Test an actual directed source->channel->sink walk using SCC intersections. */
    bool feasible_(RRNodeId source, size_t channel, RRNodeId sink);

    /** @brief Gather a bounded spatial shortlist near endpoints, their corridor and net centroid. */
    std::vector<size_t> nearby_(RRNodeId source, RRNodeId sink, int center_x, int center_y, size_t target) const;

    /** @brief Geometric hop proxy, not shortest graph distance or physical RC delay. */
    double proxy_(RRNodeId endpoint, size_t channel) const;

    /** @brief Diversity selection within a cost-ranked, finite feasible list. */
    std::vector<size_t> diversify_(const std::vector<std::pair<double, size_t>>& ranked, size_t count) const;

    const RRGraphView& graph_;                                          ///< Exact immutable graph used by detailed routing.
    bool mixed_delay_ = false;                                         ///< Experimental calibrated candidate-level delay, off by default.
    size_t mixed_pins_ = 0, mixed_informed_pins_ = 0;                    ///< Eligible and measurement-informed connections.
    size_t mixed_both_ = 0, mixed_source_only_ = 0, mixed_sink_only_ = 0, mixed_estimated_ = 0; ///< Sampled candidate coverage.
    bool edge_encoding_ = false;                                       ///< Explicit imported edge encoding, independent of native CHANZ mode.
    std::unique_ptr<H3dReachabilityIndex> reachability_;                ///< SCC DAG for same-layer non-Z edges.
    std::vector<RRNodeId> channels_;                                    ///< Candidate table of native CHANZ resources.
    vtr::vector<RRNodeId, int> channel_index_;                          ///< RR id to candidate table index.
    std::vector<std::vector<int>> entries_;                             ///< Original predecessors' components for each channel.
    std::vector<std::vector<int>> exits_;                               ///< Original successors' components for each channel.
    std::vector<bool> forward_allowed_;                                 ///< Components able to reach a Z entry.
    std::vector<bool> reverse_allowed_;                                 ///< Components reachable from a Z exit.
    std::unordered_map<RRNodeId, std::vector<int>> source_cache_;       ///< Sparse forward component closures.
    std::unordered_map<RRNodeId, std::vector<int>> sink_cache_;         ///< Sparse reverse component closures.
    std::unordered_map<unsigned long long, std::vector<size_t>> sites_; ///< XY site to native channels.
    double mean_span_ = 1.;                                             ///< Mean planar channel span for proxy-unit normalization.
    size_t queries_ = 0;                                                ///< Exact feasibility queries.
    size_t spatial_candidates_ = 0;                                     ///< Sampled candidates before feasibility/ranking.
    size_t high_fanout_fallbacks_ = 0;                                  ///< Nets using independent guides instead of a large DP.
    std::unique_ptr<H3dDelayPlan> delay_plan_;
    size_t eligible_pins_ = 0, skipped_pins_ = 0, measured_pins_ = 0, unmeasured_pins_ = 0;
};
