#include "h3d_routing.h"

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <chrono>
#include <memory>
#include <numeric>
#include <set>
#include <string>
#include <unordered_map>
#include <fstream>
#include <array>
#include <sstream>
#include <iomanip>

#include "globals.h"
#include "h3d_partition_dp.h"
#include "h3d_fast_plan.h"
#include "h3d_feedback_policy.h"
#include "h3d_crossing.h"
#include "route_common.h"
#include "route_tree.h"
#include "vpr_error.h"
#include "vtr_log.h"

namespace {

bool bounded_legal_phase=false; ///< Native legal milestone, reset on each width trial.

/** @brief Strictly parse a finite nonnegative experiment setting. */
float read_number(const char* name, float default_value) {
    const char* text = std::getenv(name);
    if (!text)
        return default_value;
    errno = 0;
    char* end = nullptr;
    float parsed = std::strtof(text, &end);
    if (errno || end == text || *end || !std::isfinite(parsed) || parsed < 0.f)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "%s must be finite and nonnegative, got '%s'", name, text);
    return parsed;
}

/** @brief Explicit experimental modes; the detailed connection search is always VPR's. */
enum class e_h3d_mode { OFF,
                        CANDIDATES,
                        STATIC,
                        DYNAMIC,
                        DYNAMIC_WHOLE,
                        DYNAMIC_SUBTREE };

/** @brief Immutable per-process settings, recorded at the first routing iteration. */
struct t_settings {
    bool trace_search_domain = false;
    bool trace_guide_influence = false; ///< Read-only actual crossing-cost trace.
    bool bounded_after_legal = false;
    bool use_scc = false;              ///< Exact SCC reachability with geometric costs instead of full BFS distances.
    e_h3d_mode mode = e_h3d_mode::OFF; ///< Candidate-planning ablation.
    size_t candidates = 8;             ///< Diverse preferred candidates per remote terminal.
    float miss_weight = 2.f;           ///< Additional relative CHANZ cost outside the preference set.
    bool dp_tie_pressure = false; ///< Enable final-pressure records for the shared-DP tie ablation.
    bool dp_margin_pressure = false; ///< Enable final-pressure records for the relative-margin ablation.
    float opening_weight = 8.f;        ///< Channel-opening weight in hop-cost planning units.
    bool delay_cost = false;
    size_t delay_budget = 4096;
    float min_criticality = 0.f;
    std::string feedback_action_name = "all"; ///< Exact label for action-ablation provenance.
    e_h3d_feedback_action feedback_action = e_h3d_feedback_action::ALL; ///< Development action ablation; full selective policy remains default.
    bool eligibility_trigger = false; ///< Refresh missing guides when a remote pin newly crosses the selection threshold.
    bool trace_prior = false; ///< Diagnose old-assignment coverage without changing refresh decisions.
    bool trace_planar = false; ///< Decision-neutral pre-prune planar overuse diagnostics on native-selected reroutes.
    bool trace_target_gate = false; ///< Compare whole-net and actual-target timing drift without changing refresh decisions.
    bool target_drift = false; ///< Only native remaining targets contribute timing drift to target-restricted refresh.
    bool target_feedback = false; ///< Limit refresh optimization and guide replacement to actual native remaining targets.
    bool trace_update_pins = false; ///< Observe accepted preference changes against the exact native remaining-target list.
    bool planar_feedback = false; ///< Also consider guided-path ordinary planar overuse after the normal cooldown.
    bool feedback = false;            ///< Selective refresh of guides on VPR-selected reroute nets.
    int cooldown = 3;                  ///< Minimum iterations between refresh attempts.
    double refresh_margin = .05;       ///< Required relative surrogate improvement.
    bool final_trace = false;          ///< Emit one final per-connection guide/path table.
    bool post_legal_release = false;   ///< Release guide use after native first legal convergence.
    bool post_legal_freeze = false;    ///< Independently freeze planning, retaining guide use.
    bool edge_encoding = false;       ///< Prefer actual crossing-edge sources in imported single-layer-node graphs.
};

