#pragma once

#include "h3d_delay_search.h"
#include "h3d_persistent_bidirectional.h"
#include "h3d_candidate_path.h"
#include "rr_graph_view.h"
#include <map>
#include <memory>
#include <unordered_map>
#include <unordered_set>

struct t_bb;

/** Exact first-crossing switch-delay distances on verified zero-RC graphs.
 * Reverse edges are an analysis index only; the router's graph is unchanged. */
class H3dDelayPlan {
  public:
    using Distances = std::unordered_map<RRNodeId, double>;
    H3dDelayPlan(const RRGraphView& graph, size_t budget, bool edge_encoding = false);
    const Distances& distances(RRNodeId endpoint, bool reverse);
    /** @brief Measure ordered targets within the lifetime budget and an optional
     * equal share of remaining work for remaining_users. Unused work is retained.
     * The default of one user preserves the original request allowance. */
    const Distances& targeted_distances(RRNodeId endpoint, bool reverse, const std::vector<RRNodeId>& targets, size_t remaining_users = 1);
    /** @brief Uncharged lifetime work for this endpoint and query direction. */
    size_t remaining_work(RRNodeId endpoint, bool reverse) const;
    bool supported() const { return supported_; }
    double delay_unit() const { return delay_unit_; }
    struct WorkSnapshot { size_t queries, settled, hits; };
    WorkSnapshot work_snapshot() const { return {queries_,settled_,hits_}; }
    bool trace_bounds() const { return trace_bounds_; }
    bool clamp_bounds() const { return clamp_bounds_; }
    double lower_bound_seconds(RRNodeId endpoint, bool reverse) const;
    double adjust_estimate_units(RRNodeId endpoint, bool reverse, double estimate) const;
    struct PathWitness {
        const char* status;
        double delay_seconds = 0.;
        std::vector<RRNodeId> nodes; ///< Always in actual forward RR-edge order.
        std::vector<double> edge_delays; ///< nodes[i] -> nodes[i+1].
    };
    bool trace_paths() const { return trace_paths_; }
    bool cache_paths() const { return cache_paths_; }
    PathWitness path_witness(RRNodeId endpoint, bool reverse, RRNodeId entry) const;
    /** @brief Independent reverse candidate query; never modifies old distance
     * caches. Result edges are in the reverse adapter's order, ending at the
     * virtual target graph.num_nodes(), which represents this crossing entry. */
    H3dCandidatePath::Result probe_reverse_candidate(RRNodeId sink, RRNodeId entry, size_t work,
        double heuristic_per_grid_seconds, double toll_weight, float pres_fac,
        const std::unordered_set<RRNodeId>& owned);
    struct ResidualAnswer {
        int status=-4; bool cache_hit=false; size_t origin=0,cache_records=0,cache_stops=0;
        H3dCandidatePath::Result query{H3dCandidatePath::Stop::WORK_LIMIT,std::nullopt,std::nullopt,std::nullopt,std::nullopt,{},0,0,0};
    };
    ResidualAnswer probe_residual_sources(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,
        const t_bb& box,int mode,double heuristic_per_grid,size_t search);
    void log() const;

  private:
    struct ResidualSuffix { size_t origin;std::vector<H3dCandidatePath::Edge> reverse_edges; };
    std::map<std::pair<RRNodeId,RRNodeId>,std::vector<ResidualSuffix>> residual_cache_;
    size_t residual_cache_records_=0,residual_cache_stops_=0;
    struct Predecessor { RRNodeId node; float delay; };
    const RRGraphView& graph_;
    size_t budget_;
    size_t targeted_quota_ = 0; ///< Optional per-candidate work slice; cumulative endpoint budget remains unchanged.
    size_t targeted_quota_stops_ = 0; ///< Local work slices exhausted before endpoint budget.
    bool targeted_reuse_ = false; ///< Cache incidental exact endpoint-side crossing distances from targeted queries.
    size_t reuse_labels_ = 0, reuse_inserted_ = 0, reuse_duplicates_ = 0, reuse_uncertified_ = 0, reuse_capacity_stops_ = 0;
    bool edge_encoding_ = false;                       ///< Use virtual query terminals for actual crossing-edge sources.
    std::vector<RRNodeId> edge_sources_;                ///< Query terminal index to real crossing source.
    vtr::vector<RRNodeId, int> edge_source_index_;        ///< Real source ID to synthetic query terminal index.
    bool supported_ = true;
    double delay_unit_ = 1.e-10;
    std::vector<size_t> reverse_start_;
    std::vector<Predecessor> predecessors_;
    std::unique_ptr<H3dDelaySearch> search_;
    std::unordered_map<RRNodeId, Distances> forward_, reverse_;
    Distances empty_;
    size_t queries_ = 0, settled_ = 0, truncated_ = 0, hits_ = 0;
    bool trace_paths_ = false; ///< Decision-neutral canonical shortest witnesses, legacy queries only.
    bool cache_paths_ = false; ///< Capture settled paths independently of verbose diagnostics.
    bool compact_paths_ = false; ///< Cache only ancestors of measured terminals.
    size_t witness_full_records_ = 0, witness_compact_records_ = 0;
    using WitnessForest = std::unordered_map<size_t, H3dDelaySearch::WitnessStep>;
    std::unordered_map<RRNodeId, WitnessForest> forward_witness_, reverse_witness_;
    size_t witness_records_ = 0, witness_cache_skips_ = 0;
    static constexpr size_t witness_record_limit_ = 2000000;
    struct CandidateBox { int xmin, xmax, ymin, ymax; };
    std::map<std::pair<RRNodeId,int>,CandidateBox> candidate_boxes_; ///< Immutable geometry only, never current prices.
    std::unordered_map<RRNodeId, size_t> forward_work_, reverse_work_; ///< Work survives changing candidate requests.
    size_t targeted_queries_ = 0, targeted_hits_ = 0, targeted_exact_ = 0, targeted_unknown_ = 0; ///< Candidate-level accounting.
    size_t targeted_settled_ = 0, targeted_memory_stops_ = 0; ///< Both directions charged together.
    size_t validation_queries_ = 0;                     ///< Limit the optional unbounded reference comparisons to eight queries.
    const Distances& persistent_distances_(RRNodeId endpoint, bool reverse, const std::vector<RRNodeId>& targets, size_t call_end);
    struct FrontierState { std::unique_ptr<H3dPersistentBidirectional> search; size_t used; };
    std::map<std::pair<RRNodeId, bool>, FrontierState> frontiers_; ///< Bounded LRU; exact answer caches and work ledgers outlive eviction.
    bool persistent_frontier_ = false;
    bool frontier_retain_ = true; ///< Ablation: discard only the search frontier after each target, retaining exact values and work charges.
    size_t frontier_discards_ = 0;
    bool trace_bounds_ = false; ///< Decision-neutral diagnostic; no scoring clamp is applied.
    bool clamp_bounds_ = false; ///< Separate opt-in score change, never applied to exact measurements.
    std::unordered_map<RRNodeId, double> forward_bounds_, reverse_bounds_; ///< Certified maxima survive frontier eviction.
    size_t bound_updates_ = 0;
    size_t frontier_slots_ = 8, frontier_clock_ = 0, frontier_evictions_ = 0, frontier_restarts_ = 0;
    size_t frontier_forward_work_ = 0, frontier_reverse_work_ = 0, frontier_terminals_ = 0, frontier_peak_states_ = 0;
};
