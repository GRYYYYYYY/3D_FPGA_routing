#include "h3d_fast_plan.h"
#include "h3d_crossing.h"
#include "h3d_calibrated_cost.h"
#include "h3d_independent_plan.h"
#include "h3d_feedback_policy.h"
#include "h3d_timing_regret.h"
#include "h3d_equivalent_guides.h"
#include "h3d_exit_price.h"
#include "h3d_partition_sensitivity.h"

#include <cmath>
#include <chrono>
#include <bit>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <set>
#include <sstream>
#include <iomanip>
#include <cstring>

#include "globals.h"
#include "h3d_partition_dp.h"
#include "route_common.h"
#include "route_tree.h"
#include "vtr_log.h"
#include "vpr_error.h"

namespace {

/** @brief Pack nonnegative integer XY coordinates into a collision-free key. */
unsigned long long site_key(int x, int y) {
    return (static_cast<unsigned long long>(static_cast<unsigned>(x)) << 32) | static_cast<unsigned>(y);
}

/** @brief Whether two sorted component-id lists have a common member. */
bool intersects(const std::vector<int>& a, const std::vector<int>& b) {
    // Crossing-entry lists are often singletons, while their reachable closure
    // can contain hundreds of thousands of SB half-node components.
    if (a.size() > 8 * b.size()) {
        for (int value : b)
            if (std::binary_search(a.begin(), a.end(), value)) return true;
        return false;
    }
    if (b.size() > 8 * a.size()) return intersects(b, a);
    size_t i = 0, j = 0;
    while (i < a.size() && j < b.size()) {
        if (a[i] == b[j]) return true;
        if (a[i] < b[j])
            ++i;
        else
            ++j;
    }
    return false;
}

/** @brief Sort and deduplicate a small component list. */
void unique_components(std::vector<int>& values) {
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
}

} // namespace

