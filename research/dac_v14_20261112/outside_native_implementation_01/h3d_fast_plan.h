#pragma once

#include <memory>
#include <set>
#include <unordered_map>
#include <vector>

#include "h3d_reachability.h"
#include "h3d_routing.h"
#include "h3d_delay_plan.h"
#include "h3d_plan_profile.h"
#include "h3d_partition_dp.h"
#include "rr_graph_view.h"
#include "vtr_vector.h"

/** @brief SCC-backed finite candidate result; all costs remain planning proxies. */
struct t_h3d_fast_plan {
    std::vector<t_h3d_connection_guide> guides; ///< Per-terminal soft preferences.
    bool prior_table_diagnosed = false; ///< Opt-in diagnostic counters refer to an evaluated finite table.
    size_t prior_leaves = 0, prior_pairs = 0; ///< Current eligible table leaves and representable old choices.
    size_t prior_multiple = 0, prior_outside_table = 0; ///< Old guides with non-singleton choices or absent candidates.
    size_t prior_branch_missing = 0, prior_branch_nonfinite = 0, prior_opening_nonfinite = 0; ///< Unavailable old costs after table lookup.
    std::vector<int> prior_empty_pins; ///< Current leaves without any old preferred candidate, diagnostic only.
    bool refresh_clear = false; ///< Proposed deactivation because no remote pin remains eligible.
    bool refresh_accepted = false;                 ///< Candidate assignment passes same-cost hysteresis.
    double proposed_cost = 0., previous_cost = 0.; ///< Current surrogate values on identical finite table.
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
    t_h3d_fast_plan plan(ParentNetId net, const std::vector<float>& criticality, const std::vector<RRNodeId>& previous_channels, float pres_fac, size_t candidate_count, float opening_weight, float miss_weight, bool use_tree, float min_criticality = 0.f, const std::vector<t_h3d_connection_guide>* prior_guides = nullptr, double refresh_margin = .05, bool trace_prior = false, const std::vector<size_t>* refresh_targets = nullptr);

    /** @brief Report cache, candidate and high-fanout fallback counts. */
    H3dDelayPlan::ResidualAnswer probe_residual(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,const t_bb& bb,int mode,size_t search) {
        if(!delay_plan_)return {};
        return delay_plan_->probe_residual_sources(sink,sources,bb,mode,4.*delay_plan_->delay_unit()/std::max(1.,mean_span_),search);
    }
    void log() const;

    /** @brief Opt-in real-RRG adapter check against independent planar BFS. */
    void validate_against_bfs();

  private:
    /** @brief Reachable component set for one source or reverse sink query. */
    const std::vector<int>& reach_(RRNodeId endpoint, bool reverse);
    /** @brief Cached immutable closure view, avoiding full endpoint expansion. */
    const H3dReachabilityView& reach_view_(RRNodeId endpoint, bool reverse);

    /** @brief Test an actual directed source->channel->sink walk using SCC intersections. */
    bool feasible_(RRNodeId source, size_t channel, RRNodeId sink);

    /** @brief Gather a bounded spatial shortlist near endpoints, their corridor and net centroid. */
    std::vector<size_t> nearby_(RRNodeId source, RRNodeId sink, int center_x, int center_y, size_t target) const;

    /** @brief Geometric hop proxy, not shortest graph distance or physical RC delay. */
    double proxy_(RRNodeId endpoint, size_t channel) const;

    /** @brief Diversity selection within a cost-ranked, finite feasible list. */
    std::vector<size_t> diversify_(const std::vector<std::pair<double, size_t>>& ranked, size_t count) const;
    bool probe_candidates_(ParentNetId net, size_t plan_id, const std::vector<RRNodeId>& terminals,
        const std::vector<float>& criticality, const std::vector<size_t>& targets, float pres_fac,
        const std::vector<size_t>& table, const std::vector<double>& openings,
        std::vector<t_h3d_plan_leaf>& leaves, const t_h3d_partition_plan& planned,
        const std::unordered_map<int,const H3dDelayPlan::Distances*>& reverse, const std::set<int>& timed);