/** @brief Parse modes exactly; misspellings must not silently run the baseline. */
const t_settings& settings() {
    static const t_settings value = [] {
        t_settings result;
        const char* env = std::getenv("VPR_H3D_MODE");
        std::string mode = env ? env : "off";
        if (mode == "off")
            result.mode = e_h3d_mode::OFF;
        else if (mode == "candidates")
            result.mode = e_h3d_mode::CANDIDATES;
        else if (mode == "static")
            result.mode = e_h3d_mode::STATIC;
        else if (mode == "dynamic")
            result.mode = e_h3d_mode::DYNAMIC;
        else if (mode == "dynamic_whole")
            result.mode = e_h3d_mode::DYNAMIC_WHOLE;
        else if (mode == "dynamic_subtree")
            result.mode = e_h3d_mode::DYNAMIC_SUBTREE;
        else
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unknown VPR_H3D_MODE '%s'", mode.c_str());
        float candidates = read_number("VPR_H3D_CANDIDATES", 8.f);
        if (candidates < 1.f || candidates > 64.f || std::floor(candidates) != candidates)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CANDIDATES must be an integer in [1,64]");
        result.candidates = static_cast<size_t>(candidates);
        result.miss_weight = read_number("VPR_H3D_MISS_WEIGHT", 2.f);
        const char* release = std::getenv("VPR_H3D_POST_LEGAL_RELEASE");
        if (release && std::string(release) != "0" && std::string(release) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_POST_LEGAL_RELEASE must be 0 or 1");
        result.post_legal_release = release && std::string(release) == "1";
        const char* freeze = std::getenv("VPR_H3D_POST_LEGAL_FREEZE");
        if (freeze && std::string(freeze) != "0" && std::string(freeze) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_POST_LEGAL_FREEZE must be 0 or 1");
        result.post_legal_freeze = freeze && std::string(freeze) == "1";
        if (result.post_legal_freeze && result.post_legal_release)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Post-legal freeze and release are independent experiments; do not combine");
        const char* tie_pressure = std::getenv("VPR_H3D_DP_TIE_PRESSURE");
        if (tie_pressure && std::string(tie_pressure) != "0" && std::string(tie_pressure) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DP_TIE_PRESSURE must be 0 or 1");
        result.dp_tie_pressure = tie_pressure && std::string(tie_pressure) == "1";
        const char* margin_pressure = std::getenv("VPR_H3D_DP_MARGIN_PRESSURE");
        if (margin_pressure && std::string(margin_pressure) != "0" && std::string(margin_pressure) != "1")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DP_MARGIN_PRESSURE must be 0 or 1");
        result.dp_margin_pressure = margin_pressure && std::string(margin_pressure) == "1";
        result.opening_weight = read_number("VPR_H3D_OPENING_WEIGHT", 8.f);
        const char* search = std::getenv("VPR_H3D_REACHABILITY");
        std::string reachability = search ? search : "bfs";
        if (reachability != "bfs" && reachability != "scc")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_REACHABILITY must be bfs or scc");
        result.use_scc = reachability == "scc";
        if ((result.dp_tie_pressure || result.dp_margin_pressure) && !result.use_scc)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "DP tie pressure requires the SCC finite-table planner");
        const char* encoding_env = std::getenv("VPR_H3D_GRAPH_ENCODING");
        std::string encoding = encoding_env ? encoding_env : "native";
        if (encoding != "native" && encoding != "edge")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_GRAPH_ENCODING must be native or edge");
        result.edge_encoding = encoding == "edge";
        if (result.edge_encoding && !result.use_scc)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Edge encoding requires SCC planning");
        const char* score = std::getenv("VPR_H3D_CANDIDATE_COST");
        std::string cost = score ? score : "geometry";
        if (cost != "geometry" && cost != "delay")
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CANDIDATE_COST must be geometry or delay");
        result.delay_cost = cost == "delay";
        float budget = read_number("VPR_H3D_DELAY_BUDGET", 4096.f);
        if (budget < 1.f || budget > 1000000.f || std::floor(budget) != budget)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_DELAY_BUDGET must be an integer in [1,1000000]");
        result.delay_budget = size_t(budget);
        result.min_criticality = read_number("VPR_H3D_MIN_CRITICALITY", 0.f);
        if (result.min_criticality > 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_MIN_CRITICALITY must be in [0,1]");
        if ((result.delay_cost || result.min_criticality > 0.f) && !result.use_scc)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Delay scoring and critical selection require SCC planning");
        float feedback = read_number("VPR_H3D_FEEDBACK", 0.f);
        if (feedback != 0.f && feedback != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_FEEDBACK must be 0 or 1");
        result.feedback = feedback == 1.f;
        float trace_target_gate = read_number("VPR_H3D_TRACE_TARGET_GATE", 0.f);
        if (trace_target_gate != 0.f && trace_target_gate != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_TARGET_GATE must be 0 or 1");
        result.trace_target_gate = trace_target_gate == 1.f;
        if (result.trace_target_gate && !result.feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Target-gate tracing requires selective feedback");
        float target_feedback = read_number("VPR_H3D_TARGET_FEEDBACK", 0.f);
        if (target_feedback != 0.f && target_feedback != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TARGET_FEEDBACK must be 0 or 1");
        result.target_feedback = target_feedback == 1.f;
        if (result.target_feedback && (!result.feedback || !result.use_scc))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Target feedback requires selective SCC feedback");
        float target_drift = read_number("VPR_H3D_TARGET_DRIFT", 0.f);
        if (target_drift != 0.f && target_drift != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TARGET_DRIFT must be 0 or 1");
        result.target_drift = target_drift == 1.f;
        if (result.target_drift && !result.target_feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Target drift requires target-restricted selective feedback");
        if (result.target_drift && result.trace_target_gate)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Original-trajectory target-gate trace must be used with target drift disabled");
        float trace_update_pins = read_number("VPR_H3D_TRACE_UPDATE_PINS", 0.f);
        if (trace_update_pins != 0.f && trace_update_pins != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_UPDATE_PINS must be 0 or 1");
        result.trace_update_pins = trace_update_pins == 1.f;
        if (result.trace_update_pins && !result.feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Update-pin tracing requires selective feedback");
        float trace_planar = read_number("VPR_H3D_TRACE_PLANAR_FEEDBACK", 0.f);
        if (trace_planar != 0.f && trace_planar != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_PLANAR_FEEDBACK must be 0 or 1");
        result.trace_planar = trace_planar == 1.f;
        if (result.trace_planar && !result.feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Planar feedback tracing requires selective feedback");
        float planar_feedback = read_number("VPR_H3D_PLANAR_FEEDBACK", 0.f);
        if (planar_feedback != 0.f && planar_feedback != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_PLANAR_FEEDBACK must be 0 or 1");
        result.planar_feedback = planar_feedback == 1.f;
        if (result.planar_feedback && !result.feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Planar feedback requires selective feedback");
        float trace_prior = read_number("VPR_H3D_TRACE_PRIOR", 0.f);
        if (trace_prior != 0.f && trace_prior != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_PRIOR must be 0 or 1");
        result.trace_prior = trace_prior == 1.f;
        float eligibility = read_number("VPR_H3D_ELIGIBILITY_TRIGGER", 0.f);
        if (eligibility != 0.f && eligibility != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_ELIGIBILITY_TRIGGER must be 0 or 1");
        result.eligibility_trigger = eligibility == 1.f;
        if (result.eligibility_trigger && !result.feedback)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Eligibility trigger requires selective feedback");
        const char* action_env = std::getenv("VPR_H3D_FEEDBACK_ACTION");
        std::string action = action_env ? action_env : "all";
        result.feedback_action_name = action;
        if (action == "all") result.feedback_action = e_h3d_feedback_action::ALL;
        else if (action == "clear") result.feedback_action = e_h3d_feedback_action::CLEAR_ONLY;
        else if (action == "reassign") result.feedback_action = e_h3d_feedback_action::REASSIGN_ONLY;
        else if (action == "finite") result.feedback_action = e_h3d_feedback_action::FINITE_ONLY;
        else if (action == "incomplete") result.feedback_action = e_h3d_feedback_action::INCOMPLETE_ONLY;
        else VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_FEEDBACK_ACTION must be all, clear, reassign, finite or incomplete");
        if (!result.feedback && result.feedback_action != e_h3d_feedback_action::ALL)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Feedback action ablation requires selective feedback");
        result.final_trace = std::getenv("VPR_H3D_FINAL_TRACE") != nullptr;
        if(const char* text=std::getenv("VPR_H3D_BOUNDED_AFTER_LEGAL")) {
            if(std::string(text)!="0" && std::string(text)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_BOUNDED_AFTER_LEGAL must be0 or1");
            result.bounded_after_legal=std::string(text)=="1";
        }
        if(result.bounded_after_legal && (!std::getenv("VPR_H3D_BOUNDED_CRITICAL_GUIDE") || result.post_legal_release || result.post_legal_freeze))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"After-legal bounded policy requires its configured cost and separate release/freeze controls disabled");
        if(const char* text=std::getenv("VPR_H3D_TRACE_GUIDE_INFLUENCE")) {
            if(std::string(text)!="0" && std::string(text)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_TRACE_GUIDE_INFLUENCE must be 0 or 1");
            result.trace_guide_influence=std::string(text)=="1";
        }
        if(const char* text=std::getenv("VPR_H3D_TRACE_SEARCH_DOMAIN")) {
            if(std::string(text)!="0" && std::string(text)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_TRACE_SEARCH_DOMAIN must be 0 or 1");
            result.trace_search_domain=std::string(text)=="1";
        }
        if(result.trace_search_domain && !result.trace_guide_influence)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Search domain tracing requires influence tracing");
        if(result.trace_guide_influence && (!result.edge_encoding || result.mode==e_h3d_mode::OFF))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Guide influence tracing requires serial edge-encoding H3D routing");
        if (result.feedback && (!result.use_scc || result.mode != e_h3d_mode::STATIC))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Selective feedback requires static SCC planning");
        return result;
    }();
    return value;
}

/** @brief Persistent exact reachability caches and per-net surrogate plans.
 *
 * Searches stay on the starting die and stop on first entering CHANZ. A forward
 * source search and reverse sink search therefore certify a real single-crossing
 * walk. Congestion never removes candidates. Reverse CSR is only an auxiliary
 * index of the unchanged RRG; it does not create legal reverse routing edges.
 */
class H3dPlanner {
  public:
    /** @brief Build a reverse-edge CSR and identify native physical channels. */
    H3dPlanner() {
        auto start = std::chrono::steady_clock::now();
        const auto& graph = g_vpr_ctx.device().rr_graph;
        size_t count = graph.num_nodes();
        z_index_.resize(count, -1);
        for (RRNodeId node : graph.nodes()) {
            if (settings().edge_encoding ? h3d_crossing_entry(graph, node) : graph.node_type(node) == e_rr_type::CHANZ) {
                z_index_[node] = channels_.size();
                channels_.push_back(node);
            }
        }
        if (settings().use_scc) {
            fast_plan_ = std::make_unique<H3dFastPlan>(graph, settings().delay_cost, settings().delay_budget, settings().edge_encoding);
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            VTR_LOG("H3D_INIT reachability=scc channels=%zu init_seconds=%.6f\n", channels_.size(), planning_seconds_);
            VTR_LOG("H3D_CONFIG candidate_cost=%s min_criticality=%g delay_budget=%zu\n",
                    settings().delay_cost ? "delay" : "geometry", settings().min_criticality, settings().delay_budget);
            VTR_LOG("H3D_GRAPH_ENCODING %s graph_unchanged=1\n", settings().edge_encoding ? "edge" : "native");
            return;
        }
        reverse_start_.resize(count, 0);
        reverse_count_.resize(count, 0);
        distance_.resize(count, -1);
        for (RRNodeId node : graph.nodes())
            for (auto edge : graph.node_out_edges(node))
                ++reverse_count_[graph.edge_sink_node(node, edge)];
        size_t total = 0;
        for (RRNodeId node : graph.nodes()) {
            reverse_start_[node] = total;
            total += reverse_count_[node];
        }
        reverse_edges_.resize(total);
        auto cursor = reverse_start_;
        for (RRNodeId node : graph.nodes())
            for (auto edge : graph.node_out_edges(node))
                reverse_edges_[cursor[graph.edge_sink_node(node, edge)]++] = node;
        if (channels_.empty())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes require native CHANZ; legacy encodings need an explicit adapter");
        planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        VTR_LOG("H3D_INIT channels=%zu reverse_edges=%zu candidates=%zu miss_weight=%g opening_weight=%g init_seconds=%.6f\n",
                channels_.size(), total, settings().candidates, settings().miss_weight, settings().opening_weight, planning_seconds_);
    }

    /** @brief Save old channels so replanning does not discard already used choices. */
    void capture(ParentNetId net) {
        captured_net_ = net;
        captured_actual_.clear();
        captured_overuse_ = false;
        captured_planar_nodes_ = captured_guided_paths_ = captured_planar_paths_ = 0;
        if (settings().feedback) {
            auto prior = guides_.find(net);
            backup_had_guide_ = prior != guides_.end();
            backup_guides_ = backup_had_guide_ ? prior->second : std::vector<t_h3d_connection_guide>{};
            auto state = feedback_state_.find(net);
            backup_had_state_ = state != feedback_state_.end();
            backup_state_ = backup_had_state_ ? state->second : t_feedback_state{};
            const auto& graph = g_vpr_ctx.device().rr_graph;
            const auto& routing = g_vpr_ctx.routing();
            if (routing.route_trees[net]) {
                for (const auto& node : routing.route_trees[net]->all_nodes()) {
                    auto parent = node.parent();
                    if (settings().edge_encoding ? parent && h3d_crosses_layers(graph, parent->inode, node.inode)
                                                 : graph.node_type(node.inode) == e_rr_type::CHANZ) {
                        RRNodeId identity = settings().edge_encoding ? parent->inode : node.inode;
                        captured_actual_.insert(identity);
                        // Only overload at a recommended actual crossing triggers
                        // this signal; ordinary rerouting by itself is insufficient.
                        bool recommended = false;
                        for (const auto& guide : backup_guides_)
                            recommended |= std::binary_search(guide.preferred.begin(), guide.preferred.end(), identity);
                        captured_overuse_ |= recommended && (routing.rr_node_route_inf[identity].occ() > graph.node_capacity(identity)
                                                             || routing.rr_node_route_inf[node.inode].occ() > graph.node_capacity(node.inode));
                    }
                }
            }
            for (const auto& guide : backup_guides_)
                for (RRNodeId node : guide.preferred)
                    captured_overuse_ |= routing.rr_node_route_inf[node].occ() > graph.node_capacity(node);
            bool inspect_guided_planar = settings().planar_feedback
                                        && std::any_of(backup_guides_.begin(), backup_guides_.end(),
                                                       [](const auto& guide) { return !guide.preferred.empty(); });
            if ((settings().trace_planar || inspect_guided_planar) && routing.route_trees[net]) {
                const auto& tree = *routing.route_trees[net];
                std::set<RRNodeId> ordinary_overused;
                std::string resources;
                for (const auto& node : tree.all_nodes()) {
                    auto type = graph.node_type(node.inode);
                    auto parent = node.parent();
                    // Count planar channel resources away from the encoded
                    // crossing entry and its immediately reached destination.
                    bool ordinary = (type == e_rr_type::CHANX || type == e_rr_type::CHANY)
                                    && z_index_[node.inode] < 0
                                    && (!parent || !h3d_crosses_layers(graph, parent->inode, node.inode));
                    int occupancy = routing.rr_node_route_inf[node.inode].occ();
                    if (ordinary && occupancy > graph.node_capacity(node.inode)) ordinary_overused.insert(node.inode);
                }
                captured_planar_nodes_ = ordinary_overused.size();
                if (settings().trace_planar)
                    for (RRNodeId node : ordinary_overused)
                        resources += std::to_string(size_t(node)) + ":" + std::to_string(routing.rr_node_route_inf[node].occ())
                                     + ":" + std::to_string(graph.node_capacity(node)) + ";";
                for (size_t pin = 1; pin < backup_guides_.size(); ++pin) {
                    if (backup_guides_[pin].preferred.empty()) continue;
                    auto node = tree.find_by_isink(pin);
                    if (!node) continue;
                    ++captured_guided_paths_;
                    std::string overloaded;
                    bool affected = false;
                    while (node) {
                        if (ordinary_overused.contains(node->inode)) {
                            affected = true;
                            if (!settings().trace_planar) break;
                            overloaded += std::to_string(size_t(node->inode)) + ";";
                        }
                        node = node->parent();
                    }
                    captured_planar_paths_ += affected;
                    if (settings().trace_planar && affected)
                        VTR_LOG("H3D_PLANAR_PATH net=%zu pin=%zu overused=%s\n", size_t(net), pin, overloaded.c_str());
                }
                if (settings().trace_planar)
                    VTR_LOG("H3D_PLANAR_CAPTURE net=%zu nodes=%zu guided_paths=%zu affected_paths=%zu overused=%s\n",
                            size_t(net), captured_planar_nodes_, captured_guided_paths_, captured_planar_paths_, resources.c_str());
            }
        }
        current_channels_.clear();
        const auto& tree = g_vpr_ctx.routing().route_trees[net];
        if (tree)
            for (const auto& node : tree->all_nodes())
                if (z_index_[node.inode] >= 0)
                    current_channels_.insert(z_index_[node.inode]);
    }

    /** @brief Build source/sink feasible sets, then rank independently or solve the hierarchy. */
    void plan(ParentNetId net, int iteration, float pres_fac, const std::vector<float>& criticality, const std::vector<size_t>& remaining_targets) {
        if (plans_frozen_) {
            ++frozen_prepare_calls_;
            return;
        }
        bool refresh = settings().mode == e_h3d_mode::STATIC && guides_.contains(net);
        if (refresh && !settings().feedback) return;
        auto start = std::chrono::steady_clock::now();
        if (refresh) {
            ++refresh_checks_;
            auto& state = feedback_state_.at(net);
            const auto& graph = g_vpr_ctx.device().rr_graph;
            const auto& terminals = g_vpr_ctx.routing().net_rr_terminals[net];
            double drift = 0.;
            size_t newly_missing = 0;
            std::vector<bool> drift_targets;
            if (settings().target_drift) {
                drift_targets.assign(criticality.size(), false);
                for (size_t pin : remaining_targets) drift_targets.at(pin) = true;
            }
            for (size_t pin = 1; pin < criticality.size(); ++pin) {
                if (settings().target_drift && !drift_targets[pin]) continue;
                if (graph.node_layer_low(terminals[0]) != graph.node_layer_low(terminals[pin])
                    && std::max(criticality[pin], state.criticality[pin]) >= settings().min_criticality) {
                    drift = std::max(drift, double(std::abs(criticality[pin] - state.criticality[pin])));
                    newly_missing += state.criticality[pin] < settings().min_criticality
                                     && criticality[pin] >= settings().min_criticality
                                     && guides_.at(net).at(pin).preferred.empty();
                }
            }
            eligibility_checks_ += newly_missing > 0;
            size_t difference = 0;
            for (RRNodeId node : captured_actual_) difference += !state.actual.contains(node);
            for (RRNodeId node : state.actual) difference += !captured_actual_.contains(node);
            size_t union_size = (difference + captured_actual_.size() + state.actual.size()) / 2;
            double change = state.observed && union_size ? double(difference) / union_size : 0.;
            bool original_due = h3d_feedback_due(iteration, state.last_attempt, settings().cooldown, captured_overuse_, drift, change);
            bool with_eligibility = h3d_feedback_due(iteration, state.last_attempt, settings().cooldown, captured_overuse_, drift, change, newly_missing > 0);
            eligibility_opportunities_ += with_eligibility && !original_due;
            bool base_due = settings().eligibility_trigger ? with_eligibility : original_due;
            bool planar_due = h3d_feedback_due(iteration, state.last_attempt, settings().cooldown,
                                              captured_planar_paths_ > 0, 0., 0.);
            bool due = base_due || (settings().planar_feedback && planar_due);
            if (settings().trace_target_gate) {
                double target_drift = 0.;
                size_t target_missing = 0, target_eligible = 0, target_guided = 0;
                for (size_t pin : remaining_targets) {
                    target_guided += !guides_.at(net).at(pin).preferred.empty();
                    if (graph.node_layer_low(terminals[0]) == graph.node_layer_low(terminals[pin])) continue;
                    target_eligible += criticality[pin] >= settings().min_criticality;
                    if (std::max(criticality[pin], state.criticality[pin]) < settings().min_criticality) continue;
                    target_drift = std::max(target_drift, double(std::abs(criticality[pin] - state.criticality[pin])));
                    target_missing += state.criticality[pin] < settings().min_criticality
                                      && criticality[pin] >= settings().min_criticality
                                      && guides_.at(net).at(pin).preferred.empty();
                }
                bool target_original_due = h3d_feedback_due(iteration, state.last_attempt, settings().cooldown,
                                                           captured_overuse_, target_drift, change);
                VTR_LOG("H3D_TARGET_GATE net=%zu iter=%d last_attempt=%d cooldown=%d targets=%zu eligible=%zu guided=%zu crossing_overuse=%d drift=%.17g target_drift=%.17g missing=%zu target_missing=%zu change=%.17g original_due=%d target_original_due=%d due=%d\n",
                        size_t(net), iteration, state.last_attempt, settings().cooldown, remaining_targets.size(),
                        target_eligible, target_guided, captured_overuse_, drift, target_drift, newly_missing,
                        target_missing, change, original_due, target_original_due, due);
            }
            if (settings().trace_planar)
                VTR_LOG("H3D_PLANAR_CONTEXT net=%zu iter=%d last_attempt=%d cooldown=%d crossing_overuse=%d drift=%.17g change=%.17g original_due=%d due=%d planar_nodes=%zu guided_paths=%zu affected_paths=%zu\n",
                        size_t(net), iteration, state.last_attempt, settings().cooldown, captured_overuse_, drift, change,
                        original_due, due, captured_planar_nodes_, captured_guided_paths_, captured_planar_paths_);
            if (!due) {
                ++refresh_skips_;
                refresh_check_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
                return;
            }
            if (settings().trace_prior)
                VTR_LOG("H3D_REFRESH_TRIGGER net=%zu iter=%d last_attempt=%d newly_missing=%zu original_due=%d eligibility_enabled=%d extra_attempt=%d\n",
                        size_t(net), iteration, state.last_attempt, newly_missing, original_due,
                        settings().eligibility_trigger, !original_due);
            eligibility_extra_attempts_ += settings().eligibility_trigger && with_eligibility && !original_due;
            if (settings().planar_feedback && !base_due) {
                ++planar_extra_attempts_;
                VTR_LOG("H3D_PLANAR_TRIGGER net=%zu iter=%d last_attempt=%d cooldown=%d affected_paths=%zu planar_nodes=%zu\n",
                        size_t(net), iteration, state.last_attempt, settings().cooldown, captured_planar_paths_, captured_planar_nodes_);
            }
            state.last_attempt = iteration;
            ++refresh_attempts_;
            refresh_overuse_ += captured_overuse_;
            refresh_drift_ += drift >= .15;
            refresh_path_ += change >= .25;
        }
        if (fast_plan_) {
            std::vector<RRNodeId> previous;
            for (size_t c : current_channels_)
                previous.push_back(channels_[c]);
            auto result = fast_plan_->plan(net, criticality, previous, pres_fac, settings().candidates,
                                           settings().opening_weight, settings().miss_weight,
                                           settings().mode != e_h3d_mode::CANDIDATES, settings().min_criticality,
                                           refresh ? &guides_.at(net) : nullptr, settings().refresh_margin, settings().trace_prior,
                                           refresh && settings().target_feedback ? &remaining_targets : nullptr);
            ++plans_;
            groups_ += result.groups;
            no_candidate_ += result.no_candidate;
            bool accept = !refresh || (result.refresh_accepted
                                      && h3d_allow_refresh_action(settings().feedback_action, result.refresh_clear, std::isfinite(result.previous_cost)));
            if (refresh && settings().trace_prior) {
                const auto& old_guides = guides_.at(net);
                const auto& old_criticality = feedback_state_.at(net).criticality;
                size_t newly_eligible_empty = 0, previously_eligible_empty = 0, old_guided = 0;
                for (const auto& guide : old_guides) old_guided += !guide.preferred.empty();
                for (int pin : result.prior_empty_pins) {
                    bool newly_eligible = old_criticality.at(pin) < settings().min_criticality
                                          && criticality.at(pin) >= settings().min_criticality;
                    newly_eligible_empty += newly_eligible;
                    previously_eligible_empty += !newly_eligible;
                    VTR_LOG("H3D_PRIOR_PIN net=%zu iter=%d pin=%d reason=empty old_criticality=%.9g new_criticality=%.9g newly_eligible=%d\n",
                            size_t(net), iteration, pin, old_criticality.at(pin), criticality.at(pin), newly_eligible);
                }
                VTR_LOG("H3D_PRIOR_REASON net=%zu iter=%d table=%d clear=%d old_guided=%zu leaves=%zu pairs=%zu empty=%zu multiple=%zu outside=%zu branch_missing=%zu branch_nonfinite=%zu opening_nonfinite=%zu empty_newly_eligible=%zu empty_previously_eligible=%zu proposed_accepted=%d accepted=%d old_cost=%g new_cost=%g\n",
                        size_t(net), iteration, result.prior_table_diagnosed, result.refresh_clear, old_guided,
                        result.prior_leaves, result.prior_pairs, result.prior_empty_pins.size(), result.prior_multiple,
                        result.prior_outside_table, result.prior_branch_missing, result.prior_branch_nonfinite,
                        result.prior_opening_nonfinite, newly_eligible_empty, previously_eligible_empty,
                        result.refresh_accepted, accept, result.previous_cost, result.proposed_cost);
            }
            if (refresh && settings().feedback_action != e_h3d_feedback_action::ALL)
                VTR_LOG("H3D_REFRESH_ACTION net=%zu iter=%d policy=%s proposed_accepted=%d clear=%d accepted=%d prior_finite=%d\n",
                        size_t(net), iteration,
                        settings().feedback_action_name.c_str(),
                        result.refresh_accepted, result.refresh_clear, accept, std::isfinite(result.previous_cost));
            if (refresh) {
                refresh_accepts_ += accept;
                VTR_LOG("H3D_REFRESH net=%zu iter=%d accepted=%d old_cost=%g new_cost=%g\n",
                        size_t(net), iteration, accept, result.previous_cost, result.proposed_cost);
            }
            if (accept) {
                // Construct membership once. Repeated linear scans here cost
                // O(sinks * targets) on high-fanout reroutes without changing
                // any planning or native routing decisions.
                std::vector<bool> target_membership;
                if (refresh && (settings().target_feedback || settings().trace_update_pins)) {
                    target_membership.assign(result.guides.size(), false);
                    for (size_t pin : remaining_targets) target_membership.at(pin) = true;
                }
                if (refresh && settings().trace_update_pins) {
                    const auto& prior = guides_.at(net);
                    const auto& tree = g_vpr_ctx.routing().route_trees[net];
                    VTR_ASSERT(prior.size() == result.guides.size());
                    for (size_t pin = 1; pin < prior.size(); ++pin) {
                        const auto& before = prior[pin].preferred;
                        const auto& after = result.guides[pin].preferred;
                        if (before == after) continue;
                        // The sink lookup may retain a pointer after pruning; the native
                        // reached bitmap is the authoritative membership state.
                        bool retained = tree && tree->get_is_isink_reached().get(pin);
                        bool targeted = target_membership.at(pin);
                        VTR_ASSERT(!retained || !targeted);
                        std::string old_ids, new_ids;
                        for (RRNodeId node : before) old_ids += std::to_string(size_t(node)) + ";";
                        for (RRNodeId node : after) new_ids += std::to_string(size_t(node)) + ";";
                        ++update_pin_records_;
                        update_pin_retained_ += retained;
                        update_pin_targeted_ += targeted;
                        VTR_LOG("H3D_UPDATE_PIN net=%zu iter=%d pin=%zu retained=%d targeted=%d criticality=%.17g old=%s new=%s\n",
                                size_t(net), iteration, pin, retained, targeted, double(criticality[pin]), old_ids.c_str(), new_ids.c_str());
                    }
                }
                // Non-target preferences and their timing-generation metadata remain
                // unchanged. The transaction/best-route snapshots still own the full state.
                auto generation_criticality = criticality;
                if (refresh && settings().target_feedback) {
                    generation_criticality = feedback_state_.at(net).criticality;
                    for (size_t pin : remaining_targets) generation_criticality.at(pin) = criticality.at(pin);
                    for (size_t pin = 1; pin < result.guides.size(); ++pin) {
                        if (target_membership.at(pin)) continue;
                        const auto& before = guides_.at(net).at(pin);
                        const auto& after = result.guides.at(pin);
                        VTR_ASSERT(before.preferred == after.preferred
                                   && before.miss_weight == after.miss_weight
                                   && before.edge_encoding == after.edge_encoding
                                   && before.timing_miss_penalty == after.timing_miss_penalty
                                   && before.timing_regret == after.timing_regret
                                   && before.timing_alternatives == after.timing_alternatives
                                   && before.bounded_critical == after.bounded_critical
                                   && before.bounded_cap_only == after.bounded_cap_only
                                   && before.bounded_reliability == after.bounded_reliability
                                   && before.bounded_unit_seconds == after.bounded_unit_seconds
                                   && before.bounded_beta == after.bounded_beta
                                   && before.bounded_penalty_seconds == after.bounded_penalty_seconds);
                        VTR_ASSERT(generation_criticality.at(pin) == feedback_state_.at(net).criticality.at(pin));
                    }
                }
                guides_[net] = std::move(result.guides);
                if (settings().feedback || settings().final_trace)
                    feedback_state_[net] = {iteration, std::move(generation_criticality), captured_actual_, false};
            }
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            return;
        }
        const auto& graph = g_vpr_ctx.device().rr_graph;
        const auto& terminals = g_vpr_ctx.routing().net_rr_terminals[net];
        RRNodeId source = terminals[0];
        auto& guides = guides_[net];
        guides.assign(terminals.size(), {});
        std::vector<int> remote_pins;
        for (size_t pin = 1; pin < terminals.size(); ++pin)
            if (graph.node_layer_low(source) != graph.node_layer_low(terminals[pin]))
                remote_pins.push_back(pin);
        if (remote_pins.empty()) {
            planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            return;
        }
        ++plans_;
        const auto& from_source = distances_(source, false);
        std::set<size_t> pool;
        std::vector<double> opening(channels_.size(), 0.);
        for (size_t c = 0; c < channels_.size(); ++c) {
            RRNodeId node = channels_[c];
            float base = g_vpr_ctx.device().rr_indexed_data[graph.node_cost_index(node)].base_cost;
            double congestion = get_rr_cong_cost(node, pres_fac) / std::max(base, 1.e-20f);
            opening[c] = std::max(0, from_source[c]) + settings().opening_weight * congestion;
        }
        for (int pin : remote_pins) {
            const auto& to_sink = distances_(terminals[pin], true);
            std::vector<std::pair<double, size_t>> ranked;
            for (size_t c = 0; c < channels_.size(); ++c) {
                if (from_source[c] < 0 || to_sink[c] < 0)
                    continue;
                double branch = to_sink[c] * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * from_source[c];
                ranked.emplace_back(opening[c] + branch, c);
            }
            std::sort(ranked.begin(), ranked.end());
            std::set<size_t> chosen;
            if (!ranked.empty()) {
                chosen.insert(ranked.front().second);
                // Retain cost quality while spreading the alternatives across
                // distinct XY sites. Channels at one site can still differ in
                // directed access and are kept when fewer sites are available.
                size_t shortlist = std::min(ranked.size(), settings().candidates * 8);
                while (chosen.size() < settings().candidates && chosen.size() < ranked.size()) {
                    double best_score = -1.;
                    size_t best = ranked.front().second;
                    for (size_t i = 0; i < shortlist; ++i) {
                        size_t c = ranked[i].second;
                        if (chosen.contains(c)) continue;
                        int spread = std::numeric_limits<int>::max();
                        for (size_t previous : chosen) {
                            int distance = std::abs(graph.node_xlow(channels_[c]) - graph.node_xlow(channels_[previous]))
                                           + std::abs(graph.node_ylow(channels_[c]) - graph.node_ylow(channels_[previous]));
                            spread = std::min(spread, distance);
                        }
                        double score = (1. + spread) / (1. + ranked[i].first - ranked.front().first);
                        if (score > best_score) {
                            best_score = score;
                            best = c;
                        }
                    }
                    if (best_score < 0.) break;
                    chosen.insert(best);
                }
            }
            for (size_t c : current_channels_)
                if (from_source[c] >= 0 && to_sink[c] >= 0)
                    chosen.insert(c);
            if (chosen.empty()) {
                ++no_candidate_;
                continue;
            }
            pool.insert(chosen.begin(), chosen.end());
            for (size_t c : chosen)
                guides[pin].preferred.push_back(channels_[c]);
            guides[pin].miss_weight = settings().miss_weight;
        }
        if (settings().mode != e_h3d_mode::CANDIDATES) {
            std::vector<t_h3d_plan_leaf> leaves;
            for (int pin : remote_pins) {
                if (guides[pin].preferred.empty()) continue;
                RRNodeId sink = terminals[pin];
                const auto& to_sink = distances_(sink, true);
                t_h3d_plan_leaf leaf{pin, graph.node_xlow(sink), graph.node_ylow(sink), {}};
                for (size_t c : pool)
                    if (from_source[c] >= 0 && to_sink[c] >= 0)
                        leaf.candidates.push_back({c, to_sink[c] * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * from_source[c]});
                leaves.push_back(std::move(leaf));
            }
            auto result = h3d_plan_partition(leaves, opening);
            if (std::isfinite(result.cost)) {
                groups_ += result.groups;
                for (const auto& [pin, channel] : result.assignment)
                    guides[pin].preferred = {channels_[channel]};
            }
        }
        for (auto& guide : guides)
            std::sort(guide.preferred.begin(), guide.preferred.end());
        planning_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    }

    /** @brief Read the stable guide storage while a net's sink searches execute. */
    const t_h3d_connection_guide* guide(ParentNetId net, int pin) const {
        if (guides_released_) return nullptr;
        auto found = guides_.find(net);
        if (found == guides_.end() || found->second.at(pin).preferred.empty())
            return nullptr;
        return &found->second[pin];
    }

    /** @brief Keep planning independent while releasing future search pressure. */
    void enter_legal_refinement(int iteration) {
        if(settings().bounded_after_legal && !bounded_legal_phase) {
            bounded_legal_phase=true;
            VTR_LOG("H3D_BOUNDED_PHASE iter=%d active=1 reason=native_legal_convergence\n",iteration);
        }
        if (settings().post_legal_release && !guides_released_) {
            guides_released_ = true;
            VTR_LOG("H3D_POST_LEGAL_RELEASE iter=%d guide_use=0 feedback_unchanged=1\n", iteration);
        }
        if (settings().post_legal_freeze && !plans_frozen_) {
            plans_frozen_ = true;
            VTR_LOG("H3D_POST_LEGAL_FREEZE iter=%d guide_use=1 feedback_plans=0\n", iteration);
        }
    }

    /** @brief Report cumulative preprocessing/search overhead separately from native A*. */
    void log() const {
        if (plans_frozen_)
            VTR_LOG("H3D_POST_LEGAL_FREEZE_SUMMARY skipped_prepare_calls=%zu\n", frozen_prepare_calls_);
        VTR_LOG("H3D_UPDATE_PINS_SUMMARY enabled=%d records=%zu retained=%zu targeted=%zu\n",
                settings().trace_update_pins, update_pin_records_, update_pin_retained_, update_pin_targeted_);
        VTR_LOG("H3D_PLANAR_FEEDBACK enabled=%d extra_attempts=%zu\n", settings().planar_feedback, planar_extra_attempts_);
        VTR_LOG("H3D_PLAN plans=%zu groups=%zu bfs_nodes=%zu cache_entries=%zu no_candidate=%zu fallback=%zu planning_seconds=%.6f\n",
                plans_, groups_, bfs_nodes_, forward_cache_.size() + reverse_cache_.size(), no_candidate_, fallbacks_, planning_seconds_);
        VTR_LOG("H3D_TREE guided_paths=%zu preferred_paths=%zu rollbacks=%zu\n", guided_observations_, preferred_observations_, rollbacks_);
        VTR_LOG("H3D_ELIGIBILITY_TRIGGER enabled=%d checks_newly_missing=%zu opportunities_after_cooldown=%zu extra_attempts=%zu\n",
                settings().eligibility_trigger, eligibility_checks_, eligibility_opportunities_, eligibility_extra_attempts_);
        VTR_LOG("H3D_FEEDBACK checks=%zu skipped=%zu attempts=%zu accepted=%zu overuse=%zu criticality=%zu path=%zu check_seconds=%.6f\n",
                refresh_checks_, refresh_skips_, refresh_attempts_, refresh_accepts_, refresh_overuse_, refresh_drift_, refresh_path_, refresh_check_seconds_);
        if (fast_plan_) fast_plan_->log();
    }

    /** @brief Count an explicit fallback retry. */
    void fallback() { ++fallbacks_; }

    /** @brief Measure preferences on each actual source-to-sink route-tree path. */
    void observe(ParentNetId net) {
        auto found = guides_.find(net);
        const auto& tree = g_vpr_ctx.routing().route_trees[net];
        if (found == guides_.end() || !tree) return;
        if (settings().feedback && !feedback_state_.at(net).observed) {
            auto& state = feedback_state_.at(net);
            state.actual.clear();
            const auto& graph = g_vpr_ctx.device().rr_graph;
            for (const auto& node : tree->all_nodes()) {
                auto parent = node.parent();
                if (settings().edge_encoding ? parent && h3d_crosses_layers(graph, parent->inode, node.inode)
                                             : graph.node_type(node.inode) == e_rr_type::CHANZ)
                    state.actual.insert(settings().edge_encoding ? parent->inode : node.inode);
            }
            state.observed = true;
        }
        for (size_t pin = 1; pin < found->second.size(); ++pin) {
            const auto& preferred = found->second[pin].preferred;
            if (preferred.empty()) continue;
            auto node = tree->find_by_isink(pin);
            if (!node) continue;
            ++guided_observations_;
            while (node) {
                auto parent = node->parent();
                const auto& graph = g_vpr_ctx.device().rr_graph;
                bool eligible = !settings().edge_encoding || (parent && h3d_crosses_layers(graph, parent->inode, node->inode));
                RRNodeId identity = settings().edge_encoding && parent ? parent->inode : node->inode;
                if (eligible && std::binary_search(preferred.begin(), preferred.end(), identity)) {
                    ++preferred_observations_;
                    break;
                }
                node = node->parent();
            }
        }
    }

    /** @brief Count restoration of a complete prior tree and its bookkeeping. */
    void rollback() {
        ++rollbacks_;
        if (settings().feedback) {
            if (backup_had_guide_) guides_[captured_net_] = backup_guides_;
            else guides_.erase(captured_net_);
            if (backup_had_state_) feedback_state_[captured_net_] = backup_state_;
            else feedback_state_.erase(captured_net_);
            ++guide_rollbacks_;
            VTR_LOG("H3D_GUIDE_ROLLBACK net=%zu restored=1\n", size_t(captured_net_));
        }
    }

    /** @brief Preserve the guide version corresponding to VPR's best complete routing. */
    void save_best() {
        if (!settings().final_trace) return;
        best_guides_ = guides_;
        best_feedback_state_ = feedback_state_;
        best_bounded_phase_ = !settings().bounded_after_legal || bounded_legal_phase;
    }

    /** @brief Observe restored final route trees once, without affecting routing or STA. */
    void final_trace(bool success) const {
        if (!settings().final_trace) return;
        const auto& chosen = success ? best_guides_ : guides_;
        const auto& states = success ? best_feedback_state_ : feedback_state_;
        const auto& graph = g_vpr_ctx.device().rr_graph;
        const auto& routing = g_vpr_ctx.routing();
        if(settings().bounded_after_legal)
            VTR_LOG("H3D_FINAL_BOUNDED_PHASE success=%d milestone_seen=%d active_when_saved=%d\n",
                int(success),int(bounded_legal_phase),int(success ? best_bounded_phase_ : bounded_legal_phase));
        std::ofstream out("h3d_final_guides.csv");
        if (!out) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot create final guide trace");
        out << "net,pin,source,sink,planned_criticality,preferred,actual_crossings,routed,adopted,timing_penalty_seconds\n";
        std::vector<ParentNetId> nets;
        for (const auto& entry : chosen) nets.push_back(entry.first);
        std::sort(nets.begin(), nets.end());
        size_t guided = 0, routed = 0, adopted = 0;
        for (ParentNetId net : nets) {
            const auto& guides = chosen.at(net);
            const auto& tree = routing.route_trees[net];
            const auto& terminals = routing.net_rr_terminals[net];
            for (size_t pin = 1; pin < guides.size(); ++pin) {
                const auto& guide = guides[pin];
                if (guide.preferred.empty()) continue;
                ++guided;
                if(guide.bounded_critical) {
                    std::ostringstream ids;for(auto node:guide.preferred) {if(ids.tellp()>0)ids<<',';ids<<size_t(node);}
                    VTR_LOG("H3D_FINAL_BOUNDED_GUIDE net=%zu pin=%zu reliability=%.17g unit_seconds=%.17g beta=%.17g penalty_seconds=%.17g preferred=%s\n",
                        size_t(net),pin,guide.bounded_reliability,guide.bounded_unit_seconds,guide.bounded_beta,double(guide.bounded_penalty_seconds),ids.str().c_str());
                    if(guide.bounded_cap_only)
                        VTR_LOG("H3D_FINAL_BOUNDED_CAP net=%zu pin=%zu configured=1\n",size_t(net),pin);
                }
                if (settings().dp_tie_pressure || settings().dp_margin_pressure)
                    VTR_LOG("H3D_FINAL_PRESSURE net=%zu pin=%zu miss_weight=%.9g\n", size_t(net), pin, double(guide.miss_weight));
                std::set<RRNodeId> crossings;
                bool reached = tree && tree->find_by_isink(pin);
                if (reached) {
                    ++routed;
                    auto node = tree->find_by_isink(pin);
                    while (node) {
                        auto parent = node->parent();
                        if (settings().edge_encoding ? parent && h3d_crosses_layers(graph, parent->inode, node->inode)
                                                     : graph.node_type(node->inode) == e_rr_type::CHANZ)
                            crossings.insert(settings().edge_encoding ? parent->inode : node->inode);
                        node = parent;
                    }
                }
                bool match = false;
                for (RRNodeId resource : crossings)
                    match |= std::binary_search(guide.preferred.begin(), guide.preferred.end(), resource);
                adopted += match;
                auto state = states.find(net);
                float criticality = state != states.end() ? state->second.criticality.at(pin) : -1.f;
                out << size_t(net) << ',' << pin << ',' << size_t(terminals[0]) << ',' << size_t(terminals[pin]) << ',' << criticality << ',';
                for (RRNodeId resource : guide.preferred) out << size_t(resource) << ';';
                out << ',';
                for (RRNodeId resource : crossings) out << size_t(resource) << ';';
                out << ',' << reached << ',' << match << ',' << guide.timing_miss_penalty << '\n';
            }
        }
        VTR_LOG("H3D_FINAL success=%d guided=%zu routed=%zu adopted=%zu guide_rollbacks=%zu\n", success, guided, routed, adopted, guide_rollbacks_);
    }

  private:
    bool best_bounded_phase_=false;
    /** @brief Cache directed same-die BFS distances to every first-crossing channel. */
    const std::vector<int>& distances_(RRNodeId terminal, bool reverse) {
        auto& cache = reverse ? reverse_cache_ : forward_cache_;
        auto found = cache.find(terminal);
        if (found != cache.end()) return found->second;
        const auto& graph = g_vpr_ctx.device().rr_graph;
        int layer = graph.node_layer_low(terminal);
        std::fill(distance_.begin(), distance_.end(), -1);
        std::vector<RRNodeId> queue{terminal};
        distance_[terminal] = 0;
        std::vector<int> result(channels_.size(), -1);
        for (size_t head = 0; head < queue.size(); ++head) {
            RRNodeId current = queue[head];
            ++bfs_nodes_;
            auto visit = [&](RRNodeId next) {
                if (distance_[next] >= 0) return;
                if (z_index_[next] >= 0) {
                    distance_[next] = distance_[current] + 1;
                    result[z_index_[next]] = distance_[next];
                } else if (graph.node_layer_low(next) == layer && graph.node_layer_high(next) == layer) {
                    distance_[next] = distance_[current] + 1;
                    queue.push_back(next);
                }
            };
            if (reverse) {
                size_t end = reverse_start_[current] + reverse_count_[current];
                for (size_t edge = reverse_start_[current]; edge < end; ++edge)
                    visit(reverse_edges_[edge]);
            } else {
                for (auto edge : graph.node_out_edges(current))
                    visit(graph.edge_sink_node(current, edge));
            }
        }
        return cache.emplace(terminal, std::move(result)).first->second;
    }

    /** @brief Guide generation state; replaced only after an accepted refresh. */
    struct t_feedback_state {
        int last_attempt = 1;                    ///< Cooldown timestamp.
        std::vector<float> criticality;           ///< Timing weights used by this guide.
        std::set<RRNodeId> actual;                ///< Actual crossings after its first successful route.
        bool observed = false;                   ///< Whether actual crossings have been initialized.
    };
    std::unordered_map<ParentNetId, t_feedback_state> feedback_state_, best_feedback_state_; ///< Per-net and best-route state.
    std::unordered_map<ParentNetId, std::vector<t_h3d_connection_guide>> best_guides_; ///< Best-route diagnostic guide versions.
    bool guides_released_ = false; ///< Per-trial monotone epoch, independent of route transactions.
    bool plans_frozen_ = false; ///< Separate epoch: preserve existing guide pressure.
    size_t frozen_prepare_calls_ = 0;
    ParentNetId captured_net_;                    ///< Current serial routing transaction.
    bool backup_had_guide_ = false, backup_had_state_ = false; ///< Exact restoration membership.
    std::vector<t_h3d_connection_guide> backup_guides_; ///< Transaction snapshot.
    t_feedback_state backup_state_;              ///< Transaction feedback snapshot.
    std::set<RRNodeId> captured_actual_;          ///< Pre-prune actual crossing resources.
    size_t eligibility_checks_ = 0, eligibility_opportunities_ = 0, eligibility_extra_attempts_ = 0; ///< Repeated eligible-gap check/trigger counts, not unique pins or nets.
    bool captured_overuse_ = false;               ///< Recommended crossing currently overloaded.
    size_t captured_planar_nodes_ = 0, captured_guided_paths_ = 0, captured_planar_paths_ = 0; ///< Pre-prune ordinary planar overuse and guided path counts.
    size_t update_pin_records_ = 0, update_pin_retained_ = 0, update_pin_targeted_ = 0; ///< Accepted preference-change observations, no influence on planning.
    size_t planar_extra_attempts_ = 0; ///< Refresh attempts newly admitted by guided-path planar overuse.
    size_t refresh_checks_ = 0, refresh_skips_ = 0, refresh_attempts_ = 0, refresh_accepts_ = 0; ///< Refresh work accounting.
    size_t refresh_overuse_ = 0, refresh_drift_ = 0, refresh_path_ = 0, guide_rollbacks_ = 0; ///< Trigger and restoration counts.
    double refresh_check_seconds_ = 0.;           ///< Includes gate work on skipped reroutes.
    std::vector<RRNodeId> channels_;                                              ///< Candidate index to native physical RR resource.
    std::unique_ptr<H3dFastPlan> fast_plan_;                                      ///< Optional SCC index with geometric surrogate planning.
    vtr::vector<RRNodeId, int> z_index_;                                          ///< RR resource to candidate index, -1 for planar resources.
    vtr::vector<RRNodeId, size_t> reverse_start_;                                 ///< Reverse CSR offset per resource.
    vtr::vector<RRNodeId, size_t> reverse_count_;                                 ///< Reverse CSR length per resource.
    std::vector<RRNodeId> reverse_edges_;                                         ///< Sources of original incoming directed edges.
    vtr::vector<RRNodeId, int> distance_;                                         ///< Reusable per-search BFS distance scratch.
    std::unordered_map<RRNodeId, std::vector<int>> forward_cache_;                ///< Source-to-channel distances.
    std::unordered_map<RRNodeId, std::vector<int>> reverse_cache_;                ///< Channel-to-sink distances.
    std::unordered_map<ParentNetId, std::vector<t_h3d_connection_guide>> guides_; ///< Guides indexed by net and terminal.
    std::set<size_t> current_channels_;                                           ///< Previous tree channels included before pruning.
    size_t plans_ = 0;                                                            ///< Completed planning events.
    size_t groups_ = 0;                                                           ///< Shared groups selected cumulatively.
    size_t bfs_nodes_ = 0;                                                        ///< BFS node expansions, separate from A* statistics.
    size_t no_candidate_ = 0;                                                     ///< Connections delegated to unmodified search.
    size_t fallbacks_ = 0;                                                        ///< Guided search failures retried without preferences.
    double planning_seconds_ = 0.;                                                ///< Includes reverse-index build and all cache/search/DP work.
    size_t guided_observations_ = 0;                                              ///< Cumulative routed sink paths with preferences.
    size_t preferred_observations_ = 0;                                           ///< Cumulative preferred-channel matches on those paths.
    size_t rollbacks_ = 0;                                                        ///< Fully restored failed/rejected signal-net transactions.
};

std::unique_ptr<H3dPlanner> planner; ///< Serial-router-owned experimental planner.

struct InfluenceBucket {
    size_t count=0,rows=0,finite=0,positive=0,below_unit=0;
    double extra=0.,physical=0.,timing=0.,maximum_extra=0.;
};
struct DomainLayer {
    size_t pushes=0;
    double minimum_delay=std::numeric_limits<double>::infinity();
    double minimum_backward=std::numeric_limits<double>::infinity();
    double minimum_total=std::numeric_limits<double>::infinity();
};
struct InfluenceState {
    size_t domain_searches=0,domain_rows=0,domain_omitted=0,domain_seed_rows=0,domain_seed_omitted=0,domain_local_seed_rows=0;
    std::vector<DomainLayer> domain_layers;

    size_t events=0,rows=0,attempts=0,contexts=0,context_omitted=0,current_net=0;
    int iteration=0,current_pin=0;
    std::array<size_t,7> group_rows{};
    std::array<InfluenceBucket,16> buckets{};
    double unit=1.e-10;
    bool bounded_mode=false;
    size_t bounded_applications=0,bounded_rows=0;
    double bounded_old_extra=0.,bounded_timing=0.;
};
std::unique_ptr<InfluenceState> influence;

int influence_focus(size_t net,int pin) {
    if(net==4674 && pin==9)return 0;
    if(net==4674 && pin==21)return 1;
    if(net==4675 && pin==23)return 2;
    return -1;
}
int influence_bin(double criticality) {
    return criticality<.7 ? 0 : criticality<.9 ? 1 : criticality<.95 ? 2 : 3;
}
std::string influence_preferences(const t_h3d_connection_guide* guide) {
    std::ostringstream out;
    if(guide)for(auto node:guide->preferred) {if(out.tellp()>0)out<<',';out<<size_t(node);}
    return out.str().empty() ? "-" : out.str();
}
void log_influence() {
    if(!influence)return;
    const auto& s=*influence;
    if(settings().trace_search_domain)
        VTR_LOG("H3D_SEARCH_DOMAIN_SUMMARY searches=%zu rows=%zu omitted=%zu seed_rows=%zu seed_omitted=%zu row_cap=20000 seed_cap=6000\n",
                s.domain_searches,s.domain_rows,s.domain_omitted,s.domain_seed_rows,s.domain_seed_omitted);
    VTR_LOG("H3D_GUIDE_INFLUENCE_SUMMARY iter=%d events=%zu rows=%zu omitted=%zu attempts=%zu contexts=%zu context_omitted=%zu row_cap=10000 unit_seconds=%.17g\n",
        s.iteration,s.events,s.rows,s.events-s.rows,s.attempts,s.contexts,s.context_omitted,s.unit);
    if(s.bounded_mode)
        VTR_LOG("H3D_BOUNDED_CRITICAL_SUMMARY iter=%d applications=%zu sampled=%zu omitted=%zu old_analytic_extra=%.17g weighted_timing_seconds=%.17g threshold=%.17g\n",
            s.iteration,s.bounded_applications,s.bounded_rows,s.bounded_applications-s.bounded_rows,s.bounded_old_extra,s.bounded_timing,double(.9f));
    for(size_t i=0;i<s.buckets.size();++i) {
        const auto& b=s.buckets[i];
        VTR_LOG("H3D_GUIDE_INFLUENCE_BUCKET iter=%d bin=%zu configurable=%zu preferred=%zu count=%zu rows=%zu finite=%zu positive=%zu below_unit=%zu analytic_extra=%.17g weighted_physical_seconds=%.17g weighted_timing_seconds=%.17g maximum_extra=%.17g\n",
            s.iteration,i/4,(i%4)/2,i%2,b.count,b.rows,b.finite,b.positive,b.below_unit,b.extra,b.physical,b.timing,b.maximum_extra);
    }
}

} // namespace

bool h3d_trace_guide_influence() {return settings().trace_guide_influence;}
bool h3d_trace_search_domain() {return settings().trace_search_domain;}
void h3d_domain_reset() {
    VTR_ASSERT(influence);auto& s=*influence;
    ++s.domain_searches;s.domain_local_seed_rows=0;
    s.domain_layers.assign(g_vpr_ctx.device().grid.get_num_layers(),DomainLayer{});
}
void h3d_domain_seed(RRNodeId node,float delay,float backward,float total,bool rcv) {
    VTR_ASSERT(influence);auto& s=*influence;const auto& graph=g_vpr_ctx.device().rr_graph;
    const size_t layer=graph.node_layer_low(node);VTR_ASSERT(layer<s.domain_layers.size());
    auto& l=s.domain_layers[layer];++l.pushes;
    l.minimum_delay=std::min(l.minimum_delay,double(delay));
    l.minimum_backward=std::min(l.minimum_backward,double(backward));
    l.minimum_total=std::min(l.minimum_total,double(total));
    if(influence_focus(s.current_net,s.current_pin)<0)return;
    if(s.domain_seed_rows>=6000 || s.domain_local_seed_rows>=100) {++s.domain_seed_omitted;return;}
    ++s.domain_seed_rows;++s.domain_local_seed_rows;
    VTR_LOG("H3D_SEARCH_DOMAIN_SEED iter=%d attempt=%zu search=%zu net=%zu pin=%d node=%zu layer=%zu delay_seconds=%.17g backward=%.17g total=%.17g rcv=%d\n",
        s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin,size_t(node),layer,double(delay),double(backward),double(total),int(rcv));
}
void h3d_domain_search(RRNodeId sink,float criticality,const t_h3d_connection_guide* guide,const t_bb& bb,bool rcv) {
    VTR_ASSERT(influence);auto& s=*influence;
    if(!guide && influence_focus(s.current_net,s.current_pin)<0)return;
    if(s.domain_rows>=20000) {++s.domain_omitted;return;}
    ++s.domain_rows;const auto& graph=g_vpr_ctx.device().rr_graph;
    size_t preferred_inside=0,preferred_cross_heads=0,admitted_cross_heads=0;
    if(guide)for(auto node:guide->preferred) {
        const bool from_inside=inside_bb(graph,node,bb);preferred_inside+=from_inside;
        for(auto edge:graph.edges(node)) {
            const auto head=graph.edge_sink_node(node,edge);
            if(!h3d_crosses_layers(graph,node,head))continue;
            ++preferred_cross_heads;
            admitted_cross_heads+=from_inside && (rcv || inside_bb(graph,head,bb));
        }
    }
    std::ostringstream layers;layers<<std::setprecision(17);
    for(size_t i=0;i<s.domain_layers.size();++i) {
        if(i)layers<<';';
        const auto& l=s.domain_layers[i];
        layers<<i<<','<<l.pushes<<','<<l.minimum_delay<<','<<l.minimum_backward<<','<<l.minimum_total;
    }
    VTR_LOG("H3D_SEARCH_DOMAIN iter=%d attempt=%zu search=%zu net=%zu pin=%d sink=%zu sink_layer=%d guide=%d criticality=%.17g preferred=%s preferred_inside=%zu crossing_heads=%zu admitted_heads=%zu xmin=%d xmax=%d ymin=%d ymax=%d layer_min=%d layer_max=%d rcv=%d layers=%s\n",
        s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin,size_t(sink),int(graph.node_layer_low(sink)),int(guide!=nullptr),double(criticality),influence_preferences(guide).c_str(),preferred_inside,preferred_cross_heads,admitted_cross_heads,bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.layer_min,bb.layer_max,int(rcv),layers.str().c_str());
}

bool h3d_bounded_critical_stage_active() {return !settings().bounded_after_legal || bounded_legal_phase;}

void h3d_influence_begin(ParentNetId net,int pin,RRNodeId sink,bool high_fanout,
                        float criticality,const t_h3d_connection_guide* guide) {
    VTR_ASSERT(influence);auto& s=*influence;
    ++s.attempts;s.current_net=size_t(net);s.current_pin=pin;
    if(influence_focus(size_t(net),pin)<0)return;
    if(s.contexts>=2000) {++s.context_omitted;return;}
    ++s.contexts;
    const auto& graph=g_vpr_ctx.device().rr_graph;
    const auto& tree=g_vpr_ctx.routing().route_trees[net];
    size_t nodes=0,expanded_on_sink_layer=0,crossings=0;std::ostringstream edges;edges<<std::setprecision(17);
    if(tree)for(const auto& node:tree->all_nodes()) {
        ++nodes;expanded_on_sink_layer+=node.re_expand && graph.node_layer_low(node.inode)==graph.node_layer_low(sink);
        auto parent=node.parent();
        if(!parent || !h3d_crosses_layers(graph,parent->inode,node.inode))continue;
        if(crossings++)edges<<';';
        edges<<size_t(parent->inode)<<','<<size_t(node.inode)<<','<<int(parent->re_expand)<<','<<int(node.re_expand)
             <<','<<double(parent->Tdel)<<','<<double(node.Tdel);
    }
    VTR_LOG("H3D_GUIDE_INFLUENCE_CONTEXT iter=%d attempt=%zu net=%zu pin=%d sink=%zu high_fanout=%d guide=%d criticality=%.17g preferred=%s tree_nodes=%zu reexpand_sink_layer=%zu crossings=%zu edges=%s\n",
        s.iteration,s.attempts,size_t(net),pin,size_t(sink),int(high_fanout),int(guide!=nullptr),double(criticality),
        influence_preferences(guide).c_str(),nodes,expanded_on_sink_layer,crossings,crossings?edges.str().c_str():"-");
}

void h3d_influence_edge(ParentNetId net,int pin,RRNodeId from,RRNodeId to,int sw,
                       bool configurable,float criticality,float before,float after,
                       float physical_delay,float timing_penalty,bool rcv,
                       const t_h3d_connection_guide& guide,bool bounded_applied,float unbounded_congestion) {
    VTR_ASSERT(influence);auto& s=*influence;
    VTR_ASSERT(s.current_net==size_t(net) && s.current_pin==pin);
    const bool preferred=std::binary_search(guide.preferred.begin(),guide.preferred.end(),from);
    const int bin=influence_bin(criticality),focus=influence_focus(size_t(net),pin);
    const size_t group=focus<0 ? 3+bin : focus,cap=focus<0 ? 1000 : 2000;
    auto& b=s.buckets[bin*4+int(configurable)*2+int(preferred)];++b.count;++s.events;
    const double extra=(1.-double(criticality))*(double(after)-double(before));
    const double physical=double(criticality)*double(physical_delay);
    const double timing=!rcv ? double(criticality)*double(timing_penalty) : 0.;
    const bool finite=std::isfinite(extra) && std::isfinite(physical) && std::isfinite(timing);
    if(finite) {
        ++b.finite;b.positive+=extra>0.;b.below_unit+=extra>0. && extra<s.unit;
        b.extra+=extra;b.physical+=physical;b.timing+=timing;b.maximum_extra=std::max(b.maximum_extra,extra);
    }
    if(bounded_applied) {
        ++s.bounded_applications;
        s.bounded_old_extra+=(1.-double(criticality))*(double(unbounded_congestion)-double(before));
        s.bounded_timing+=timing;
    }
    if(s.group_rows[group]>=cap)return;
    ++s.group_rows[group];++s.rows;++b.rows;
    VTR_LOG("H3D_GUIDE_INFLUENCE_EDGE iter=%d event=%zu attempt=%zu net=%zu pin=%d from=%zu to=%zu switch=%d group=%zu group_row=%zu bin=%d configurable=%d preferred=%d rcv=%d criticality=%.17g miss_weight=%.17g preferred_ids=%s before_congestion=%.17g after_congestion=%.17g physical_seconds=%.17g timing_penalty_seconds=%.17g analytic_extra=%.17g weighted_physical_seconds=%.17g weighted_timing_seconds=%.17g finite=%d\n",
        s.iteration,s.events,s.attempts,size_t(net),pin,size_t(from),size_t(to),sw,group,s.group_rows[group],bin,int(configurable),int(preferred),int(rcv),double(criticality),double(guide.miss_weight),
        influence_preferences(&guide).c_str(),double(before),double(after),double(physical_delay),double(timing_penalty),extra,physical,timing,int(finite));
    if(bounded_applied) {
        ++s.bounded_rows;
        VTR_LOG("H3D_BOUNDED_CRITICAL_APPLY iter=%d event=%zu attempt=%zu net=%zu pin=%d from=%zu to=%zu criticality=%.17g before_congestion=%.17g old_congestion=%.17g new_congestion=%.17g reliability=%.17g unit_seconds=%.17g beta=%.17g penalty_seconds=%.17g weighted_timing_seconds=%.17g\n",
            s.iteration,s.events,s.attempts,size_t(net),pin,size_t(from),size_t(to),double(criticality),double(before),double(unbounded_congestion),double(after),
            guide.bounded_reliability,guide.bounded_unit_seconds,guide.bounded_beta,double(guide.bounded_penalty_seconds),timing);
    }
}

bool h3d_enabled() { return settings().mode != e_h3d_mode::OFF; }

bool h3d_force_whole_net() { return settings().mode == e_h3d_mode::DYNAMIC_WHOLE; }

bool h3d_force_subtree() { return settings().mode == e_h3d_mode::DYNAMIC_SUBTREE; }

bool h3d_transactional() { return settings().feedback || h3d_force_whole_net() || h3d_force_subtree(); }

void h3d_observe_net(ParentNetId net) {
    if (planner) planner->observe(net);
}

void h3d_record_rollback() {
    VTR_ASSERT(planner);
    planner->rollback();
}

bool h3d_test_rollback_once() {
    static const bool enabled = std::getenv("VPR_H3D_TEST_ROLLBACK_ONCE") != nullptr;
    static bool used = false;
    if (enabled && !used) {
        used = true;
        VTR_LOG("H3D_TEST rejecting one completed replacement to exercise full rollback\n");
        return true;
    }
    return false;
}

void h3d_prepare_iteration(int iteration, bool is_flat) {
    if (!h3d_enabled()) return;
    if (iteration == 1) {
        bounded_legal_phase=false;
        influence.reset();
        if(settings().trace_guide_influence) {
            influence=std::make_unique<InfluenceState>();
            influence->bounded_mode=std::getenv("VPR_H3D_BOUNDED_CRITICAL_GUIDE")!=nullptr;
            double total=0.;size_t positive=0;
            for(const auto& sw:g_vpr_ctx.device().rr_graph.rr_switch())
                if(sw.Tdel>0.f) {total+=sw.Tdel;++positive;}
            if(positive)influence->unit=total/positive;
        }
        const auto& device = g_vpr_ctx.device();
        if (is_flat || device.grid.get_num_layers() != 2 || device.grid.has_interposer_cuts() || !device.rr_bus_muxes.empty())
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes currently require clustered routing, two stacked layers, no interposer cuts and no bus-mux sharing");
        planner = std::make_unique<H3dPlanner>();
    }
    if(influence)influence->iteration=iteration;
}

void h3d_capture_net(ParentNetId net) {
    if (!h3d_enabled()) return;
    if (!planner)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D candidate modes require the serial netlist router");
    planner->capture(net);
}

void h3d_prepare_net(ParentNetId net, int iteration, float pres_fac, const std::vector<float>& criticality, const std::vector<size_t>& remaining_targets) {
    if (h3d_enabled()) planner->plan(net, iteration, pres_fac, criticality, remaining_targets);
}

const t_h3d_connection_guide* h3d_connection_guide(ParentNetId net, int pin) {
    return h3d_enabled() ? planner->guide(net, pin) : nullptr;
}

void h3d_record_fallback() {
    if (planner) planner->fallback();
}

float h3d_vertical_weight() {
    static const float value = [] {
        const char* text = std::getenv("VPR_H3D_VERTICAL_WEIGHT");
        if (!text)
            return 0.f;
        errno = 0;
        char* end = nullptr;
        float parsed = std::strtof(text, &end);
        if (errno || end == text || *end || !std::isfinite(parsed) || parsed < 0.f) {
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_VERTICAL_WEIGHT must be finite and nonnegative, got '%s'", text);
        }
        VTR_LOG("H3D vertical_weight=%g (additional congestion preference; native timing unchanged)\n", parsed);
        return parsed;
    }();
    return value;
}

void h3d_log_iteration(int iteration, float pres_fac, const RouterStats& stats) {
    static const bool enabled = std::getenv("VPR_H3D_STATS") != nullptr;
    if (!enabled && !h3d_enabled())
        return;
    const auto& graph = g_vpr_ctx.device().rr_graph;
    const auto& routing = g_vpr_ctx.routing();
    size_t vertical_used = 0;
    size_t vertical_occupancy = 0;
    size_t vertical_overused = 0;
    size_t vertical_total_overuse = 0;
    for (RRNodeId inode : graph.nodes()) {
        if (graph.node_type(inode) != e_rr_type::CHANZ)
            continue;
        int occ = routing.rr_node_route_inf[inode].occ();
        int capacity = graph.node_capacity(inode);
        vertical_used += occ > 0;
        vertical_occupancy += occ;
        vertical_overused += occ > capacity;
        vertical_total_overuse += std::max(0, occ - capacity);
    }
    VTR_LOG("H3D_ITER iter=%d pres=%g z_used=%zu z_net_occupancy=%zu z_overused=%zu z_excess=%zu nets_routed=%zu connections_routed=%zu heap_pushes=%zu heap_pops=%zu\n",
            iteration, pres_fac, vertical_used, vertical_occupancy, vertical_overused, vertical_total_overuse,
            stats.nets_routed, stats.connections_routed, stats.heap_pushes, stats.heap_pops);
    if (planner) planner->log();
    log_influence();
    if (settings().edge_encoding) {
        std::unordered_map<RRNodeId, int> crossing_occupancy;
        for (const auto& tree : routing.route_trees) {
            if (!tree) continue;
            std::set<RRNodeId> used;
            for (const auto& node : tree->all_nodes()) {
                auto parent = node.parent();
                if (parent && h3d_crosses_layers(graph, parent->inode, node.inode)) used.insert(parent->inode);
            }
            for (auto node : used) ++crossing_occupancy[node];
        }
        size_t occupancy = 0, excess = 0;
        for (auto [node, count] : crossing_occupancy) {
            occupancy += count;
            excess += std::max(0, count - graph.node_capacity(node));
        }
        VTR_LOG("H3D_EDGE_ITER iter=%d crossing_sources_used=%zu crossing_source_net_occupancy=%zu crossing_source_excess=%zu\n",
                iteration, crossing_occupancy.size(), occupancy, excess);
    }
}

void h3d_save_best_guides() { if (planner) planner->save_best(); }
void h3d_enter_legal_refinement(int iteration) { if (planner) planner->enter_legal_refinement(iteration); }
void h3d_report_final_guides(bool success) { if (planner) planner->final_trace(success); }