H3dFastPlan::H3dFastPlan(const RRGraphView& graph, bool delay_cost, size_t delay_budget, bool edge_encoding)
    : graph_(graph), edge_encoding_(edge_encoding) {
    if(const char* value=std::getenv("VPR_H3D_TRACE_OUTSIDE")) {
        if(std::string(value)!="0" && std::string(value)!="1")VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_TRACE_OUTSIDE must be0/1");
        trace_outside_=std::string(value)=="1";
        const char* query=std::getenv("VPR_H3D_RESIDUAL_QUERY");
        if(trace_outside_ && (!query || std::string(query)!="reuse" || !delay_cost || !edge_encoding))VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Outside trace requires zeroRC delay planner, edge encoding and residual reuse mode");
    }
    const char* profile = std::getenv("VPR_H3D_PLAN_PROFILE");
    profile_.enabled = profile && std::string(profile) == "1";
    const char* shared = std::getenv("VPR_H3D_SHARED_CLOSURE");
    shared_closure_ = edge_encoding_ && shared && std::string(shared) == "1";
    const char* view = std::getenv("VPR_H3D_CLOSURE_VIEW");
    closure_view_ = view && std::string(view) == "1";
    if (closure_view_ && !shared_closure_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Closure views require shared closures on edge-encoded graphs");
    const char* generation = std::getenv("VPR_H3D_GENERATION_CLOSURE");
    bool generation_closure = generation && std::string(generation) == "1";
    VTR_LOG("H3D_REACH_MODE generation_closure=%d profile=%d\n", generation_closure, profile_.enabled);
    const char* mixed = std::getenv("VPR_H3D_MIXED_DELAY");
    if (mixed && std::string(mixed) != "0" && std::string(mixed) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_MIXED_DELAY must be 0 or 1");
    mixed_delay_ = mixed && std::string(mixed) == "1";
    const char* targeted = std::getenv("VPR_H3D_TARGET_DELAY");
    targeted_delay_ = targeted && std::string(targeted) == "1";
    if (targeted_delay_ && (!mixed_delay_ || !delay_cost || !edge_encoding_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Target delay requires mixed delay scoring on edge-encoded delay graphs");
    const char* query_order = std::getenv("VPR_H3D_QUERY_CRITICALITY_ORDER");
    if (query_order && std::string(query_order) != "0" && std::string(query_order) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_QUERY_CRITICALITY_ORDER must be 0 or 1");
    criticality_query_order_ = query_order && std::string(query_order) == "1";
    if (criticality_query_order_ && !targeted_delay_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Criticality query order requires candidate-targeted delay queries");
    const char* balanced = std::getenv("VPR_H3D_SOURCE_QUERY_SHARE");
    if (balanced && std::string(balanced) != "0" && std::string(balanced) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_SOURCE_QUERY_SHARE must be 0 or 1");
    balance_source_queries_ = balanced && std::string(balanced) == "1";
    const char* persistent = std::getenv("VPR_H3D_TARGET_FRONTIER");
    if (balance_source_queries_ && (!targeted_delay_ || !persistent || std::string(persistent) != "1"))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Source query sharing requires persistent candidate-targeted delay queries");
    const char* rerank = std::getenv("VPR_H3D_REVERSE_RERANK");
    if (rerank && std::string(rerank) != "0" && std::string(rerank) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_REVERSE_RERANK must be 0 or 1");
    reverse_rerank_ = rerank && std::string(rerank) == "1";
    if (reverse_rerank_ && !targeted_delay_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Reverse reranking requires candidate-targeted mixed delay scoring");
    const char* source_floor = std::getenv("VPR_H3D_SOURCE_GEOMETRY_FLOOR");
    if (source_floor && std::string(source_floor) != "0" && std::string(source_floor) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_SOURCE_GEOMETRY_FLOOR must be 0 or 1");
    source_geometry_floor_ = source_floor && std::string(source_floor) == "1";
    if (source_geometry_floor_ && (!mixed_delay_ || !delay_cost || !edge_encoding_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Source geometry floor requires mixed delay on edge-encoded delay graphs");
    const char* estimates = std::getenv("VPR_H3D_TRACE_ESTIMATES");
    if (estimates && std::string(estimates) != "0" && std::string(estimates) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_ESTIMATES must be 0 or 1");
    trace_estimates_ = estimates && std::string(estimates) == "1";
    const char* guide_margin = std::getenv("VPR_H3D_TRACE_GUIDE_MARGIN");
    if (guide_margin && std::string(guide_margin) != "0" && std::string(guide_margin) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_GUIDE_MARGIN must be 0 or 1");
    trace_guide_margin_ = guide_margin && std::string(guide_margin) == "1";
    const char* sensitivity = std::getenv("VPR_H3D_TRACE_DP_SENSITIVITY");
    if (sensitivity && std::string(sensitivity) != "0" && std::string(sensitivity) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_DP_SENSITIVITY must be 0 or 1");
    trace_dp_sensitivity_ = sensitivity && std::string(sensitivity) == "1";
    const char* tie_pressure = std::getenv("VPR_H3D_DP_TIE_PRESSURE");
    if (tie_pressure && std::string(tie_pressure) != "0" && std::string(tie_pressure) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DP_TIE_PRESSURE must be 0 or 1");
    dp_tie_pressure_ = tie_pressure && std::string(tie_pressure) == "1";
    const char* margin_pressure = std::getenv("VPR_H3D_DP_MARGIN_PRESSURE");
    if (margin_pressure && std::string(margin_pressure) != "0" && std::string(margin_pressure) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DP_MARGIN_PRESSURE must be 0 or 1");
    dp_margin_pressure_ = margin_pressure && std::string(margin_pressure) == "1";
    if (dp_margin_pressure_ && dp_tie_pressure_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Tie-only and relative-margin pressure are separate ablations");
    if (trace_dp_sensitivity_ && !trace_guide_margin_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "DP sensitivity diagnostic requires the paired local-margin trace");
    if (trace_estimates_ && !targeted_delay_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Estimate tracing requires candidate-targeted mixed delay scoring");
    const char* timing = std::getenv("VPR_H3D_TIMING_GUIDE");
    if (timing) {
        char* end = nullptr;
        timing_guide_weight_ = std::strtod(timing, &end);
        if (end == timing || *end || !std::isfinite(timing_guide_weight_) || timing_guide_weight_ < 0. || timing_guide_weight_ > 1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TIMING_GUIDE must be in [0,1]");
    }
    const char* timing_mode = std::getenv("VPR_H3D_TIMING_GUIDE_MODE");
    std::string mode = timing_mode ? timing_mode : "coverage";
    if (mode != "coverage" && mode != "regret")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TIMING_GUIDE_MODE must be coverage or regret");
    timing_regret_ = mode == "regret";
    if (timing_regret_ && (!mixed_delay_ || !edge_encoding_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Regret timing guidance requires mixed edge-delay scoring");
    const char* equivalent = std::getenv("VPR_H3D_EQUIVALENT_GUIDES");
    if (equivalent) {
        char* end = nullptr;
        long cap = std::strtol(equivalent, &end, 10);
        if (end == equivalent || *end || cap < 0 || cap > 16)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_EQUIVALENT_GUIDES must be an integer in [0,16]");
        equivalent_guide_cap_ = size_t(cap);
    }
    if (equivalent_guide_cap_ && (!mixed_delay_ || !edge_encoding_ || timing_guide_weight_ > 0. || timing_regret_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Equivalent guides require mixed edge scoring and a separate timing-guidance ablation");
    const char* feedback = std::getenv("VPR_H3D_FEEDBACK");
    if (equivalent_guide_cap_ && feedback && std::string(feedback) != "0")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Equivalent guides are currently an independent static-guide experiment");
    const char* exit_price = std::getenv("VPR_H3D_EXIT_PRICE");
    if (exit_price) {
        char* end = nullptr;
        exit_price_weight_ = std::strtod(exit_price, &end);
        if (end == exit_price || *end || !std::isfinite(exit_price_weight_) || exit_price_weight_ < 0. || exit_price_weight_ > 1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_EXIT_PRICE must be in [0,1]");
    }
    if (exit_price_weight_ > 0. && (!edge_encoding_ || !feedback || std::string(feedback) != "1"))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Exit pricing requires selective feedback on an edge-encoded graph");
    const char* assignment = std::getenv("VPR_H3D_ASSIGNMENT");
    std::string solver = assignment ? assignment : "shared";
    if (solver != "shared" && solver != "independent")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_ASSIGNMENT must be shared or independent");
    independent_ = solver == "independent";
    const char* refresh_assignment = std::getenv("VPR_H3D_REFRESH_ASSIGNMENT");
    std::string refresh_solver = refresh_assignment ? refresh_assignment : "inherit";
    if (refresh_solver != "inherit" && refresh_solver != "independent")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_REFRESH_ASSIGNMENT must be inherit or independent");
    refresh_independent_ = refresh_solver == "independent";
    if ((dp_tie_pressure_ || dp_margin_pressure_) && (independent_ || refresh_independent_ || timing_guide_weight_ > 0. || equivalent_guide_cap_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "DP tie pressure requires shared assignment and separate timing/equivalent-guide ablations");
    if (trace_dp_sensitivity_ && (independent_ || refresh_independent_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "DP sensitivity diagnostic requires shared assignment throughout");
    const char* target_feedback = std::getenv("VPR_H3D_TARGET_FEEDBACK");
    const char* retained_source = std::getenv("VPR_H3D_RETAINED_SOURCE_COST");
    if (retained_source && std::string(retained_source) != "0" && std::string(retained_source) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_RETAINED_SOURCE_COST must be 0 or 1");
    retained_source_cost_ = retained_source && std::string(retained_source) == "1";
    const char* retained_credit = std::getenv("VPR_H3D_RETAINED_OPENING_CREDIT");
    if (retained_credit) {
        char* end = nullptr;
        retained_opening_credit_ = std::strtod(retained_credit, &end);
        if (end == retained_credit || *end || !std::isfinite(retained_opening_credit_)
            || retained_opening_credit_ < 0. || retained_opening_credit_ > 1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_RETAINED_OPENING_CREDIT must be in [0,1]");
    }
    if (retained_opening_credit_ > 0.) {
        if (!edge_encoding_ || !closure_view_ || !delay_cost
            || !feedback || std::string(feedback) != "1"
            || !target_feedback || std::string(target_feedback) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Retained opening credit requires target feedback, edge delay scoring and cached closure views");
        VTR_LOG("H3D_RETAINED_OPENING credit=%.17g scope=refresh_owned_entry preserve_congestion_premium=1\n", retained_opening_credit_);
    }
    if (retained_source_cost_) {
        if (!edge_encoding_ || !closure_view_ || !delay_cost || mixed_delay_ || timing_guide_weight_ > 0.
            || retained_opening_credit_ > 0. || !feedback || std::string(feedback) != "1"
            || !target_feedback || std::string(target_feedback) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Retained source cost requires separate legacy-delay target feedback with cached closure views");
        VTR_LOG("H3D_RETAINED_SOURCE scope=refresh_expandable_entry physical_delay_modified=0 additional_queries=0\n");
    }
    const char* retained_prefix = std::getenv("VPR_H3D_TRACE_RETAINED_PREFIX");
    if (retained_prefix && std::string(retained_prefix) != "0" && std::string(retained_prefix) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_RETAINED_PREFIX must be 0 or 1");
    trace_retained_prefix_ = retained_prefix && std::string(retained_prefix) == "1";
    if (trace_retained_prefix_ && (!edge_encoding_ || !closure_view_ || !delay_cost
                                  || !feedback || std::string(feedback) != "1"
                                  || !target_feedback || std::string(target_feedback) != "1"))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Retained-prefix tracing requires target feedback, edge delay scoring and cached closure views");
    const char* candidate_path=std::getenv("VPR_H3D_CANDIDATE_PATH");
    if (candidate_path) {
        const std::string mode(candidate_path);
        if (mode=="off") candidate_path_mode_=0;
        else if (mode=="uniform") candidate_path_mode_=1;
        else if (mode=="spatial") candidate_path_mode_=2;
        else if (mode=="priced") candidate_path_mode_=3;
        else VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_CANDIDATE_PATH must be off, uniform, spatial or priced");
    }
    if (candidate_path_mode_ && (!trace_retained_prefix_ || targeted_delay_ || mixed_delay_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Candidate path prototype requires separate legacy-delay target-feedback prefix tracing");
    if(const char* text=std::getenv("VPR_H3D_CANDIDATE_PATH_SCORE")) {
        char* end=nullptr;candidate_path_score_weight_=std::strtod(text,&end);
        if(end==text || *end || !std::isfinite(candidate_path_score_weight_) || candidate_path_score_weight_<0. || candidate_path_score_weight_>1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_CANDIDATE_PATH_SCORE must be in [0,1]");
    }
    if(candidate_path_score_weight_>0. && candidate_path_mode_!=3)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Candidate price score requires the independently tested priced query mode");
    if(const char* text=std::getenv("VPR_H3D_CANDIDATE_PATH_USE_CACHED")) {
        if(std::string(text)!="0" && std::string(text)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_CANDIDATE_PATH_USE_CACHED must be 0 or 1");
        candidate_path_use_cached_=std::string(text)=="1";
    }
    if(candidate_path_use_cached_ && candidate_path_mode_!=3)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Cached observations require priced candidate query mode");
    if(const char* text=std::getenv("VPR_H3D_CANDIDATE_PATH_DELAY")) {
        char* end=nullptr;candidate_path_delay_weight_=std::strtod(text,&end);
        if(end==text || *end || !std::isfinite(candidate_path_delay_weight_) || candidate_path_delay_weight_<0. || candidate_path_delay_weight_>1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_CANDIDATE_PATH_DELAY must be in [0,1]");
    }
    if(candidate_path_delay_weight_>0. && !candidate_path_use_cached_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Physical sink-delay ablation requires captured legacy witnesses");
    if(const char* text=std::getenv("VPR_H3D_SOURCE_EMPTY_REVERSE")) {
        if(std::string(text)!="0" && std::string(text)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_SOURCE_EMPTY_REVERSE must be 0 or 1");
        source_empty_reverse_=std::string(text)=="1";
    }
    if(source_empty_reverse_) {
        const char* compact=std::getenv("VPR_H3D_CANDIDATE_PATH_COMPACT");
        if(candidate_path_delay_weight_<=0. || mixed_delay_ || targeted_delay_ || !compact || std::string(compact)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Source-empty reverse revalidation requires legacy physical-sink scoring with compact witnesses");
    }
    if(const char* text=std::getenv("VPR_H3D_SOURCE_COVERAGE_SKIP")) {
        if(std::string(text)!="0" && std::string(text)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_SOURCE_COVERAGE_SKIP must be 0 or 1");
        source_coverage_skip_=std::string(text)=="1";
    }
    if(source_coverage_skip_ && (source_empty_reverse_ || candidate_path_mode_!=3 || !candidate_path_use_cached_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Source-coverage skip ablation requires separate legacy cached-query mode without source-empty admission");
    if (refresh_independent_ && (independent_ || !feedback || std::string(feedback) != "1"
                                || !target_feedback || std::string(target_feedback) != "1"))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Independent refresh ablation requires initial shared planning and target-restricted feedback");
    if(const char* text=std::getenv("VPR_H3D_BOUNDED_CRITICAL_GUIDE")) {
        char* end=nullptr;bounded_critical_beta_=std::strtod(text,&end);bounded_critical_guide_=true;
        if(end==text || *end || !std::isfinite(bounded_critical_beta_) || bounded_critical_beta_<0. || bounded_critical_beta_>1.)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_BOUNDED_CRITICAL_GUIDE must be in [0,1]");
        if(!edge_encoding_ || !delay_cost || targeted_delay_ || mixed_delay_ || timing_guide_weight_>0. || timing_regret_)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Bounded critical guide requires separate legacy edge-delay scoring without old timing guidance");
    }
    if(const char* text=std::getenv("VPR_H3D_BOUNDED_CRITICAL_CAP_ONLY")) {
        if(std::string(text)!="0" && std::string(text)!="1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_BOUNDED_CRITICAL_CAP_ONLY must be0 or1");
        bounded_cap_only_=std::string(text)=="1";
    }
    if(bounded_cap_only_) {
        const char* late=std::getenv("VPR_H3D_BOUNDED_AFTER_LEGAL");
        if(!bounded_critical_guide_ || (late && std::string(late)=="1"))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Cap-only guide is an independent all-stage bounded policy");
    }
    VTR_LOG("H3D_EXPERIMENT mixed_delay=%d timing_guide=%g assignment=%s\n", mixed_delay_, timing_guide_weight_, solver.c_str());
    channel_index_.resize(graph_.num_nodes(), -1);
    size_t planar_count = 0;
    double planar_length = 0.;
    std::vector<std::pair<size_t, size_t>> planar_edges;
    for (RRNodeId node : graph_.nodes()) {
        if (edge_encoding_ && graph_.node_type(node) == e_rr_type::CHANZ)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Edge encoding requires single-layer RR nodes; mixed CHANZ encoding is unsupported");
        if (edge_encoding_ ? h3d_crossing_entry(graph_, node) : graph_.node_type(node) == e_rr_type::CHANZ) {
            if (edge_encoding_ && graph_.node_type(node) != e_rr_type::OPIN
                && !(graph_.node_type(node) == e_rr_type::CHANX && graph_.node_direction(node) == Direction::NONE))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unsupported crossing source %zu; expected OPIN or SB half-node", size_t(node));
            channel_index_[node] = channels_.size();
            sites_[site_key(graph_.node_xlow(node), graph_.node_ylow(node))].push_back(channels_.size());
            channels_.push_back(node);
            if (!edge_encoding_) continue;
        }
        if ((graph_.node_type(node) == e_rr_type::CHANX || graph_.node_type(node) == e_rr_type::CHANY)
            && (!edge_encoding_ || graph_.node_direction(node) != Direction::NONE)) {
            ++planar_count;
            planar_length += 1 + graph_.node_xhigh(node) - graph_.node_xlow(node)
                             + graph_.node_yhigh(node) - graph_.node_ylow(node);
        }
        for (auto edge : graph_.node_out_edges(node)) {
            RRNodeId sink = graph_.edge_sink_node(node, edge);
            if (graph_.node_type(sink) != e_rr_type::CHANZ
                && graph_.node_layer_low(node) == graph_.node_layer_high(node)
                && graph_.node_layer_low(sink) == graph_.node_layer_high(sink)
                && graph_.node_layer_low(node) == graph_.node_layer_low(sink))
                planar_edges.emplace_back(size_t(node), size_t(sink));
        }
    }
    if (planar_count) mean_span_ = planar_length / planar_count;
    reachability_ = std::make_unique<H3dReachabilityIndex>(graph_.num_nodes(), planar_edges, generation_closure);
    entries_.resize(channels_.size());
    exits_.resize(channels_.size());
    for (RRNodeId node : graph_.nodes()) {
        for (auto edge : graph_.node_out_edges(node)) {
            RRNodeId sink = graph_.edge_sink_node(node, edge);
            int source_z = channel_index_[node];
            int sink_z = channel_index_[sink];
            if (edge_encoding_) {
                if (h3d_crosses_layers(graph_, node, sink)) {
                    VTR_ASSERT(source_z >= 0);
                    entries_[source_z].push_back(reachability_->component(size_t(node)));
                    exits_[source_z].push_back(reachability_->component(size_t(sink)));
                }
                continue;
            }
            if (source_z < 0 && sink_z >= 0)
                entries_[sink_z].push_back(reachability_->component(size_t(node)));
            if (source_z >= 0 && sink_z < 0)
                exits_[source_z].push_back(reachability_->component(size_t(sink)));
        }
    }
    std::vector<int> all_entries, all_exits;
    for (size_t c = 0; c < channels_.size(); ++c) {
        unique_components(entries_[c]);
        unique_components(exits_[c]);
        all_entries.insert(all_entries.end(), entries_[c].begin(), entries_[c].end());
        all_exits.insert(all_exits.end(), exits_[c].begin(), exits_[c].end());
    }
    forward_allowed_ = reachability_->mark(all_entries, true);
    reverse_allowed_ = reachability_->mark(all_exits, false);
    if (shared_closure_) {
        const char* compact_env = std::getenv("VPR_H3D_COMPACT_CLOSURE");
        bool compact = compact_env && std::string(compact_env) == "1";
        reachability_->configure_shared_closures(forward_allowed_, reverse_allowed_, 4 * 1024 * 1024, 8, 64, compact);
        VTR_LOG("H3D_SHARED_STORAGE compact=%d logical_entries=%zu stored_words=%zu admitted=%zu refused=%zu\n", compact,
                reachability_->shared_logical_entries(), reachability_->shared_entries(),
                reachability_->shared_admitted(), reachability_->shared_refused());
        VTR_LOG("H3D_SHARED_CLOSURE entries=%zu entry_cap=4194304 hub_cap=8 min_members=64\n", reachability_->shared_entries());
    }
    VTR_LOG("H3D_SCC_INIT components=%zu planar_edges=%zu channels=%zu mean_planar_span=%g\n",
            reachability_->num_components(), planar_edges.size(), channels_.size(), mean_span_);
    if (std::getenv("VPR_H3D_VALIDATE_SCC")) validate_against_bfs();
    if (channels_.empty() && !edge_encoding_)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "No CHANZ candidates; select an explicit supported graph encoding");
    if (delay_cost) delay_plan_ = std::make_unique<H3dDelayPlan>(graph_, delay_budget, edge_encoding_);
    if(candidate_path_use_cached_ && (!delay_plan_ || !delay_plan_->cache_paths()))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Cached price observations require enabled legacy path capture");
}

void H3dFastPlan::validate_against_bfs() {
    std::vector<std::vector<RRNodeId>> predecessors(graph_.num_nodes());
    for (RRNodeId node : graph_.nodes())
        for (auto edge : graph_.node_out_edges(node))
            predecessors[size_t(graph_.edge_sink_node(node, edge))].push_back(node);
    auto bfs = [&](RRNodeId endpoint, bool backwards) {
        std::vector<bool> seen(graph_.num_nodes(), false), result(channels_.size(), false);
        std::vector<RRNodeId> frontier{endpoint};
        seen[size_t(endpoint)] = true;
        int layer = graph_.node_layer_low(endpoint);
        for (size_t i = 0; i < frontier.size(); ++i) {
            if (edge_encoding_) {
                RRNodeId current = frontier[i];
                if (!backwards && channel_index_[current] >= 0)
                    result[channel_index_[current]] = true;
                auto visit_edge = [&](RRNodeId next) {
                    if (backwards && h3d_crosses_layers(graph_, next, current)) {
                        VTR_ASSERT(channel_index_[next] >= 0);
                        result[channel_index_[next]] = true;
                    } else if (graph_.node_layer_low(next) == layer && !seen[size_t(next)]) {
                        seen[size_t(next)] = true;
                        frontier.push_back(next);
                    }
                };
                if (backwards) {
                    for (RRNodeId next : predecessors[size_t(current)]) visit_edge(next);
                } else {
                    for (auto edge : graph_.node_out_edges(current)) visit_edge(graph_.edge_sink_node(current, edge));
                }
                continue;
            }
            auto visit = [&](RRNodeId next) {
                if (seen[size_t(next)]) return;
                int z = channel_index_[next];
                if (z >= 0) {
                    seen[size_t(next)] = true;
                    result[z] = true;
                } else if (graph_.node_layer_low(next) == layer && graph_.node_layer_high(next) == layer) {
                    seen[size_t(next)] = true;
                    frontier.push_back(next);
                }
            };
            RRNodeId node = frontier[i];
            if (backwards) {
                for (RRNodeId next : predecessors[size_t(node)])
                    visit(next);
            } else {
                for (auto edge : graph_.node_out_edges(node))
                    visit(graph_.edge_sink_node(node, edge));
            }
        }
        return result;
    };
    size_t connections = 0, comparisons = 0, reachable = 0;
    for (const auto& terminals : g_vpr_ctx.routing().net_rr_terminals) {
        if (terminals.size() < 2 || terminals[0] == RRNodeId::INVALID()) continue;
        RRNodeId source = terminals[0];
        for (size_t pin = 1; pin < terminals.size() && connections < 32; ++pin) {
            RRNodeId sink = terminals[pin];
            if (sink == RRNodeId::INVALID() || graph_.node_layer_low(source) == graph_.node_layer_low(sink)) continue;
            auto from = bfs(source, false), to = bfs(sink, true);
            for (size_t c = 0; c < channels_.size(); ++c) {
                bool expected = from[c] && to[c];
                if (feasible_(source, c, sink) != expected)
                    VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "SCC/BFS mismatch for source %zu channel %zu sink %zu", size_t(source), size_t(channels_[c]), size_t(sink));
                ++comparisons;
                reachable += expected;
            }
            ++connections;
        }
        if (connections == 32) break;
    }
    VTR_LOG("H3D_SCC_VALIDATED connections=%zu channel_comparisons=%zu reachable=%zu\n", connections, comparisons, reachable);
}

const std::vector<int>& H3dFastPlan::reach_(RRNodeId endpoint, bool reverse) {
    auto& cache = reverse ? sink_cache_ : source_cache_;
    auto found = cache.find(endpoint);
    if (found != cache.end()) return found->second;
    auto start = profile_.enabled ? std::chrono::steady_clock::now() : std::chrono::steady_clock::time_point{};
    ++reach_misses_;
    auto result = shared_closure_ ? reachability_->shared_relevant_components(size_t(endpoint), reverse)
                                  : reachability_->relevant_components(size_t(endpoint), reverse, reverse ? reverse_allowed_ : forward_allowed_, edge_encoding_);
    if (profile_.enabled) reach_miss_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    return cache.emplace(endpoint, std::move(result)).first->second;
}

const H3dReachabilityView& H3dFastPlan::reach_view_(RRNodeId endpoint, bool reverse) {
    auto& cache = reverse ? sink_views_ : source_views_;
    auto found = cache.find(endpoint);
    if (found != cache.end()) return found->second;
    auto start = profile_.enabled ? std::chrono::steady_clock::now() : std::chrono::steady_clock::time_point{};
    ++reach_misses_;
    auto result = reachability_->shared_relevant_view(size_t(endpoint), reverse);
    view_local_entries_ += result.local_entries();
    view_shared_references_ += result.shared_references();
    if (profile_.enabled) reach_miss_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    return cache.emplace(endpoint, std::move(result)).first->second;
}

bool H3dFastPlan::feasible_(RRNodeId source, size_t channel, RRNodeId sink) {
    ++queries_;
    if (closure_view_)
        return reach_view_(source, false).intersects(entries_[channel]) && reach_view_(sink, true).intersects(exits_[channel]);
    return intersects(reach_(source, false), entries_[channel]) && intersects(reach_(sink, true), exits_[channel]);
}

double H3dFastPlan::proxy_(RRNodeId endpoint, size_t channel) const {
    RRNodeId z = channels_[channel];
    int distance = std::abs(graph_.node_xlow(endpoint) - graph_.node_xlow(z))
                   + std::abs(graph_.node_ylow(endpoint) - graph_.node_ylow(z));
    return 2. + distance / mean_span_;
}

std::vector<size_t> H3dFastPlan::nearby_(RRNodeId source, RRNodeId sink, int center_x, int center_y, size_t target) const {
    int sx = graph_.node_xlow(source), sy = graph_.node_ylow(source);
    int tx = graph_.node_xlow(sink), ty = graph_.node_ylow(sink);
    std::vector<std::pair<int, int>> points{{sx, sy}, {tx, ty}, {(sx + tx) / 2, (sy + ty) / 2}, {(3 * sx + tx) / 4, (3 * sy + ty) / 4}, {(sx + 3 * tx) / 4, (sy + 3 * ty) / 4}, {sx, ty}, {tx, sy}, {center_x, center_y}};
    std::set<size_t> selected;
    for (int radius = 0; radius <= 3 && selected.size() < target; ++radius) {
        for (const auto& [x, y] : points)
            for (int dx = -radius; dx <= radius; ++dx)
                for (int dy = -radius; dy <= radius; ++dy) {
                    if (std::max(std::abs(dx), std::abs(dy)) != radius || x + dx < 0 || y + dy < 0) continue;
                    auto site = sites_.find(site_key(x + dx, y + dy));
                    if (site != sites_.end()) selected.insert(site->second.begin(), site->second.end());
                }
    }
    return {selected.begin(), selected.end()};
}

std::vector<size_t> H3dFastPlan::diversify_(const std::vector<std::pair<double, size_t>>& ranked, size_t count) const {
    if (ranked.empty()) return {};
    std::vector<size_t> chosen{ranked.front().second};
    size_t shortlist = std::min(ranked.size(), count * 8);
    while (chosen.size() < count && chosen.size() < shortlist) {
        double best_score = -1.;
        size_t best = chosen.front();
        for (size_t i = 0; i < shortlist; ++i) {
            size_t c = ranked[i].second;
            if (std::find(chosen.begin(), chosen.end(), c) != chosen.end()) continue;
            int spread = std::numeric_limits<int>::max();
            for (size_t prior : chosen)
                spread = std::min(spread, std::abs(graph_.node_xlow(channels_[c]) - graph_.node_xlow(channels_[prior]))
                                              + std::abs(graph_.node_ylow(channels_[c]) - graph_.node_ylow(channels_[prior])));
            double score = (1. + spread) / (1. + ranked[i].first - ranked.front().first);
            if (score > best_score) {
                best_score = score;
                best = c;
            }
        }
        if (best_score < 0.) break;
        chosen.push_back(best);
    }
    return chosen;
}

t_h3d_fast_plan H3dFastPlan::plan(ParentNetId net, const std::vector<float>& criticality, const std::vector<RRNodeId>& previous_channels, float pres_fac, size_t candidate_count, float opening_weight, float miss_weight, bool use_tree, float min_criticality, const std::vector<t_h3d_connection_guide>* prior_guides, double refresh_margin, bool trace_prior, const std::vector<size_t>* refresh_targets) {
    H3dPlanProfile::Scope profile(profile_, prior_guides != nullptr);
    using Phase = H3dPlanProfile::Phase;
    const auto& routing = g_vpr_ctx.routing();
    const auto& terminals = routing.net_rr_terminals[net];
    const size_t prefix_trace = trace_retained_prefix_ && prior_guides ? ++retained_trace_plans_ : 0;
    RRNodeId source = terminals[0];
    t_h3d_fast_plan result;
    result.guides.resize(terminals.size());
    for (auto& guide : result.guides) guide.edge_encoding = edge_encoding_;
    std::vector<bool> active(terminals.size(), true);
    if (refresh_targets) {
        VTR_ASSERT(prior_guides && prior_guides->size() == terminals.size());
        std::fill(active.begin(), active.end(), false);
        for (size_t pin : *refresh_targets) {
            VTR_ASSERT(pin > 0 && pin < terminals.size() && !active.at(pin));
            active.at(pin) = true;
        }
        for (size_t pin = 0; pin < terminals.size(); ++pin)
            if (!active[pin]) result.guides[pin] = prior_guides->at(pin);
        VTR_LOG("H3D_TARGET_REFRESH net=%zu targets=%zu preserved=%zu\n",
                size_t(net), refresh_targets->size(), terminals.size() - 1 - refresh_targets->size());
    }
    std::vector<int> pins;
    int center_x = 0, center_y = 0;
    for (size_t pin = 1; pin < terminals.size(); ++pin)
        if (active[pin] && graph_.node_layer_low(source) != graph_.node_layer_low(terminals[pin])) {
            if (criticality[pin] < min_criticality) { ++skipped_pins_; continue; }
            ++eligible_pins_;
            pins.push_back(pin);
            center_x += graph_.node_xlow(terminals[pin]);
            center_y += graph_.node_ylow(terminals[pin]);
        }
    if (pins.empty()) {
        if (prefix_trace)
            VTR_LOG("H3D_PREFIX_SKIP plan=%zu net=%zu reason=no_eligible_pins\n", prefix_trace, size_t(net));
        if (prior_guides) {
            // Deactivation is a criticality eligibility change, not an
            // objective-improvement claim: no active eligible connection needs a guide.
            // In target feedback, other connections retain their prior guides.
            result.refresh_accepted = true;
            result.refresh_clear = true;
            VTR_LOG("H3D_REFRESH_CLEAR net=%zu reason=no_eligible_pins\n", size_t(net));
        }
        return result;
    }
    center_x /= pins.size();
    center_y /= pins.size();
    profile.enter(Phase::SOURCE);
    const H3dDelayPlan::Distances* forward = nullptr;
    if (delay_plan_ && delay_plan_->supported())
        forward = targeted_delay_ ? &delay_plan_->targeted_distances(source, false, {})
                                  : &delay_plan_->distances(source, false);
    std::unordered_map<int, const H3dDelayPlan::Distances*> reverse;
    std::set<int> timed;
    // Normalize observed delay by the same physical unit before fitting a
    // robust endpoint-local scale. Unknown distance is not infeasibility.
    auto calibrate = [&](RRNodeId endpoint, const H3dDelayPlan::Distances& distances) {
        std::vector<double> ratios;
        for (const auto& [node, delay] : distances) {
            int c = channel_index_[node];
            if (c >= 0) ratios.push_back(delay / delay_plan_->delay_unit() / proxy_(endpoint, c));
        }
        return h3d_calibrated_scale(std::move(ratios));
    };
    const bool mixed = mixed_delay_ && forward;
    double source_scale = mixed ? calibrate(source, *forward) : 1.;
    std::unordered_map<int, double> sink_scales;
    auto legacy_source_cost = [&](size_t c) {
        if (forward) {
            auto found = forward->find(channels_[c]);
            if (found != forward->end()) return found->second / delay_plan_->delay_unit();
        }
        // Bounded source measurements may not represent the unmeasured pool.
        // This prior floor is a model choice, not a certified distance bound.
        double scale = source_geometry_floor_ ? std::max(1., source_scale) : source_scale;
        double estimate = scale * proxy_(source, c);
        return delay_plan_ ? delay_plan_->adjust_estimate_units(source, false, estimate) : estimate;
    };
    std::unordered_map<RRNodeId, double> retained_source_units;
    if (retained_source_cost_ && prior_guides && delay_plan_ && delay_plan_->supported()
        && routing.route_trees[net]) {
        const double unit = delay_plan_->delay_unit();
        VTR_ASSERT(std::isfinite(unit) && unit > 0.);
        for (const auto& node : routing.route_trees[net]->all_nodes()) {
            if (channel_index_[node.inode] >= 0 && node.re_expand
                && std::isfinite(node.Tdel) && node.Tdel >= 0.)
                retained_source_units.emplace(node.inode, double(node.Tdel) / unit);
        }
    }
    auto source_cost = [&](size_t c) {
        auto found = retained_source_units.find(channels_[c]);
        return found == retained_source_units.end() ? legacy_source_cost(c) : found->second;
    };
    std::set<RRNodeId> owned;
    if (routing.route_trees[net])
        for (const auto& node : routing.route_trees[net]->all_nodes())
            if (channel_index_[node.inode] >= 0 || (exit_price_weight_ > 0. && prior_guides)) owned.insert(node.inode);
    auto opening = [&](size_t c) {
        RRNodeId node = channels_[c];
        const auto& info = routing.rr_node_route_inf[node];
        int demand = info.occ() + (owned.contains(node) ? 0 : 1);
        // Additional demand is zero for a retained channel of this net.
        double negotiated = info.acc_cost * (1. + pres_fac * std::max(0, demand - graph_.node_capacity(node)));
        if (retained_opening_credit_ > 0. && prior_guides && owned.contains(node)) {
            // The entry is already present in this net's pruned route tree.
            // Credit only its baseline opening component. Retain accumulated
            // and current overuse premiums, and do not change native prices,
            // feasibility, physical delay, branch costs or routing state.
            const double credit = retained_opening_credit_ * std::min(1., negotiated);
            return source_cost(c) + opening_weight * (negotiated - credit);
        }
        return source_cost(c) + opening_weight * negotiated;
    };
    auto branch_base = [&](int pin, size_t c) {
        if (mixed) {
            double sink_cost = proxy_(terminals[pin], c);
            bool measured = false;
            auto back = reverse.find(pin);
            if (back != reverse.end()) {
                auto found = back->second->find(channels_[c]);
                measured = found != back->second->end();
                sink_cost = measured ? found->second / delay_plan_->delay_unit() : sink_cost * sink_scales.at(pin);
            }
            if (!measured) sink_cost = delay_plan_->adjust_estimate_units(terminals[pin], true, sink_cost);
            return sink_cost * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * source_cost(c);
        }
        if (timed.contains(pin)) {
            const auto& distances = *reverse.at(pin);
            auto found = distances.find(channels_[c]);
            if (found == distances.end() || !forward->contains(channels_[c]))
                return std::numeric_limits<double>::infinity();
            return found->second / delay_plan_->delay_unit() * (1. + 4. * criticality[pin])
                   + 4. * criticality[pin] * source_cost(c);
        }
        // The unchanged legacy fallback uses geometry on both sides. In this
        // separate refresh experiment, substitute only an already expandable
        // retained source prefix. This is a current-tree observation, not a
        // final RC extension bound or a change to native physical delays.
        auto prefix = retained_source_units.find(channels_[c]);
        const double from = prefix == retained_source_units.end() ? proxy_(source, c) : prefix->second;
        return proxy_(terminals[pin], c) * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * from;
    };
    // Prices depend on this refresh's occupancy and present factor. Cache only
    // within the call, while reusing the static SCC endpoint reachability view.
    std::unordered_map<int, std::unordered_map<size_t, double>> exit_premiums;
    auto branch = [&](int pin, size_t c) {
        double base = branch_base(pin, c);
        if (exit_price_weight_ == 0. || !prior_guides || !std::isfinite(base)) return base;
        auto& cached = exit_premiums[pin];
        if (auto found = cached.find(c); found != cached.end()) return base + found->second;
        double best = std::numeric_limits<double>::infinity();
        RRNodeId best_exit = RRNodeId::INVALID();
        RRNodeId entry = channels_[c];
        for (auto edge : graph_.node_out_edges(entry)) {
            RRNodeId destination = graph_.edge_sink_node(entry, edge);
            if (!h3d_crosses_layers(graph_, entry, destination)) continue;
            ++exit_price_edges_;
            std::vector<int> component{reachability_->component(size_t(destination))};
            bool reaches_sink = closure_view_ ? reach_view_(terminals[pin], true).intersects(component)
                                              : intersects(reach_(terminals[pin], true), component);
            if (!reaches_sink) continue;
            const auto& info = routing.rr_node_route_inf[destination];
            int demand = info.occ() + (owned.contains(destination) ? 0 : 1);
            // Native search does not separately charge a nonconfigurable edge.
            double price = graph_.edge_is_configurable(entry, edge)
                               ? info.acc_cost * (1. + pres_fac * std::max(0, demand - graph_.node_capacity(destination)))
                               : 1.;
            if (price < best || (price == best && destination < best_exit)) {
                best = price;
                best_exit = destination;
            }
        }
        VTR_ASSERT(std::isfinite(best));
        double premium = h3d_exit_price_premium(best, opening_weight, exit_price_weight_);
        cached.emplace(c, premium);
        ++exit_price_pairs_;
        exit_price_positive_ += premium > 0.;
        if (premium > 0.)
            VTR_LOG("H3D_EXIT_PRICE net=%zu pin=%d candidate=%zu destination=%zu price=%.17g opening_weight=%.17g weight=%.17g premium=%.17g\n",
                    size_t(net), pin, size_t(entry), size_t(best_exit), best, double(opening_weight), exit_price_weight_, premium);
        return base + premium;
    };
    // Read-only observations: never query, recalibrate, sort, or alter a score.
    auto trace_estimate = [&](const char* phase, int pin, size_t c) {
        if (!trace_estimates_ || !mixed) return;
        RRNodeId node = channels_[c];
        auto back = reverse.find(pin);
        bool from = forward->contains(node);
        bool to = back != reverse.end() && back->second->contains(node);
        double sink_scale = back != reverse.end() ? sink_scales.at(pin) : 1.;
        double sink_proxy = proxy_(terminals[pin], c);
        double sink_value = to ? back->second->at(node) / delay_plan_->delay_unit()
                               : delay_plan_->adjust_estimate_units(terminals[pin], true, sink_proxy * sink_scale);
        double source_value = source_cost(c);
        double open_value = opening(c), branch_value = branch(pin, c);
        VTR_ASSERT(std::isfinite(open_value) && std::isfinite(branch_value));
        ++estimate_trace_rows_;
        VTR_LOG("H3D_ESTIMATE phase=%s net=%zu pin=%d source=%zu sink=%zu candidate=%zu criticality=%.17g source_known=%d sink_known=%d source_value=%.17g sink_value=%.17g source_scale=%.17g sink_scale=%.17g source_proxy=%.17g sink_proxy=%.17g opening=%.17g branch=%.17g unit=%.17g\n",
                phase, size_t(net), pin, size_t(source), size_t(terminals[pin]), size_t(node), double(criticality[pin]), int(from), int(to),
                source_value, sink_value, source_scale, sink_scale, proxy_(source, c), sink_proxy, open_value, branch_value, delay_plan_->delay_unit());
    };
    std::set<size_t> pool;
    // Each sink has its own reverse ledger, but source work is shared across
    // this net's pins. Only the measurement/candidate pass is reordered: keep
    // the original pins vector for DP topology and deterministic tie-breaking.
    auto query_pins = pins;
    ++query_order_nets_;
    if (criticality_query_order_) {
        std::stable_sort(query_pins.begin(), query_pins.end(), [&](int a, int b) {
            return criticality[a] > criticality[b];
        });
        query_order_changed_ += query_pins != pins;
    }
    size_t query_position = 0;
    for (int pin : query_pins) {
        size_t remaining_users = query_pins.size() - query_position++;
        profile.enter(Phase::CANDIDATES);
        auto candidates = nearby_(source, terminals[pin], center_x, center_y, candidate_count * 8);
        for (RRNodeId node : previous_channels)
            if (channel_index_[node] >= 0) candidates.push_back(channel_index_[node]);
        if (prior_guides)
            for (const auto& guide : *prior_guides)
                for (RRNodeId node : guide.preferred)
                    if (channel_index_[node] >= 0) candidates.push_back(channel_index_[node]);
        std::sort(candidates.begin(), candidates.end());
        candidates.erase(std::unique(candidates.begin(), candidates.end()), candidates.end());
        spatial_candidates_ += candidates.size();
        std::vector<std::pair<double, size_t>> ranked;
        for (size_t c : candidates)
            if (feasible_(source, c, terminals[pin])) ranked.emplace_back(opening(c) + branch(pin, c), c);
        // Spatial sampling failure is not infeasibility. Search the full
        // candidate table until a usable fallback set is found.
        if (ranked.empty())
            for (size_t c = 0; c < channels_.size() && ranked.size() < candidate_count * 8; ++c)
                if (feasible_(source, c, terminals[pin])) ranked.emplace_back(opening(c) + branch(pin, c), c);
        if (trace_estimates_) for (const auto& candidate : ranked) trace_estimate("pre", pin, candidate.second);
        profile.enter(Phase::DISTANCE);
        if (mixed && !ranked.empty()) {
            // Unlike the legacy all-or-nothing rule, reverse-only measurements
            // are useful even when the bounded source query found no candidate.
            std::vector<RRNodeId> query_targets;
            if (targeted_delay_) {
                // Targets use only current geometry, congestion, known distances
                // and SCC feasibility. No final-route information is consulted.
                std::sort(ranked.begin(), ranked.end());
                for (size_t c : diversify_(ranked, candidate_count)) query_targets.push_back(channels_[c]);
                size_t users = balance_source_queries_ ? remaining_users : 1;
                size_t before = balance_source_queries_ ? delay_plan_->remaining_work(source, false) : 0;
                forward = &delay_plan_->targeted_distances(source, false, query_targets, users);
                if (balance_source_queries_) {
                    size_t after = delay_plan_->remaining_work(source, false);
                    size_t allowance = before / users + (before % users != 0);
                    VTR_ASSERT(after <= before && before - after <= allowance);
                    VTR_LOG("H3D_SOURCE_SHARE net=%zu pin=%d source=%zu users=%zu remaining_before=%zu allowance=%zu remaining_after=%zu charged=%zu\n",
                            size_t(net), pin, size_t(source), users, before, allowance, after, before - after);
                }
                source_scale = calibrate(source, *forward);
                if (trace_estimates_) for (const auto& candidate : ranked) trace_estimate("source", pin, candidate.second);
                if (reverse_rerank_) {
                    // Source measurements can change which alternatives merit
                    // sink-side work. Reuse the same feasible population and
                    // diversity rule; unknown source costs retain calibration.
                    // Reverse requests still run even with no source coverage.
                    auto original_targets = query_targets;
                    for (auto& [cost, c] : ranked) cost = opening(c) + branch(pin, c);
                    std::sort(ranked.begin(), ranked.end());
                    query_targets.clear();
                    for (size_t c : diversify_(ranked, candidate_count)) query_targets.push_back(channels_[c]);
                    VTR_ASSERT(query_targets.size() == original_targets.size());
                    ++reverse_rerank_pins_;
                    reverse_rerank_changed_ += query_targets != original_targets;
                    size_t old_known = 0, new_known = 0, introduced = 0;
                    std::string old_ids, new_ids;
                    for (RRNodeId node : original_targets) {
                        old_known += forward->contains(node);
                        old_ids += std::to_string(size_t(node)) + ";";
                    }
                    for (RRNodeId node : query_targets) {
                        new_known += forward->contains(node);
                        introduced += std::find(original_targets.begin(), original_targets.end(), node) == original_targets.end();
                        new_ids += std::to_string(size_t(node)) + ";";
                    }
                    VTR_LOG("H3D_REVERSE_TARGETS net=%zu pin=%d targets=%zu changed=%d introduced=%zu old_source_known=%zu new_source_known=%zu old=%s new=%s\n",
                            size_t(net), pin, query_targets.size(), int(query_targets != original_targets), introduced,
                            old_known, new_known, old_ids.c_str(), new_ids.c_str());
                }
            }
            const auto& back = targeted_delay_ ? delay_plan_->targeted_distances(terminals[pin], true, query_targets)
                                               : delay_plan_->distances(terminals[pin], true);
            reverse[pin] = &back;
            sink_scales[pin] = calibrate(terminals[pin], back);
            ++mixed_pins_;
            size_t measured = 0;
            for (auto& [cost, c] : ranked) {
                bool from = forward->contains(channels_[c]);
                bool to = back.contains(channels_[c]);
                measured += from || to;
                mixed_both_ += from && to;
                mixed_source_only_ += from && !to;
                mixed_sink_only_ += !from && to;
                mixed_estimated_ += !from && !to;
                cost = opening(c) + branch(pin, c);
            }
            mixed_informed_pins_ += measured > 0;
        } else if (forward && (!forward->empty() || source_empty_reverse_) && !ranked.empty()) {
            bool skip_reverse=false;
            if(source_coverage_skip_) {
                ++coverage_gate_checks_;
                size_t available=0,need=std::min(candidate_count,ranked.size());
                for(const auto& [cost,c]:ranked)available+=forward->contains(channels_[c]);
                skip_reverse=available<need;
                if(skip_reverse) {
                    ++coverage_gate_skips_;++unmeasured_pins_;
                    if(coverage_gate_rows_<20000) {
                        ++coverage_gate_rows_;std::ostringstream entries;
                        for(const auto& [cost,c]:ranked) {
                            if(entries.tellp()>0)entries<<';';
                            entries<<size_t(channels_[c])<<','<<int(forward->contains(channels_[c]));
                        }
                        VTR_LOG("H3D_SOURCE_COVERAGE_SKIP net=%zu pin=%d source=%zu sink=%zu refresh=%d ranked=%zu need=%zu available=%zu entries=%s\n",
                                size_t(net),pin,size_t(source),size_t(terminals[pin]),int(prior_guides!=nullptr),ranked.size(),need,available,entries.str().c_str());
                    } else ++coverage_gate_omitted_;
                }
            }
            if(!skip_reverse) {
                H3dDelayPlan::WorkSnapshot before{0,0,0};
                if(source_empty_reverse_ && forward->empty())before=delay_plan_->work_snapshot();
                const auto& back = delay_plan_->distances(terminals[pin], true);
                reverse[pin] = &back;
                if(source_empty_reverse_ && forward->empty()) {
                    auto after=delay_plan_->work_snapshot();
                    ++empty_reverse_requests_;empty_reverse_queries_+=after.queries-before.queries;
                    empty_reverse_work_+=after.settled-before.settled;empty_reverse_hits_+=after.hits-before.hits;
                    empty_reverse_measured_+=back.size();
                    if(empty_reverse_rows_<20000) {
                        ++empty_reverse_rows_;
                        VTR_LOG("H3D_SOURCE_EMPTY_REVERSE net=%zu pin=%d source=%zu sink=%zu refresh=%d source_entries=0 ranked=%zu measured_entries=%zu before_queries=%zu after_queries=%zu before_settled=%zu after_settled=%zu before_hits=%zu after_hits=%zu\n",
                                size_t(net),pin,size_t(source),size_t(terminals[pin]),int(prior_guides!=nullptr),ranked.size(),back.size(),before.queries,after.queries,before.settled,after.settled,before.hits,after.hits);
                    } else ++empty_reverse_omitted_;
                }
                std::vector<size_t> covered;
                for (auto [cost, c] : ranked)
                    if (forward->contains(channels_[c]) && back.contains(channels_[c])) covered.push_back(c);
                // Preserve K alternatives when possible; a bounded search miss is
                // not a failed reachability proof and does not remove router edges.
                if (covered.size() >= std::min(candidate_count, ranked.size())) {
                    timed.insert(pin);
                    ranked.clear();
                    for (size_t c : covered) ranked.emplace_back(opening(c) + branch(pin, c), c);
                    ++measured_pins_;
                } else ++unmeasured_pins_;
            }
        } else if (delay_plan_) ++unmeasured_pins_;
        if (trace_estimates_) for (const auto& candidate : ranked) trace_estimate("post", pin, candidate.second);
        profile.enter(Phase::SELECT);
        std::sort(ranked.begin(), ranked.end());
        auto selected = diversify_(ranked, candidate_count);
        for (RRNodeId node : previous_channels) {
            int c = channel_index_[node];
            if (c >= 0 && feasible_(source, c, terminals[pin])) selected.push_back(c);
        }
        if (prior_guides && size_t(pin) < prior_guides->size())
            for (RRNodeId node : (*prior_guides)[pin].preferred) {
                int c = channel_index_[node];
                if (c >= 0 && feasible_(source, c, terminals[pin])) selected.push_back(c);
            }
        std::sort(selected.begin(), selected.end());
        selected.erase(std::unique(selected.begin(), selected.end()), selected.end());
        if (selected.empty()) ++result.no_candidate;
        for (size_t c : selected) {
            result.guides[pin].preferred.push_back(channels_[c]);
            pool.insert(c);
        }
        result.guides[pin].miss_weight = miss_weight;
    }
    profile.enter(Phase::TABLE);
    if (targeted_delay_)
        for (const auto& [pin, distances] : reverse)
            sink_scales[pin] = calibrate(terminals[pin], *distances);
    // Another pin may have extended the same endpoint cache. Final DP costs
    // must use scales fitted to that same final measurement state.
    // Keep pathological high-fanout work linear in the connection count.
    // This explicit fallback is counted and does not claim a tree optimum.
    if (use_tree && pins.size() > 128) {
        ++high_fanout_fallbacks_;
        use_tree = false;
    }
    if (prefix_trace && (!use_tree || pool.empty()))
        VTR_LOG("H3D_PREFIX_SKIP plan=%zu net=%zu reason=no_finite_tree_table pins=%zu pool=%zu tree=%d\n",
                prefix_trace, size_t(net), pins.size(), pool.size(), int(use_tree));
    if (use_tree && !pool.empty()) {
        std::vector<size_t> table(pool.begin(), pool.end());
        std::vector<double> openings;
        for (size_t c : table)
            openings.push_back(opening(c));
        std::vector<t_h3d_plan_leaf> leaves;
        for (int pin : pins) {
            if (result.guides[pin].preferred.empty()) continue;
            RRNodeId sink = terminals[pin];
            t_h3d_plan_leaf leaf{pin, graph_.node_xlow(sink), graph_.node_ylow(sink), {}};
            for (size_t i = 0; i < table.size(); ++i) {
                if (!feasible_(source, table[i], sink)) continue;
                trace_estimate("table", pin, table[i]);
                double cost = branch(pin, table[i]);
                // A delay-scored leaf may not have measured a candidate
                // contributed by another leaf. The finite DP model omits
                // that entry; this never removes an edge from detailed routing.
                if (std::isfinite(cost)) leaf.candidates.push_back({i, cost});
            }
            leaves.push_back(std::move(leaf));
        }
        if(trace_outside_ && delay_plan_ && delay_plan_->supported()) {
            const size_t event=++outside_plan_;
            struct TreeValue { bool expand;double delay; };
            std::unordered_map<RRNodeId,TreeValue> tree_nodes;
            std::vector<const RouteTreeNode*> tree_order;
            if(routing.route_trees[net])for(const auto& node:routing.route_trees[net]->all_nodes()) {
                tree_nodes[node.inode]={bool(node.re_expand),double(node.Tdel)};tree_order.push_back(&node);
            }
            std::map<int,std::vector<H3dDelayPlan::RetainedSuffix>> cached;
            size_t witnesses=0,edges=0;
            for(const auto& leaf:leaves) {
                auto paths=delay_plan_->retained_suffixes(terminals[leaf.pin]);
                witnesses+=paths.size();for(const auto& path:paths)edges+=path.reverse_edges.size();
                cached.emplace(leaf.pin,std::move(paths));
            }
            const auto& bb=routing.route_bb[net];
            const bool guard=tree_order.size()>32768 || tree_order.size()+edges>2000000-outside_trace_rows_;
            VTR_LOG("H3D_OUTSIDE_CONTEXT event=%zu net=%zu refresh=%d leaves=%zu tree_nodes=%zu witnesses=%zu edges=%zu guard=%d pres=%.17g opening=%.17g unit=%.17g xmin=%d xmax=%d ymin=%d ymax=%d layer_min=%d layer_max=%d\n",event,size_t(net),int(prior_guides!=nullptr),leaves.size(),tree_order.size(),witnesses,edges,int(guard),double(pres_fac),double(opening_weight),delay_plan_->delay_unit(),bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.layer_min,bb.layer_max);
            if(witnesses && !guard) {
                for(size_t seq=0;seq<tree_order.size();++seq) {
                    const auto& node=*tree_order[seq];const auto parent=node.parent();
                    VTR_LOG("H3D_OUTSIDE_TREE event=%zu seq=%zu node=%zu expand=%d delay=%.17g parent=%lld switch=%lld\n",event,seq,size_t(node.inode),int(node.re_expand),double(node.Tdel),parent?static_cast<long long>(size_t(parent->inode)):-1ll,parent?static_cast<long long>(size_t(node.parent_switch)):-1ll);
                }
                outside_trace_rows_+=tree_order.size()+edges;
            }
            for(const auto& leaf:leaves) {
                const RRNodeId sink=terminals[leaf.pin];double standalone=std::numeric_limits<double>::infinity();
                for(const auto& c:leaf.candidates)standalone=std::min(standalone,openings[c.channel]+c.branch_cost);
                VTR_LOG("H3D_OUTSIDE_LEAF event=%zu net=%zu pin=%d sink=%zu criticality=%.17g standalone=%.17g witnesses=%zu\n",event,size_t(net),leaf.pin,size_t(sink),double(criticality[leaf.pin]),standalone,cached.at(leaf.pin).size());
                if(guard)continue;
                size_t number=0;
                for(const auto& path:cached.at(leaf.pin)) {
                    const auto anchor=tree_nodes.find(path.anchor);const char* reason="valid";
                    if(anchor==tree_nodes.end())reason="anchor_absent";
                    else if(!anchor->second.expand)reason="anchor_inactive";
                    else if(graph_.node_layer_low(path.anchor)!=graph_.node_layer_low(sink))reason="wrong_layer";
                    double physical=0.,premium=0.;bool bb_ok=inside_bb(graph_,path.anchor,bb),simple=true,tree_hit=false;
                    std::set<size_t> visited;size_t previous=size_t(sink);
                    for(size_t i=0;i<path.reverse_edges.size();++i) {
                        const auto& e=path.reverse_edges[i];const auto node=RRNodeId(e.from);const auto next=RRNodeId(e.to);
                        simple=simple && e.from==previous && visited.insert(e.from).second;previous=e.to;
                        bb_ok=bb_ok && inside_bb(graph_,node,bb) && inside_bb(graph_,next,bb);
                        tree_hit=tree_hit || tree_nodes.contains(node);
                        const auto& info=routing.rr_node_route_inf[node];const int occ=info.occ(),capacity=graph_.node_capacity(node);
                        const bool ordinary=(graph_.node_type(node)==e_rr_type::CHANX || graph_.node_type(node)==e_rr_type::CHANY) && graph_.node_direction(node)!=Direction::NONE;
                        const double price=double(info.acc_cost)*(1.+double(pres_fac)*std::max(0,occ+1-capacity));
                        const double toll=ordinary ? std::max(0.,price-1.)/std::max(1.,price) : 0.;
                        physical+=e.physical_seconds;premium+=toll;
                        VTR_LOG("H3D_OUTSIDE_EDGE event=%zu pin=%d witness=%zu index=%zu from=%zu to=%zu delay=%.17g occ=%d capacity=%d acc=%.17g ordinary=%d price=%.17g premium=%.17g\n",event,leaf.pin,number,i,e.from,e.to,e.physical_seconds,occ,capacity,double(info.acc_cost),int(ordinary),price,toll);
                    }
                    simple=simple && previous==size_t(path.anchor) && !visited.contains(size_t(path.anchor));
                    if(std::string(reason)=="valid") {
                        if(!simple)reason="not_simple";
                        else if(!bb_ok)reason="outside_bb";
                        else if(tree_hit)reason="tree_intersection";
                    }
                    const double prefix=anchor==tree_nodes.end()?0.:anchor->second.delay;
                    const double raw=(1.+4.*double(criticality[leaf.pin]))*(prefix+physical)/delay_plan_->delay_unit()+double(opening_weight)*premium;
                    VTR_LOG("H3D_OUTSIDE_WITNESS event=%zu net=%zu pin=%d witness=%zu anchor=%zu origin=%zu edges=%zu reason=%s prefix=%.17g physical=%.17g premium=%.17g raw=%.17g\n",event,size_t(net),leaf.pin,number++,size_t(path.anchor),path.origin,path.reverse_edges.size(),reason,prefix,physical,premium,raw);
                }
            }
        }
        // Diagnostic-only exact-cost fingerprint, before either solver.
        static const bool trace_table = std::getenv("VPR_H3D_TRACE_TABLE") != nullptr;
        auto fingerprint_table=[&]() {
            uint64_t fingerprint = 14695981039346656037ull;
            auto mix = [&](uint64_t word) {
                for (int i = 0; i < 8; ++i) {
                    fingerprint ^= word & 255;
                    fingerprint *= 1099511628211ull;
                    word >>= 8;
                }
            };
            mix(table.size());
            for (size_t i = 0; i < table.size(); ++i) {
                mix(size_t(channels_[table[i]]));
                mix(std::bit_cast<uint64_t>(openings[i]));
            }
            mix(leaves.size());
            for (const auto& leaf : leaves) {
                mix(leaf.pin); mix(leaf.x); mix(leaf.y); mix(leaf.candidates.size());
                for (const auto& c : leaf.candidates) {
                    mix(c.channel); mix(std::bit_cast<uint64_t>(c.branch_cost));
                }
            }
            return fingerprint;
        };
        if (trace_table) {
            VTR_LOG("H3D_TABLE net=%zu fingerprint=%016llx candidates=%zu leaves=%zu\n",
                    size_t(net),static_cast<unsigned long long>(fingerprint_table()),table.size(),leaves.size());
        }
        profile.enter(Phase::SOLVE);
        const bool independent = independent_ || (prior_guides && refresh_independent_);
        auto planned = independent ? h3d_plan_independent(leaves, openings) : h3d_plan_partition(leaves, openings);
        if (candidate_path_mode_ && prior_guides && refresh_targets && prefix_trace
            && delay_plan_ && delay_plan_->supported() && std::isfinite(planned.cost)) {
            size_t before=candidate_path_score_plans_;
            bool changed=probe_candidates_(net,prefix_trace,terminals,criticality,*refresh_targets,pres_fac,table,openings,leaves,planned,reverse,timed);
            if(changed) {
                auto start=std::chrono::steady_clock::now();
                planned=independent ? h3d_plan_independent(leaves,openings) : h3d_plan_partition(leaves,openings);
                ++candidate_path_resolves_;candidate_path_resolve_seconds_+=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            }
            if(candidate_path_score_plans_>before) {
                for(const auto& leaf:leaves)
                    VTR_LOG("H3D_PATH_PRICE_LAYOUT plan=%zu net=%zu pin=%d x=%d y=%d sink=%zu\n",prefix_trace,size_t(net),leaf.pin,leaf.x,leaf.y,size_t(terminals[leaf.pin]));
                VTR_LOG("H3D_PATH_PRICE_TABLE plan=%zu net=%zu fingerprint=%016llx candidates=%zu leaves=%zu\n",
                        prefix_trace,size_t(net),static_cast<unsigned long long>(fingerprint_table()),table.size(),leaves.size());
            }
        }
        if (prior_guides) {
            refresh_independent_calls_ += independent;
            refresh_shared_calls_ += !independent;
        }
        if (prefix_trace) {
            // Decision-neutral: tree references live only during this plan.
            // No distance/closure construction or mutable routing state access.
            const double missing = std::numeric_limits<double>::quiet_NaN();
            const double unit = delay_plan_ && delay_plan_->supported() ? delay_plan_->delay_unit() : 0.;
            const bool path_trace = delay_plan_ && delay_plan_->trace_paths();
            std::set<RRNodeId> path_owned;
            if (path_trace && routing.route_trees[net])
                for (const auto& node : routing.route_trees[net]->all_nodes()) path_owned.insert(node.inode);
            auto observe_path = [&](int pin, RRNodeId entry, bool reverse_side, bool prior, bool proposed) {
                if (!path_trace) return;
                RRNodeId endpoint = reverse_side ? terminals[pin] : source;
                auto witness = delay_plan_->path_witness(endpoint, reverse_side, entry);
                if (witness.nodes.empty()) {
                    if (std::strcmp(witness.status, "cache_limit") == 0) ++path_cache_limit_[reverse_side];
                    else ++path_unmeasured_[reverse_side];
                    return;
                }
                ++path_measured_[reverse_side];
                if (path_trace_rows_ >= 50000) { ++path_trace_omitted_; return; }
                ++path_trace_rows_;
                size_t ordinary = 0, overused = 0, projected = 0;
                double premium = 0., maximum = 1.;
                bool finite_price = true;
                std::ostringstream path;
                path << std::setprecision(17);
                for (size_t i = 0; i < witness.nodes.size(); ++i) {
                    RRNodeId node = witness.nodes[i];
                    const auto& info = routing.rr_node_route_inf[node];
                    const bool owned_node = path_owned.contains(node);
                    int demand = info.occ() + (owned_node ? 0 : 1);
                    auto type = graph_.node_type(node);
                    bool crossing_adjacent = (i && h3d_crosses_layers(graph_, witness.nodes[i-1], node))
                                             || (i+1 < witness.nodes.size() && h3d_crosses_layers(graph_, node, witness.nodes[i+1]));
                    bool planar = (type == e_rr_type::CHANX || type == e_rr_type::CHANY)
                                  && node != entry && !crossing_adjacent;
                    if (planar) {
                        ++ordinary;
                        overused += info.occ() > graph_.node_capacity(node);
                        projected += demand > graph_.node_capacity(node);
                        // Ownership-aware negotiated multiplier only: exclude
                        // native base costs and configurability assumptions.
                        double price = double(info.acc_cost) * (1. + double(pres_fac) * std::max(0, demand - graph_.node_capacity(node)));
                        finite_price &= std::isfinite(price);
                        if (std::isfinite(price)) {
                            premium += std::max(0., price - 1.);
                            maximum = std::max(maximum, price);
                        }
                    }
                    if (i) path << ';';
                    path << size_t(node) << ',' << (i < witness.edge_delays.size() ? witness.edge_delays[i] : 0.)
                         << ',' << info.occ() << ',' << graph_.node_capacity(node) << ',' << double(info.acc_cost)
                         << ',' << int(owned_node) << ',' << int(planar);
                }
                VTR_LOG("H3D_PATH_WITNESS plan=%zu net=%zu pin=%d entry=%zu reverse=%d endpoint=%zu prior=%d proposed=%d status=%s delay_seconds=%.17g pres_fac=%.17g ordinary=%zu overused=%zu projected_overused=%zu premium_sum=%.17g max_price=%.17g finite_price=%d path=%s\n",
                        prefix_trace, size_t(net), pin, size_t(entry), int(reverse_side), size_t(endpoint), int(prior), int(proposed), witness.status,
                        witness.nodes.empty() ? missing : witness.delay_seconds, double(pres_fac), ordinary, overused, projected, premium, maximum, int(finite_price),
                        witness.nodes.empty() ? "-" : path.str().c_str());
            };
            std::unordered_map<RRNodeId, const RouteTreeNode*> retained_entries;
            if (routing.route_trees[net]) {
                for (const auto& node : routing.route_trees[net]->all_nodes())
                    if (channel_index_[node.inode] >= 0) retained_entries.emplace(node.inode, &node);
            }
            std::unordered_map<RRNodeId, std::vector<const RouteTreeNode*>> retained_exits;
            VTR_LOG("H3D_PREFIX_TABLE plan=%zu net=%zu leaves=%zu candidates=%zu unit_seconds=%.17g\n",
                    prefix_trace, size_t(net), leaves.size(), table.size(), unit);
            for (size_t c = 0; c < table.size(); ++c) {
                RRNodeId entry = channels_[table[c]];
                auto found = retained_entries.find(entry);
                const RouteTreeNode* node = found == retained_entries.end() ? nullptr : found->second;
                VTR_ASSERT(owned.contains(entry) == (node != nullptr));
                auto& exits = retained_exits[entry];
                if (node) {
                    for (const auto& child : node->child_nodes()) {
                        if (!h3d_crosses_layers(graph_, entry, child.inode)) continue;
                        exits.push_back(&child);
                        VTR_LOG("H3D_PREFIX_EXIT plan=%zu net=%zu entry=%zu exit=%zu component=%d parent_switch=%zu tdel_seconds=%.17g r_upstream=%.17g c_downstream=%.17g re_expand=%d\n",
                                prefix_trace, size_t(net), size_t(entry), size_t(child.inode),
                                reachability_->component(size_t(child.inode)), size_t(child.parent_switch),
                                double(child.Tdel), double(child.R_upstream), double(child.C_downstream), int(child.re_expand));
                    }
                }
                const auto& info = routing.rr_node_route_inf[entry];
                VTR_LOG("H3D_PREFIX_ENTRY plan=%zu net=%zu entry=%zu owned=%d retained_exits=%zu source_known=%d source_units=%.17g opening_units=%.17g occupancy=%d capacity=%d acc_cost=%.17g pres_fac=%.17g tdel_seconds=%.17g r_upstream=%.17g c_downstream=%.17g re_expand=%d retained_source=%d legacy_source_units=%.17g geometry_source_units=%.17g\n",
                        prefix_trace, size_t(net), size_t(entry), int(node != nullptr), exits.size(),
                        int(forward && forward->contains(entry)), source_cost(table[c]), openings[c],
                        info.occ(), graph_.node_capacity(entry), double(info.acc_cost), double(pres_fac),
                        node ? double(node->Tdel) : missing, node ? double(node->R_upstream) : missing,
                        node ? double(node->C_downstream) : missing, node ? int(node->re_expand) : 0,
                        int(retained_source_units.contains(entry)), legacy_source_cost(table[c]), proxy_(source, table[c]));
            }
            std::unordered_map<int, size_t> proposed;
            for (const auto& [pin, c] : planned.assignment) proposed.emplace(pin, c);
            for (const auto& leaf : leaves) {
                auto sink_view = sink_views_.find(terminals[leaf.pin]);
                for (const auto& candidate : leaf.candidates) {
                    RRNodeId entry = channels_[table[candidate.channel]];
                    size_t reachable_exits = 0, expandable_exits = 0;
                    double best_exit_tdel = std::numeric_limits<double>::infinity();
                    for (const auto* exit : retained_exits.at(entry)) {
                        const int component = reachability_->component(size_t(exit->inode));
                        const bool reaches = sink_view != sink_views_.end() && component >= 0
                                             && sink_view->second.intersects({component});
                        if (reaches) {
                            ++reachable_exits;
                            expandable_exits += exit->re_expand;
                            best_exit_tdel = std::min(best_exit_tdel, double(exit->Tdel));
                        }
                        VTR_LOG("H3D_PREFIX_REACH plan=%zu net=%zu pin=%d entry=%zu exit=%zu sink_view=%d reaches=%d\n",
                                prefix_trace, size_t(net), leaf.pin, size_t(entry), size_t(exit->inode),
                                int(sink_view != sink_views_.end()), int(reaches));
                    }
                    const auto& prior = prior_guides->at(leaf.pin).preferred;
                    const bool was_preferred = std::find(prior.begin(), prior.end(), entry) != prior.end();
                    auto choice = proposed.find(leaf.pin);
                    VTR_LOG("H3D_PREFIX_PAIR plan=%zu net=%zu pin=%d entry=%zu sink_view=%d reachable_exits=%zu expandable_exits=%zu best_exit_tdel_seconds=%.17g branch_units=%.17g prior=%d proposed=%d\n",
                            prefix_trace, size_t(net), leaf.pin, size_t(entry), int(sink_view != sink_views_.end()),
                            reachable_exits, expandable_exits, reachable_exits ? best_exit_tdel : missing,
                            candidate.branch_cost, int(was_preferred), int(choice != proposed.end() && choice->second == candidate.channel));
                    bool is_proposed = choice != proposed.end() && choice->second == candidate.channel;
                    observe_path(leaf.pin, entry, false, was_preferred, is_proposed);
                    observe_path(leaf.pin, entry, true, was_preferred, is_proposed);
                }
            }
        }
        profile.enter(Phase::PRIOR);
        if (prior_guides) {
            std::vector<std::pair<int, size_t>> prior_assignment;
            for (const auto& leaf : leaves) {
                const auto& guide = prior_guides->at(leaf.pin);
                if (guide.preferred.size() != 1) continue;
                int old_channel = channel_index_[guide.preferred.front()];
                auto found = std::lower_bound(table.begin(), table.end(), size_t(old_channel));
                if (found != table.end() && *found == size_t(old_channel))
                    prior_assignment.emplace_back(leaf.pin, found - table.begin());
            }
            if (trace_prior) {
                result.prior_table_diagnosed = true;
                result.prior_leaves = leaves.size();
                result.prior_pairs = prior_assignment.size();
                for (const auto& leaf : leaves) {
                    const auto& guide = prior_guides->at(leaf.pin);
                    if (guide.preferred.empty()) { result.prior_empty_pins.push_back(leaf.pin); continue; }
                    if (guide.preferred.size() != 1) { ++result.prior_multiple; continue; }
                    auto assigned = std::find_if(prior_assignment.begin(), prior_assignment.end(),
                                                 [&](const auto& a) { return a.first == leaf.pin; });
                    if (assigned == prior_assignment.end()) { ++result.prior_outside_table; continue; }
                    auto candidate = std::find_if(leaf.candidates.begin(), leaf.candidates.end(),
                                                  [&](const auto& c) { return c.channel == assigned->second; });
                    if (candidate == leaf.candidates.end()) ++result.prior_branch_missing;
                    else if (!std::isfinite(candidate->branch_cost)) ++result.prior_branch_nonfinite;
                    if (!std::isfinite(openings.at(assigned->second))) ++result.prior_opening_nonfinite;
                }
            }
            result.previous_cost = 0.;
            if (independent) {
                for (const auto& leaf : leaves)
                    result.previous_cost += h3d_assignment_cost({leaf}, openings, prior_assignment);
            } else result.previous_cost = h3d_assignment_cost(leaves, openings, prior_assignment);
            result.proposed_cost = planned.cost;
            result.refresh_accepted = h3d_accept_refresh(result.previous_cost, result.proposed_cost, refresh_margin);
            VTR_LOG("H3D_REFRESH_SOLVER net=%zu independent=%d leaves=%zu candidates=%zu old_cost=%.17g new_cost=%.17g groups=%zu accepted=%d\n",
                    size_t(net), independent, leaves.size(), table.size(), result.previous_cost, result.proposed_cost,
                    planned.groups, result.refresh_accepted);
            if (prefix_trace)
                VTR_LOG("H3D_PREFIX_DECISION plan=%zu net=%zu accepted=%d old_cost=%.17g new_cost=%.17g\n",
                        prefix_trace, size_t(net), int(result.refresh_accepted), result.previous_cost, result.proposed_cost);
            if (!result.refresh_accepted) {
                result.guides = *prior_guides;
                return result;
            }
        }
        profile.enter(Phase::OUTPUT);
        if (std::isfinite(planned.cost)) {
            result.groups = planned.groups;
            for (const auto& [pin, c] : planned.assignment)
                result.guides[pin].preferred = {channels_[table[c]]};
            if (trace_dp_sensitivity_ || dp_tie_pressure_ || dp_margin_pressure_) {
                auto sensitivity_start = std::chrono::steady_clock::now();
                auto sensitivity = h3d_partition_exclusion_costs(leaves, openings, planned.assignment);
                double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - sensitivity_start).count();
                VTR_ASSERT(std::abs(sensitivity.base_cost - planned.cost) <= 1e-10 * std::max(1., planned.cost));
                std::unordered_map<int, const t_h3d_plan_leaf*> sensitivity_leaves;
                if (dp_margin_pressure_)
                    for (const auto& leaf : leaves) sensitivity_leaves.emplace(leaf.pin, &leaf);
                for (size_t i = 0; i < planned.assignment.size(); ++i) {
                    const auto& [pin, candidate] = planned.assignment[i];
                    double alternative = sensitivity.exclusion_costs.at(i);
                    VTR_ASSERT(alternative + 1e-10 * std::max(1., planned.cost) >= planned.cost);
                    if (trace_dp_sensitivity_) VTR_LOG("H3D_DP_MARGIN net=%zu pin=%d refresh=%d candidate=%zu base=%.17g exclusion=%.17g delta=%.17g\n",
                            size_t(net), pin, prior_guides != nullptr, size_t(channels_[table[candidate]]),
                            sensitivity.base_cost, alternative, alternative - sensitivity.base_cost);
                    if (dp_tie_pressure_) {
                        result.guides.at(pin).miss_weight = h3d_exact_tie_pressure(miss_weight, sensitivity.base_cost, alternative);
                        VTR_LOG("H3D_DP_PRESSURE net=%zu pin=%d refresh=%d candidate=%zu base=%.17g exclusion=%.17g original=%.9g applied=%.9g\n",
                                size_t(net), pin, prior_guides != nullptr, size_t(channels_[table[candidate]]),
                                sensitivity.base_cost, alternative, double(miss_weight), double(result.guides.at(pin).miss_weight));
                    }
                    if (dp_margin_pressure_) {
                        const auto& costs = sensitivity_leaves.at(pin)->candidates;
                        auto selected = std::lower_bound(costs.begin(), costs.end(), candidate,
                            [](const auto& c, size_t index) { return c.channel < index; });
                        VTR_ASSERT(selected != costs.end() && selected->channel == candidate);
                        double leaf_cost = openings.at(candidate) + selected->branch_cost;
                        result.guides.at(pin).miss_weight = h3d_relative_margin_pressure(miss_weight, sensitivity.base_cost, alternative, leaf_cost);
                        VTR_LOG("H3D_DP_RELATIVE_PRESSURE net=%zu pin=%d refresh=%d candidate=%zu base=%.17g exclusion=%.17g leaf_cost=%.17g original=%.9g applied=%.9g\n",
                                size_t(net), pin, prior_guides != nullptr, size_t(channels_[table[candidate]]),
                                sensitivity.base_cost, alternative, leaf_cost, double(miss_weight), double(result.guides.at(pin).miss_weight));
                    }
                }
                VTR_LOG("H3D_DP_SENSITIVITY_TIME net=%zu refresh=%d leaves=%zu requests=%zu seconds=%.9g\n",
                        size_t(net), prior_guides != nullptr, leaves.size(), planned.assignment.size(), seconds);
            }
            if (trace_guide_margin_) {
                // Read the already constructed table, without queries or re-solving.
                // A shared assignment can be worse for one leaf in isolation.
                // Count co-assigned leaves, not DP groups or physical sharing.
                std::vector<size_t> users(table.size(), 0);
                std::unordered_map<int, size_t> assignments;
                for (const auto& [pin, c] : planned.assignment) {
                    ++users.at(c);
                    assignments.emplace(pin, c);
                }
                for (const auto& leaf : leaves) {
                    auto selected = assignments.find(leaf.pin);
                    VTR_ASSERT(selected != assignments.end());
                    size_t chosen = selected->second;
                    double chosen_branch = std::numeric_limits<double>::infinity();
                    double alternative = std::numeric_limits<double>::infinity();
                    size_t alternatives = 0;
                    for (const auto& candidate : leaf.candidates) {
                        double total = openings.at(candidate.channel) + candidate.branch_cost;
                        if (candidate.channel == chosen) chosen_branch = candidate.branch_cost;
                        else if (std::isfinite(total)) {
                            alternative = std::min(alternative, total);
                            ++alternatives;
                        }
                    }
                    double chosen_total = openings.at(chosen) + chosen_branch;
                    VTR_ASSERT(std::isfinite(chosen_total));
                    RRNodeId node = channels_[table[chosen]];
                    auto backward = reverse.find(leaf.pin);
                    bool source_measured = forward && forward->contains(node);
                    bool sink_measured = backward != reverse.end() && backward->second->contains(node);
                    VTR_LOG("H3D_GUIDE_MARGIN net=%zu pin=%d refresh=%d independent=%d candidate=%zu users=%zu alternatives=%zu opening=%.17g branch=%.17g chosen=%.17g alternative=%.17g criticality=%.9g source_measured=%d sink_measured=%d\n",
                            size_t(net), leaf.pin, prior_guides != nullptr, independent,
                            size_t(node), users.at(chosen), alternatives, openings.at(chosen),
                            chosen_branch, chosen_total, alternative, double(criticality.at(leaf.pin)),
                            source_measured, sink_measured);
                }
            }
        }
    }
    if (prior_guides && !result.refresh_accepted) {
        result.guides = *prior_guides;
        return result;
    }
    profile.enter(Phase::OUTPUT);
    for (int pin : pins) {
        auto& guide = result.guides[pin];
        if (equivalent_guide_cap_ > 1 && forward && guide.preferred.size() == 1) {
            VTR_ASSERT(prior_guides == nullptr);
            RRNodeId chosen = guide.preferred.front();
            auto back = reverse.find(pin);
            if (back != reverse.end() && forward->contains(chosen) && back->second->contains(chosen)) {
                size_t selected = channel_index_[chosen];
                double unit = delay_plan_->delay_unit();
                double chosen_delay = (double(forward->at(chosen)) + double(back->second->at(chosen))) / unit;
                double chosen_charge = opening(selected) - source_cost(selected);
                std::vector<std::pair<double, size_t>> alternatives;
                for (size_t c : pool) {
                    RRNodeId node = channels_[c];
                    if (node == chosen || !forward->contains(node) || !back->second->contains(node)) continue;
                    double delay = (double(forward->at(node)) + double(back->second->at(node))) / unit;
                    double charge = opening(c) - source_cost(c);
                    if (h3d_equivalent_guide(chosen_delay, delay, chosen_charge, charge))
                        alternatives.emplace_back(opening(c) + branch(pin, c), c);
                }
                std::sort(alternatives.begin(), alternatives.end());
                for (size_t c : diversify_(alternatives, equivalent_guide_cap_ - 1)) {
                    RRNodeId node = channels_[c];
                    guide.preferred.push_back(node);
                    double delay = (double(forward->at(node)) + double(back->second->at(node))) / unit;
                    VTR_LOG("H3D_EQUIVALENT_GUIDE net=%zu pin=%d chosen=%zu alternative=%zu chosen_delay_units=%.17g alternative_delay_units=%.17g chosen_charge=%.17g alternative_charge=%.17g\n",
                            size_t(net), pin, size_t(chosen), size_t(node), chosen_delay, delay, chosen_charge, opening(c) - source_cost(c));
                }
                equivalent_guide_pins_ += guide.preferred.size() > 1;
                equivalent_guide_added_ += guide.preferred.size() - 1;
                VTR_ASSERT(guide.preferred.size() <= equivalent_guide_cap_);
            }
        }
        std::sort(guide.preferred.begin(), guide.preferred.end());
        if(bounded_critical_guide_ && !guide.preferred.empty()) {
            VTR_ASSERT(delay_plan_ && forward);
            size_t from=0,to=0;std::ostringstream known;
            auto back=reverse.find(pin);
            for(auto node:guide.preferred) {
                bool a=forward->contains(node),b=back!=reverse.end() && back->second->contains(node);
                from+=a;to+=b;if(known.tellp()>0)known<<';';known<<size_t(node)<<','<<int(a)<<','<<int(b);
            }
            guide.bounded_critical=true;guide.bounded_beta=bounded_critical_beta_;
            guide.bounded_cap_only=bounded_cap_only_;
            guide.bounded_reliability=.5*double(from+to)/guide.preferred.size();
            guide.bounded_unit_seconds=delay_plan_->delay_unit();
            guide.bounded_penalty_seconds=float(bounded_critical_beta_*guide.bounded_reliability*guide.bounded_unit_seconds);
            VTR_LOG("H3D_BOUNDED_CRITICAL_GUIDE net=%zu pin=%d source=%zu sink=%zu reverse_present=%d source_known=%zu sink_known=%zu preferred_count=%zu reliability=%.17g unit_seconds=%.17g beta=%.17g penalty_seconds=%.17g known=%s\n",
                size_t(net),pin,size_t(source),size_t(terminals[pin]),int(back!=reverse.end()),from,to,guide.preferred.size(),guide.bounded_reliability,guide.bounded_unit_seconds,guide.bounded_beta,double(guide.bounded_penalty_seconds),known.str().c_str());
            if(guide.bounded_cap_only)
                VTR_LOG("H3D_BOUNDED_CAP_GUIDE net=%zu pin=%d configured=1\n",size_t(net),pin);
        }
        if (mixed && !guide.preferred.empty()) {
            ++selected_delay_pins_;
            bool informed = false;
            auto back = reverse.find(pin);
            for (RRNodeId node : guide.preferred) {
                trace_estimate("selected", pin, channel_index_[node]);
                bool from = forward->contains(node);
                source_floor_selected_ += source_geometry_floor_ && !from && source_scale < 1.;
                bool to = back != reverse.end() && back->second->contains(node);
                selected_both_ += from && to;
                selected_source_ += from && !to;
                selected_sink_ += !from && to;
                selected_estimated_ += !from && !to;
                informed |= from || to;
                if (delay_plan_->trace_bounds()) {
                    size_t c = channel_index_[node];
                    auto inspect = [&](bool measured, RRNodeId endpoint, bool backward, double estimate) {
                        if (measured) return;
                        ++bound_missing_sides_;
                        double bound = delay_plan_->lower_bound_seconds(endpoint, backward) / delay_plan_->delay_unit();
                        bound_positive_sides_ += bound > 0.;
                        if (estimate < bound) {
                            ++bound_below_sides_;
                            bound_gap_units_ += bound - estimate;
                            double effective = delay_plan_->adjust_estimate_units(endpoint, backward, estimate);
                            VTR_LOG("H3D_BOUND_SELECTED net=%zu pin=%d side=%s candidate=%zu estimate_units=%.17g lower_units=%.17g criticality=%.9g effective_units=%.17g clamp=%d\n",
                                    size_t(net), pin, backward ? "sink" : "source", size_t(node), estimate, bound, double(criticality[pin]), effective, delay_plan_->clamp_bounds());
                        }
                    };
                    inspect(from, source, false, (source_geometry_floor_ ? std::max(1., source_scale) : source_scale) * proxy_(source, c));
                    inspect(to, terminals[pin], true, proxy_(terminals[pin], c) * (back != reverse.end() ? sink_scales.at(pin) : 1.));
                }
            }
            selected_delay_informed_ += informed;
        }
        if (timing_regret_) guide.timing_regret = true;
        if (timing_regret_ && timing_guide_weight_ > 0. && forward && guide.preferred.size() == 1) {
            auto back = reverse.find(pin);
            RRNodeId chosen = guide.preferred.front();
            if (back != reverse.end() && forward->contains(chosen) && back->second->contains(chosen)) {
                double chosen_seconds = double(forward->at(chosen)) + double(back->second->at(chosen));
                // Reuse only existing exact distances in the finite table. No
                // additional query, changed assignment, or penalty for unknowns.
                for (size_t c : pool) {
                    RRNodeId node = channels_[c];
                    if (node == chosen || !forward->contains(node) || !back->second->contains(node)) continue;
                    double alternative = double(forward->at(node)) + double(back->second->at(node));
                    double penalty = h3d_timing_regret_seconds(chosen_seconds, alternative, delay_plan_->delay_unit(), timing_guide_weight_);
                    if (penalty <= 0.) continue;
                    guide.timing_alternatives.emplace_back(node, float(penalty));
                    VTR_LOG("H3D_TIMING_REGRET net=%zu pin=%d chosen=%zu alternative=%zu chosen_seconds=%.17g alternative_seconds=%.17g unit=%.17g weight=%.17g penalty=%.17g\n",
                            size_t(net), pin, size_t(chosen), size_t(node), chosen_seconds, alternative, delay_plan_->delay_unit(), timing_guide_weight_, penalty);
                }
                std::sort(guide.timing_alternatives.begin(), guide.timing_alternatives.end());
                timing_regret_guides_ += !guide.timing_alternatives.empty();
                timing_regret_pairs_ += guide.timing_alternatives.size();
            }
        } else if (!timing_regret_ && timing_guide_weight_ > 0. && forward && !guide.preferred.empty()) {
            // Confidence is measured-side coverage of the selected preference,
            // not whole-query coverage. No measurements => no timing penalty.
            double reliability = 0.;
            for (RRNodeId node : guide.preferred) {
                reliability += .5 * forward->contains(node);
                auto back = reverse.find(pin);
                if (back != reverse.end()) reliability += .5 * back->second->contains(node);
            }
            reliability /= guide.preferred.size();
            // At most one graph delay unit per mismatching crossing. This is
            // a search preference only, never part of physical Tdel or STA.
            guide.timing_miss_penalty = timing_guide_weight_ * reliability * delay_plan_->delay_unit();
            timing_guides_ += guide.timing_miss_penalty > 0.f;
        }
    }
    return result;
}

bool H3dFastPlan::probe_candidates_(ParentNetId net,size_t plan_id,const std::vector<RRNodeId>& terminals,
        const std::vector<float>& criticality,const std::vector<size_t>& targets,float pres_fac,
        const std::vector<size_t>& table,const std::vector<double>& openings,
        std::vector<t_h3d_plan_leaf>& leaves,const t_h3d_partition_plan& planned,
        const std::unordered_map<int,const H3dDelayPlan::Distances*>& reverse,const std::set<int>& timed) {
    const auto started=std::chrono::steady_clock::now();
    struct Request {int pin;size_t candidate,alternatives;double priority,gap;bool proposed;};
    struct LeafRequests {int pin;double priority;std::vector<Request> requests;};
    std::vector<LeafRequests> pending;
    for (const auto& leaf:leaves) {
        auto assignment=std::find_if(planned.assignment.begin(),planned.assignment.end(),[&](const auto& x){return x.first==leaf.pin;});
        if (assignment==planned.assignment.end()) continue;
        VTR_ASSERT(std::find(targets.begin(),targets.end(),size_t(leaf.pin))!=targets.end());
        size_t chosen=assignment->second;double chosen_cost=0.;
        std::vector<std::pair<double,size_t>> ranked,unknown;
        for (const auto& candidate:leaf.candidates) {
            double cost=openings[candidate.channel]+candidate.branch_cost;
            if (!std::isfinite(cost)) continue;
            ranked.emplace_back(cost,candidate.channel);
            if (candidate.channel==chosen) chosen_cost=cost;
            auto back=reverse.find(leaf.pin);RRNodeId entry=channels_[table[candidate.channel]];
            if (back==reverse.end() || !back->second->contains(entry)) unknown.emplace_back(cost,candidate.channel);
        }
        if (unknown.empty()) continue;
        std::sort(ranked.begin(),ranked.end());std::sort(unknown.begin(),unknown.end());
        double alternative=chosen_cost;bool has_alternative=false;
        for (auto [cost,c]:ranked) if (c!=chosen) {alternative=cost;has_alternative=true;break;}
        double gap=alternative-chosen_cost;
        double uncertainty=has_alternative ? 1./(1.+std::abs(gap)/std::max(1.,std::abs(chosen_cost))) : 0.;
        double priority=double(criticality[leaf.pin])*(.25+.75*uncertainty);
        LeafRequests selected{leaf.pin,priority,{}};
        auto chosen_unknown=std::find_if(unknown.begin(),unknown.end(),[&](const auto& x){return x.second==chosen;});
        if (chosen_unknown!=unknown.end()) selected.requests.push_back({leaf.pin,chosen,ranked.size()-1,priority,gap,true});
        RRNodeId proposed=channels_[table[chosen]];size_t alternate=table.size();
        for (size_t i=0;i<std::min(size_t(4),unknown.size());++i) {
            size_t c=unknown[i].second;if(c==chosen)continue;
            if(alternate==table.size())alternate=c;
            RRNodeId entry=channels_[table[c]];
            if(graph_.node_xlow(entry)!=graph_.node_xlow(proposed) || graph_.node_ylow(entry)!=graph_.node_ylow(proposed)) {alternate=c;break;}
        }
        if(alternate<table.size())selected.requests.push_back({leaf.pin,alternate,ranked.size()-1,priority,gap,false});
        if(!selected.requests.empty())pending.push_back(std::move(selected));
    }
    std::sort(pending.begin(),pending.end(),[](const auto& a,const auto& b){return a.priority!=b.priority ? a.priority>b.priority : a.pin<b.pin;});
    std::vector<Request> requests;
    for(size_t i=0;i<std::min(size_t(2),pending.size());++i)
        requests.insert(requests.end(),pending[i].requests.begin(),pending[i].requests.end());
    if(requests.empty())return false;
    ++candidate_path_plans_;
    const auto& routing=g_vpr_ctx.routing();std::unordered_set<RRNodeId> owned;
    if(routing.route_trees[net])for(const auto& node:routing.route_trees[net]->all_nodes())owned.insert(node.inode);
    std::map<std::pair<RRNodeId,RRNodeId>,H3dCandidatePath::Result> memo;
    struct Observation {double physical,toll,geometry;bool exact;bool physical_exact=false;};
    std::map<std::pair<int,size_t>,Observation> observations;
    std::map<std::pair<RRNodeId,RRNodeId>,Observation> calibration;
    size_t remaining=256;double unit=delay_plan_->delay_unit();
    const double heuristic=candidate_path_mode_>=2 ? 4.*unit/std::max(1.,mean_span_) : 0.;
    const double weight=candidate_path_mode_==3 ? .25 : 0.;
    const char* names[]={"exact_proxy","path_upper","unreachable","work_limit","memory_limit"};
    for(size_t i=0;i<requests.size();++i) {
        const auto request=requests[i];RRNodeId entry=channels_[table[request.candidate]],sink=terminals[request.pin];
        size_t allowance=remaining ? std::max(size_t(1),remaining/(requests.size()-i)) : 0;
        auto key=std::make_pair(sink,entry);auto found=memo.find(key);bool hit=found!=memo.end(),attempted=hit || allowance>0;
        H3dCandidatePath::Result result{H3dCandidatePath::Stop::WORK_LIMIT,{},{},{},{},{}};
        size_t charged=0;
        if(hit) {result=found->second;++candidate_path_hits_;}
        else if(allowance) {
            result=delay_plan_->probe_reverse_candidate(sink,entry,allowance,heuristic,weight,pres_fac,owned);
            charged=result.expansions;VTR_ASSERT(charged<=remaining);remaining-=charged;
            memo.emplace(key,result);++candidate_path_calls_;candidate_path_work_+=charged;
        }
        ++candidate_path_records_;
        candidate_path_found_+=result.priced_upper_seconds.has_value();
        candidate_path_exact_+=result.stop==H3dCandidatePath::Stop::EXACT;
        candidate_path_memory_+=result.stop==H3dCandidatePath::Stop::MEMORY_LIMIT;
        if((candidate_path_score_weight_>0. || candidate_path_delay_weight_>0.) && result.priced_upper_seconds) {
            Observation observation{*result.physical_path_seconds/unit,*result.toll_path_seconds/unit,
                proxy_(sink,table[request.candidate]),result.stop==H3dCandidatePath::Stop::EXACT};
            observations[{request.pin,request.candidate}]=observation;
            bool sample=calibration.emplace(key,observation).second;
            VTR_LOG("H3D_PATH_PRICE_OBSERVATION plan=%zu net=%zu pin=%d entry=%zu physical_units=%.17g toll_units=%.17g geometry_units=%.17g exact_proxy=%d calibration_sample=%d\n",
                    plan_id,size_t(net),request.pin,size_t(entry),observation.physical,observation.toll,observation.geometry,int(observation.exact),int(sample));
        }
        std::vector<RRNodeId> nodes;std::vector<double> physical,tolls;
        if(result.priced_upper_seconds) {
            for(auto it=result.edges.rbegin();it!=result.edges.rend();++it) {
                size_t raw=it->to;nodes.push_back(raw==graph_.num_nodes() ? entry : RRNodeId(raw));
                physical.push_back(it->physical_seconds);tolls.push_back(it->toll_seconds);
            }
            nodes.push_back(sink);
        }
        std::ostringstream path;path<<std::setprecision(17);
        for(size_t j=0;j<nodes.size();++j) {
            RRNodeId node=nodes[j];const auto& info=routing.rr_node_route_inf[node];if(j)path<<';';
            path<<size_t(node)<<','<<(j<physical.size()?physical[j]:0.)<<','<<(j<tolls.size()?tolls[j]:0.)
                <<','<<info.occ()<<','<<graph_.node_capacity(node)<<','<<double(info.acc_cost)<<','<<int(owned.contains(node));
        }
        double missing=std::numeric_limits<double>::quiet_NaN();
        VTR_LOG("H3D_CANDIDATE_PATH plan=%zu net=%zu pin=%d entry=%zu mode=%d request=%zu requests=%zu proposed=%d native_target=1 criticality=%.17g local_gap=%.17g rank_alternatives=%zu priority=%.17g allowance=%zu charged=%zu remaining=%zu attempted=%d cache_hit=%d stop=%s search_expansions=%zu labels=%zu peak_heap=%zu unit_seconds=%.17g heuristic_per_grid_seconds=%.17g toll_weight=%.17g pres_fac=%.17g priced_upper_seconds=%.17g physical_path_seconds=%.17g toll_path_seconds=%.17g lower_priced_seconds=%.17g sink=%zu path=%s\n",
                plan_id,size_t(net),request.pin,size_t(entry),candidate_path_mode_,i+1,requests.size(),int(request.proposed),double(criticality[request.pin]),request.gap,request.alternatives,request.priority,
                allowance,charged,remaining,int(attempted),int(hit),names[int(result.stop)],result.expansions,result.labels,result.peak_heap,unit,heuristic,weight,double(pres_fac),
                result.priced_upper_seconds.value_or(missing),result.physical_path_seconds.value_or(missing),result.toll_path_seconds.value_or(missing),result.lower_seconds.value_or(missing),size_t(sink),
                nodes.empty()?"-":path.str().c_str());
    }
    std::set<int> selected_pins;for(const auto& request:requests)selected_pins.insert(request.pin);
    if(candidate_path_use_cached_) {
        VTR_ASSERT(delay_plan_->cache_paths());
        // Only read legacy-known witnesses on the same selected native-target
        // leaves. Distances/forests are static; prices and ownership are not.
        for(const auto& leaf:leaves) {
            if(!selected_pins.contains(leaf.pin))continue;
            auto back=reverse.find(leaf.pin);if(back==reverse.end())continue;
            RRNodeId sink=terminals[leaf.pin];
            for(const auto& candidate:leaf.candidates) {
                RRNodeId entry=channels_[table[candidate.channel]];
                if(!back->second->contains(entry))continue;
                auto witness=delay_plan_->path_witness(sink,true,entry);
                if(std::string(witness.status)!="measured")continue;
                double toll=0.;std::vector<double> tolls;
                for(size_t j=1;j<witness.nodes.size();++j) {
                    RRNodeId node=witness.nodes[j];double edge_toll=0.;
                    auto type=graph_.node_type(node);
                    if((type==e_rr_type::CHANX || type==e_rr_type::CHANY) && !owned.contains(node)) {
                        const auto& info=routing.rr_node_route_inf[node];
                        double price=double(info.acc_cost)*(1.+double(pres_fac)*std::max(0,int(info.occ())+1-int(graph_.node_capacity(node))));
                        double fraction=std::isfinite(price) ? std::max(0.,price-1.)/std::max(1.,price) : 1.;
                        edge_toll=weight*unit*fraction;
                    }
                    tolls.push_back(edge_toll);toll+=edge_toll;
                }
                Observation observation{witness.delay_seconds/unit,toll/unit,proxy_(sink,table[candidate.channel]),toll==0.,true};
                VTR_ASSERT(!observations.contains({leaf.pin,candidate.channel}));
                observations[{leaf.pin,candidate.channel}]=observation;
                bool sample=calibration.emplace(std::make_pair(sink,entry),observation).second;
                std::ostringstream path;path<<std::setprecision(17);
                for(size_t j=0;j<witness.nodes.size();++j) {
                    RRNodeId node=witness.nodes[j];const auto& info=routing.rr_node_route_inf[node];if(j)path<<';';
                    path<<size_t(node)<<','<<(j<witness.edge_delays.size()?witness.edge_delays[j]:0.)<<','<<(j<tolls.size()?tolls[j]:0.)
                        <<','<<info.occ()<<','<<graph_.node_capacity(node)<<','<<double(info.acc_cost)<<','<<int(owned.contains(node));
                }
                VTR_LOG("H3D_PATH_PRICE_CACHE_OBSERVATION plan=%zu net=%zu pin=%d entry=%zu sink=%zu physical_units=%.17g toll_units=%.17g geometry_units=%.17g exact_proxy=%d calibration_sample=%d unit_seconds=%.17g pres_fac=%.17g toll_weight=%.17g path=%s\n",
                        plan_id,size_t(net),leaf.pin,size_t(entry),size_t(sink),observation.physical,observation.toll,observation.geometry,int(observation.exact),int(sample),unit,double(pres_fac),weight,path.str().c_str());
            }
        }
    }
    candidate_path_seconds_+=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    if((candidate_path_score_weight_==0. && candidate_path_delay_weight_==0.) || calibration.empty())return false;
    const auto score_started=std::chrono::steady_clock::now();
    ++candidate_path_score_plans_;
    double scale=0.,rate=0.;bool all_exact=true;
    for(const auto& [key,observation]:calibration) {
        scale+=std::clamp(observation.physical/std::max(1.,observation.geometry),.25,4.);
        rate+=std::clamp(observation.toll/std::max(1.,observation.physical),0.,1.);
        all_exact&=observation.exact;
    }
    scale/=calibration.size();rate/=calibration.size();
    const double reliability=all_exact ? 1. : .25;
    bool changed=false;
    for(auto& leaf:leaves) {
        if(!selected_pins.contains(leaf.pin))continue;
        std::vector<double> physical_ratios;
        if(candidate_path_delay_weight_>0.)
            for(const auto& [key,observation]:observations)
                if(key.first==leaf.pin && observation.physical_exact)
                    physical_ratios.push_back(std::clamp(observation.physical/std::max(1.,observation.geometry),.25,4.));
        std::sort(physical_ratios.begin(),physical_ratios.end());
        const size_t count=physical_ratios.size();
        const double physical_scale=count ? (physical_ratios[(count-1)/2]+physical_ratios[count/2])*.5 : 1.;
        for(auto& candidate:leaf.candidates) {
            RRNodeId entry=channels_[table[candidate.channel]];auto found=observations.find({leaf.pin,candidate.channel});
            double geometry=proxy_(terminals[leaf.pin],table[candidate.channel]);
            double risk=found==observations.end() ? geometry*scale*rate : found->second.toll;
            double delta=candidate_path_score_weight_*reliability*double(criticality[leaf.pin])*std::min(2.,std::max(0.,risk));
            double base=candidate.branch_cost;candidate.branch_cost+=delta;
            changed|=candidate.branch_cost!=base;
            ++candidate_path_score_records_;candidate_path_score_observed_+=found!=observations.end();
            candidate_path_score_estimated_+=found==observations.end();candidate_path_score_changed_+=candidate.branch_cost!=base;
            VTR_LOG("H3D_PATH_PRICE_SCORE plan=%zu net=%zu pin=%d entry=%zu observed=%d samples=%zu scale=%.17g rate=%.17g reliability=%.17g criticality=%.17g geometry_units=%.17g risk_units=%.17g weight=%.17g cap_units=2 base_branch=%.17g delta_units=%.17g new_branch=%.17g\n",
                    plan_id,size_t(net),leaf.pin,size_t(entry),int(found!=observations.end()),calibration.size(),scale,rate,reliability,double(criticality[leaf.pin]),geometry,risk,candidate_path_score_weight_,base,delta,candidate.branch_cost);
            if(candidate_path_delay_weight_>0. && count) {
                const bool measured=found!=observations.end() && found->second.physical_exact;
                const double previous_sink=timed.contains(leaf.pin) ? reverse.at(leaf.pin)->at(entry)/unit : geometry;
                const double next_sink=measured ? found->second.physical : geometry*physical_scale;
                const double correction=candidate_path_delay_weight_*(1.+4.*double(criticality[leaf.pin]))*std::clamp(next_sink-previous_sink,-2.,2.);
                double before_delay=candidate.branch_cost;candidate.branch_cost+=correction;
                changed|=candidate.branch_cost!=before_delay;
                ++candidate_path_delay_records_;candidate_path_delay_changed_+=candidate.branch_cost!=before_delay;
                VTR_LOG("H3D_PATH_DELAY_SCORE plan=%zu net=%zu pin=%d entry=%zu physical_measured=%d legacy_timed=%d leaf_samples=%zu scale=%.17g geometry_units=%.17g previous_sink_units=%.17g next_sink_units=%.17g criticality=%.17g weight=%.17g sink_cap_units=2 price_branch=%.17g delta_units=%.17g new_branch=%.17g\n",
                        plan_id,size_t(net),leaf.pin,size_t(entry),int(measured),int(timed.contains(leaf.pin)),count,physical_scale,geometry,previous_sink,next_sink,double(criticality[leaf.pin]),candidate_path_delay_weight_,before_delay,correction,candidate.branch_cost);
            }
        }
    }
    candidate_path_score_seconds_+=std::chrono::duration<double>(std::chrono::steady_clock::now()-score_started).count();
    return changed;
}

void H3dFastPlan::log() const {
    if(source_coverage_skip_)
        VTR_LOG("H3D_SOURCE_COVERAGE_SKIP_SUMMARY checks=%zu skips=%zu rows=%zu omitted=%zu row_cap=20000\n",
                coverage_gate_checks_,coverage_gate_skips_,coverage_gate_rows_,coverage_gate_omitted_);
    if(source_empty_reverse_)
        VTR_LOG("H3D_SOURCE_EMPTY_REVERSE_SUMMARY requests=%zu new_queries=%zu settled=%zu cache_hits=%zu measured_entry_events=%zu rows=%zu omitted=%zu row_cap=20000\n",
                empty_reverse_requests_,empty_reverse_queries_,empty_reverse_work_,empty_reverse_hits_,empty_reverse_measured_,empty_reverse_rows_,empty_reverse_omitted_);
    if(candidate_path_delay_weight_>0.)
        VTR_LOG("H3D_PATH_DELAY_SUMMARY weight=%.17g records=%zu changed=%zu\n",
                candidate_path_delay_weight_,candidate_path_delay_records_,candidate_path_delay_changed_);
    if(candidate_path_score_weight_>0. || candidate_path_delay_weight_>0.)
        VTR_LOG("H3D_PATH_PRICE_SCORE_SUMMARY weight=%.17g plans=%zu records=%zu observed=%zu estimated=%zu changed=%zu extra_solves=%zu score_seconds=%.9g resolve_seconds=%.9g\n",
                candidate_path_score_weight_,candidate_path_score_plans_,candidate_path_score_records_,candidate_path_score_observed_,candidate_path_score_estimated_,candidate_path_score_changed_,candidate_path_resolves_,candidate_path_score_seconds_,candidate_path_resolve_seconds_);
    if(candidate_path_mode_)
        VTR_LOG("H3D_CANDIDATE_PATH_SUMMARY mode=%d plans=%zu records=%zu calls=%zu cache_hits=%zu charged_expansions=%zu paths=%zu exact_proxy=%zu memory_stops=%zu per_plan_work_cap=256 label_cap=16384 heap_cap=65536 seconds=%.9g\n",
                candidate_path_mode_,candidate_path_plans_,candidate_path_records_,candidate_path_calls_,candidate_path_hits_,candidate_path_work_,candidate_path_found_,candidate_path_exact_,candidate_path_memory_,candidate_path_seconds_);
    if (delay_plan_ && delay_plan_->trace_paths())
        VTR_LOG("H3D_PATH_TRACE records=%zu omitted=%zu limit=50000 forward_measured=%zu reverse_measured=%zu forward_unmeasured=%zu reverse_unmeasured=%zu forward_cache_limit=%zu reverse_cache_limit=%zu\n",
                path_trace_rows_, path_trace_omitted_, path_measured_[0], path_measured_[1], path_unmeasured_[0], path_unmeasured_[1], path_cache_limit_[0], path_cache_limit_[1]);
    VTR_LOG("H3D_REFRESH_SOLVER_SUMMARY independent=%d shared_calls=%zu independent_calls=%zu\n",
            refresh_independent_, refresh_shared_calls_, refresh_independent_calls_);
    VTR_LOG("H3D_EXIT_PRICE_SUMMARY weight=%g pairs=%zu positive=%zu cross_edges=%zu\n",
            exit_price_weight_, exit_price_pairs_, exit_price_positive_, exit_price_edges_);
    VTR_LOG("H3D_EQUIVALENT_GUIDES cap=%zu pins=%zu added=%zu\n",
            equivalent_guide_cap_, equivalent_guide_pins_, equivalent_guide_added_);
    VTR_LOG("H3D_TIMING_REGRET_SUMMARY enabled=%d guides=%zu pairs=%zu weight=%g\n",
            timing_regret_, timing_regret_guides_, timing_regret_pairs_, timing_guide_weight_);
    profile_.log();
    VTR_LOG("H3D_BOUND_SELECTED_SUMMARY missing_sides=%zu positive_bound_sides=%zu below_bound_sides=%zu sum_shortfall_units=%.17g\n",
            bound_missing_sides_, bound_positive_sides_, bound_below_sides_, bound_gap_units_);
    if (closure_view_) VTR_LOG("H3D_CLOSURE_VIEW endpoints=%zu local_entries=%zu shared_references=%zu\n",
                              source_views_.size() + sink_views_.size(), view_local_entries_, view_shared_references_);
    if (profile_.enabled) VTR_LOG("H3D_REACH_PROFILE misses=%zu seconds=%.9f scope=inclusive_not_additive\n", reach_misses_, reach_miss_seconds_);
    VTR_LOG("H3D_SELECTED_DELAY pins=%zu informed_pins=%zu both=%zu source_only=%zu sink_only=%zu estimated=%zu\n",
            selected_delay_pins_, selected_delay_informed_, selected_both_, selected_source_, selected_sink_, selected_estimated_);
    VTR_LOG("H3D_SCC queries=%zu endpoint_cache=%zu sampled_candidates=%zu high_fanout_fallbacks=%zu\n",
            queries_, source_cache_.size() + sink_cache_.size(), spatial_candidates_, high_fanout_fallbacks_);
    VTR_LOG("H3D_SCORE eligible=%zu skipped=%zu delay_scored=%zu unmeasured=%zu\n",
            eligible_pins_, skipped_pins_, measured_pins_, unmeasured_pins_);
    VTR_LOG("H3D_MIXED pins=%zu informed_pins=%zu both=%zu source_only=%zu sink_only=%zu estimated=%zu\n",
            mixed_pins_, mixed_informed_pins_, mixed_both_, mixed_source_only_, mixed_sink_only_, mixed_estimated_);
    VTR_LOG("H3D_TIMING_GUIDE nonzero_guides=%zu weight=%g\n", timing_guides_, timing_guide_weight_);
    VTR_LOG("H3D_QUERY_PRIORITY enabled=%d plans=%zu reordered=%zu\n",
            int(criticality_query_order_), query_order_nets_, query_order_changed_);
    VTR_LOG("H3D_REVERSE_RERANK enabled=%d pins=%zu changed=%zu\n",
            int(reverse_rerank_), reverse_rerank_pins_, reverse_rerank_changed_);
    VTR_LOG("H3D_ESTIMATE_SUMMARY enabled=%d rows=%zu\n", int(trace_estimates_), estimate_trace_rows_);
    VTR_LOG("H3D_SOURCE_ESTIMATE floor_geometry=%d selected_adjusted=%zu\n", int(source_geometry_floor_), source_floor_selected_);
    if (delay_plan_) delay_plan_->log();
}