    bool trace_outside_=false;
    size_t outside_plan_=0,outside_trace_rows_=0;
    H3dPlanProfile profile_;                                           ///< Optional disjoint stage accounting.
    size_t reach_misses_ = 0;                                          ///< Endpoint closure cache misses.
    double reach_miss_seconds_ = 0.;                                   ///< Inclusive closure time, overlaps planner phases.
    const RRGraphView& graph_;                                          ///< Exact immutable graph used by detailed routing.
    double timing_guide_weight_ = 0.;                                  ///< Bounded timing-preference amplitude in graph delay units.
    bool bounded_critical_guide_=false;
    bool bounded_cap_only_=false;
    double bounded_critical_beta_=0.; ///< Explicit zero is a critical no-extra-guide ablation.
    double exit_price_weight_ = 0.; ///< Opt-in bounded feasible-destination congestion premium during selective refresh only.
    size_t exit_price_pairs_ = 0, exit_price_positive_ = 0, exit_price_edges_ = 0; ///< Per-refresh cached pairs, positive surcharges and tested cross edges.
    bool timing_regret_ = false; ///< Restrict timing guidance to measured positive alternative delay gaps.
    size_t equivalent_guide_cap_ = 0; ///< Opt-in total acceptable crossings per singleton DP guide, preserving its chosen crossing.
    size_t equivalent_guide_pins_ = 0, equivalent_guide_added_ = 0; ///< Expanded connections and additional exactly measured alternatives.
    size_t timing_regret_guides_ = 0, timing_regret_pairs_ = 0; ///< Connections with positive penalties and stored alternative entries.
    bool refresh_independent_ = false; ///< Same-table independent top-1 only during target-restricted feedback; initial shared planning unchanged.
    size_t refresh_shared_calls_ = 0, refresh_independent_calls_ = 0; ///< Nonempty finite refresh tables actually solved.
    bool independent_ = false;                                        ///< Same-table independent top-1 solver control.
    size_t timing_guides_ = 0;                                         ///< Selected guides with at least one measured side.
    bool targeted_delay_ = false;                                      ///< Candidate-specific bidirectional search, mixed scoring only.
    bool criticality_query_order_ = false; ///< Allocate shared source query work to critical pins first; DP pin order stays fixed.
    bool balance_source_queries_ = false; ///< Divide remaining source work among remaining pins without increasing lifetime/candidate limits.
    bool source_geometry_floor_ = false; ///< Keep the original geometric prior as a floor for unknown source estimates; exact distances unchanged.
    size_t source_floor_selected_ = 0; ///< Selected unknown-source candidates whose fitted scale is below the unit prior.
    bool trace_estimates_ = false; ///< Decision-neutral candidate component records for independent distance validation.
    bool trace_guide_margin_ = false; ///< Diagnostic leaf-local surrogate margins; not a shared-DP or physical-delay confidence bound.
    bool trace_dp_sensitivity_ = false; ///< Diagnostic exact fixed-hierarchy exclusion costs, no change to guidance.
    bool trace_retained_prefix_ = false; ///< Read-only retained edge/RC observations on finite target-refresh tables.
    double retained_opening_credit_ = 0.; ///< Refresh-only credit for the base opening charge of an already owned entry; congestion premiums remain.
    bool retained_source_cost_ = false; ///< Separate refresh ablation: use expandable retained-entry partial Tdel for source scoring.
    size_t retained_trace_plans_ = 0; ///< Diagnostic-only refresh identity, including explicitly uncovered calls.
    size_t path_trace_rows_ = 0, path_trace_omitted_ = 0; ///< Bounded, read-only witness telemetry.
    size_t path_measured_[2] = {0, 0}, path_unmeasured_[2] = {0, 0}, path_cache_limit_[2] = {0, 0};
    int candidate_path_mode_ = 0; ///< 0 off,1 uniform,2 spatial,3 spatial plus bounded current-price toll; query only.
    size_t candidate_path_plans_=0,candidate_path_records_=0,candidate_path_calls_=0,candidate_path_hits_=0;
    size_t candidate_path_work_=0,candidate_path_found_=0,candidate_path_exact_=0,candidate_path_memory_=0;
    double candidate_path_seconds_=0.;
    double candidate_path_score_weight_=0.,candidate_path_score_seconds_=0.,candidate_path_resolve_seconds_=0.;
    bool candidate_path_use_cached_=false; ///< Current-price observations from already-settled reverse witnesses.
    double candidate_path_delay_weight_=0.; ///< Separate calibrated physical sink-delay ablation.
    size_t candidate_path_delay_records_=0,candidate_path_delay_changed_=0;
    bool source_empty_reverse_=false; ///< Revalidate old skip under candidate-level physical sink scoring.
    size_t empty_reverse_requests_=0,empty_reverse_queries_=0,empty_reverse_work_=0,empty_reverse_hits_=0;
    size_t empty_reverse_measured_=0,empty_reverse_rows_=0,empty_reverse_omitted_=0;
    bool source_coverage_skip_=false; ///< Original available<need reverse gate; separate changed-score ablation.
    size_t coverage_gate_checks_=0,coverage_gate_skips_=0,coverage_gate_rows_=0,coverage_gate_omitted_=0;
    size_t candidate_path_score_plans_=0,candidate_path_score_records_=0,candidate_path_score_observed_=0,candidate_path_score_estimated_=0;
    size_t candidate_path_score_changed_=0,candidate_path_resolves_=0;
    bool dp_tie_pressure_ = false; ///< Zero extra congestion preference only on strict finite shared-DP exclusion ties.
    bool dp_margin_pressure_ = false; ///< Separate bounded relative surrogate-sensitivity pressure ablation.
    size_t estimate_trace_rows_ = 0; ///< Number of emitted candidate records across diagnostic phases.
    bool reverse_rerank_ = false; ///< Re-evaluate reverse targets after source measurements with unchanged limits and diversity.
    size_t reverse_rerank_pins_ = 0, reverse_rerank_changed_ = 0; ///< Pins considered and target sequences changed by source-informed reranking.
    size_t query_order_nets_ = 0, query_order_changed_ = 0; ///< Nonempty plans considered and reordered by query priority.
    bool mixed_delay_ = false;                                         ///< Experimental calibrated candidate-level delay, off by default.
    size_t mixed_pins_ = 0, mixed_informed_pins_ = 0;                    ///< Eligible and measurement-informed connections.
    size_t mixed_both_ = 0, mixed_source_only_ = 0, mixed_sink_only_ = 0, mixed_estimated_ = 0; ///< Sampled candidate coverage.
    size_t selected_delay_pins_ = 0, selected_delay_informed_ = 0; ///< Final selected-guide delay availability, separate from sampled-pool coverage.
    size_t selected_both_ = 0, selected_source_ = 0, selected_sink_ = 0, selected_estimated_ = 0; ///< Selected candidate counts, possibly several per pin.
    size_t bound_missing_sides_ = 0, bound_positive_sides_ = 0, bound_below_sides_ = 0; ///< Selected missing-side events, not cost-callback invocations.
    double bound_gap_units_ = 0.; ///< Sum of positive estimated-cost shortfalls in graph delay units.
    bool closure_view_ = false; ///< Exact union-view intersection without expanded endpoint vectors.
    size_t view_local_entries_ = 0, view_shared_references_ = 0; ///< Cache storage counters, no duplicated shared components.
    std::unordered_map<RRNodeId, H3dReachabilityView> source_views_, sink_views_; ///< Lifetime-safe immutable endpoint views.
    bool shared_closure_ = false; ///< Reuse exact large-SCC closures under static allowed masks.
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
