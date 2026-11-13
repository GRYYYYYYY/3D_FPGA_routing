from pathlib import Path
b=Path(__file__).resolve().parent/'src/vpr/src/route'
p=b/'h3d_routing.cpp';s=p.read_text().replace('#include <unordered_map>','#include <unordered_map>\n#include <fstream>')
s=s.replace('#include "h3d_fast_plan.h"','#include "h3d_fast_plan.h"\n#include "h3d_feedback_policy.h"')
s=s.replace('    bool edge_encoding = false;', '''    bool feedback = false;            ///< Selective refresh of guides on VPR-selected reroute nets.
    int cooldown = 3;                  ///< Minimum iterations between refresh attempts.
    double refresh_margin = .05;       ///< Required relative surrogate improvement.
    bool final_trace = false;          ///< Emit one final per-connection guide/path table.
    bool edge_encoding = false;''',1)
s=s.replace('        return result;\n    }();','''        float feedback = read_number("VPR_H3D_FEEDBACK", 0.f);
        if (feedback != 0.f && feedback != 1.f)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_FEEDBACK must be 0 or 1");
        result.feedback = feedback == 1.f;
        result.final_trace = std::getenv("VPR_H3D_FINAL_TRACE") != nullptr;
        if (result.feedback && (!result.use_scc || result.mode != e_h3d_mode::STATIC))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Selective feedback requires static SCC planning");
        return result;
    }();''',1)
s=s.replace('    void capture(ParentNetId net) {\n        current_channels_.clear();','''    void capture(ParentNetId net) {
        captured_net_ = net;
        captured_actual_.clear();
        captured_overuse_ = false;
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
        }
        current_channels_.clear();''')
s=s.replace('    void plan(ParentNetId net, float pres_fac, const std::vector<float>& criticality) {\n        if (settings().mode == e_h3d_mode::STATIC && guides_.contains(net))\n            return;','''    void plan(ParentNetId net, int iteration, float pres_fac, const std::vector<float>& criticality) {
        bool refresh = settings().mode == e_h3d_mode::STATIC && guides_.contains(net);
        if (refresh && !settings().feedback) return;
        auto start = std::chrono::steady_clock::now();
        if (refresh) {
            ++refresh_checks_;
            auto& state = feedback_state_.at(net);
            const auto& graph = g_vpr_ctx.device().rr_graph;
            const auto& terminals = g_vpr_ctx.routing().net_rr_terminals[net];
            double drift = 0.;
            for (size_t pin = 1; pin < criticality.size(); ++pin)
                if (graph.node_layer_low(terminals[0]) != graph.node_layer_low(terminals[pin])
                    && std::max(criticality[pin], state.criticality[pin]) >= settings().min_criticality)
                    drift = std::max(drift, double(std::abs(criticality[pin] - state.criticality[pin])));
            size_t difference = 0;
            for (RRNodeId node : captured_actual_) difference += !state.actual.contains(node);
            for (RRNodeId node : state.actual) difference += !captured_actual_.contains(node);
            size_t union_size = (difference + captured_actual_.size() + state.actual.size()) / 2;
            double change = state.observed && union_size ? double(difference) / union_size : 0.;
            if (!h3d_feedback_due(iteration, state.last_attempt, settings().cooldown, captured_overuse_, drift, change)) {
                ++refresh_skips_;
                refresh_check_seconds_ += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
                return;
            }
            state.last_attempt = iteration;
            ++refresh_attempts_;
            refresh_overuse_ += captured_overuse_;
            refresh_drift_ += drift >= .15;
            refresh_path_ += change >= .25;
        }''')
s=s.replace('        auto start = std::chrono::steady_clock::now();\n        if (fast_plan_) {','        if (fast_plan_) {',1)
s=s.replace('settings().mode != e_h3d_mode::CANDIDATES, settings().min_criticality);','''settings().mode != e_h3d_mode::CANDIDATES, settings().min_criticality,
                                           refresh ? &guides_.at(net) : nullptr, settings().refresh_margin);''',1)
s=s.replace('            guides_[net] = std::move(result.guides);','''            bool accept = !refresh || result.refresh_accepted;
            if (refresh) {
                refresh_accepts_ += accept;
                VTR_LOG("H3D_REFRESH net=%zu iter=%d accepted=%d old_cost=%g new_cost=%g\\n",
                        size_t(net), iteration, accept, result.previous_cost, result.proposed_cost);
            }
            if (accept) {
                guides_[net] = std::move(result.guides);
                if (settings().feedback || settings().final_trace)
                    feedback_state_[net] = {iteration, criticality, captured_actual_, false};
            }''',1)
s=s.replace('        if (fast_plan_) fast_plan_->log();','''        VTR_LOG("H3D_FEEDBACK checks=%zu skipped=%zu attempts=%zu accepted=%zu overuse=%zu criticality=%zu path=%zu check_seconds=%.6f\\n",
                refresh_checks_, refresh_skips_, refresh_attempts_, refresh_accepts_, refresh_overuse_, refresh_drift_, refresh_path_, refresh_check_seconds_);
        if (fast_plan_) fast_plan_->log();''',1)
