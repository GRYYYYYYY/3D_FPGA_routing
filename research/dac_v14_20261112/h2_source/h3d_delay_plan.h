#pragma once

#include "h3d_delay_search.h"
#include "rr_graph_view.h"
#include <memory>
#include <unordered_map>

/** Exact first-crossing switch-delay distances on verified zero-RC graphs.
 * Reverse edges are an analysis index only; the router's graph is unchanged. */
class H3dDelayPlan {
  public:
    using Distances = std::unordered_map<RRNodeId, double>;
    H3dDelayPlan(const RRGraphView& graph, size_t budget, bool edge_encoding = false);
    const Distances& distances(RRNodeId endpoint, bool reverse);
    bool supported() const { return supported_; }
    double delay_unit() const { return delay_unit_; }
    void log() const;

  private:
    struct Predecessor { RRNodeId node; float delay; };
    const RRGraphView& graph_;
    size_t budget_;
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
    size_t validation_queries_ = 0;                     ///< Limit the optional unbounded reference comparisons to eight queries.
};