s=s.replace('        if (found == guides_.end() || !tree) return;','''        if (found == guides_.end() || !tree) return;
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
        }''',1)
s=s.replace('    void rollback() { ++rollbacks_; }','''    void rollback() {
        ++rollbacks_;
        if (settings().feedback) {
            if (backup_had_guide_) guides_[captured_net_] = backup_guides_;
            else guides_.erase(captured_net_);
            if (backup_had_state_) feedback_state_[captured_net_] = backup_state_;
            else feedback_state_.erase(captured_net_);
            ++guide_rollbacks_;
            VTR_LOG("H3D_GUIDE_ROLLBACK net=%zu restored=1\\n", size_t(captured_net_));
        }
    }

    /** @brief Preserve the guide version corresponding to VPR's best complete routing. */
    void save_best() {
        if (!settings().final_trace) return;
        best_guides_ = guides_;
        best_feedback_state_ = feedback_state_;
    }

    /** @brief Observe restored final route trees once, without affecting routing or STA. */
    void final_trace(bool success) const {
        if (!settings().final_trace) return;
        const auto& chosen = success ? best_guides_ : guides_;
        const auto& states = success ? best_feedback_state_ : feedback_state_;
        const auto& graph = g_vpr_ctx.device().rr_graph;
        const auto& routing = g_vpr_ctx.routing();
        std::ofstream out("h3d_final_guides.csv");
        if (!out) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot create final guide trace");
        out << "net,pin,source,sink,planned_criticality,preferred,actual_crossings,routed,adopted,timing_penalty_seconds\\n";
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
                out << ',' << reached << ',' << match << ',' << guide.timing_miss_penalty << '\\n';
            }
        }
        VTR_LOG("H3D_FINAL success=%d guided=%zu routed=%zu adopted=%zu guide_rollbacks=%zu\\n", success, guided, routed, adopted, guide_rollbacks_);
    }''')
s=s.replace('    std::vector<RRNodeId> channels_;', '''    /** @brief Guide generation state; replaced only after an accepted refresh. */
    struct t_feedback_state {
        int last_attempt = 1;                    ///< Cooldown timestamp.
        std::vector<float> criticality;           ///< Timing weights used by this guide.
        std::set<RRNodeId> actual;                ///< Actual crossings after its first successful route.
        bool observed = false;                   ///< Whether actual crossings have been initialized.
    };
    std::unordered_map<ParentNetId, t_feedback_state> feedback_state_, best_feedback_state_; ///< Per-net and best-route state.
    std::unordered_map<ParentNetId, std::vector<t_h3d_connection_guide>> best_guides_; ///< Best-route diagnostic guide versions.
    ParentNetId captured_net_;                    ///< Current serial routing transaction.
    bool backup_had_guide_ = false, backup_had_state_ = false; ///< Exact restoration membership.
    std::vector<t_h3d_connection_guide> backup_guides_; ///< Transaction snapshot.
    t_feedback_state backup_state_;              ///< Transaction feedback snapshot.
    std::set<RRNodeId> captured_actual_;          ///< Pre-prune actual crossing resources.
    bool captured_overuse_ = false;               ///< Recommended crossing currently overloaded.
    size_t refresh_checks_ = 0, refresh_skips_ = 0, refresh_attempts_ = 0, refresh_accepts_ = 0; ///< Refresh work accounting.
    size_t refresh_overuse_ = 0, refresh_drift_ = 0, refresh_path_ = 0, guide_rollbacks_ = 0; ///< Trigger and restoration counts.
    double refresh_check_seconds_ = 0.;           ///< Includes gate work on skipped reroutes.
    std::vector<RRNodeId> channels_;''',1)
s=s.replace('return h3d_force_whole_net() || h3d_force_subtree();','return settings().feedback || h3d_force_whole_net() || h3d_force_subtree();',1)
s=s.replace('void h3d_prepare_net(ParentNetId net, int /*iteration*/,','void h3d_prepare_net(ParentNetId net, int iteration,').replace('planner->plan(net, pres_fac, criticality);','planner->plan(net, iteration, pres_fac, criticality);')
s += '''\nvoid h3d_save_best_guides() { if (planner) planner->save_best(); }\nvoid h3d_report_final_guides(bool success) { if (planner) planner->final_trace(success); }\n'''
p.write_text(s)
p=b/'h3d_routing.h';s=p.read_text();s+='''\n/** @brief Bind guide state to VPR's selected best routing for final observation. */
void h3d_save_best_guides();
/** @brief Write optional per-connection trace against restored final route trees. */
void h3d_report_final_guides(bool success);
''';p.write_text(s)
p=b/'route.cpp';s=p.read_text().replace('#include "route.h"','#include "route.h"\n#include "h3d_routing.h"')
s=s.replace('                best_routing = router_ctx.route_trees;','                best_routing = router_ctx.route_trees;\n                h3d_save_best_guides();',1)
s=s.replace('    if (router_opts.with_timing_analysis) {\n        VTR_LOG("Final Net Connection Criticality Histogram:', '    h3d_report_final_guides(success);\n\n    if (router_opts.with_timing_analysis) {\n        VTR_LOG("Final Net Connection Criticality Histogram:',1);p.write_text(s)
