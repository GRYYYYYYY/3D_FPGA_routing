#!/usr/bin/env python3
import difflib,shutil
from retained_prefix_workflow import D,read,write,sha
R=D/'src/vpr/src/route';out=D/'outside_native_implementation_01';out.mkdir(exist_ok=False);parent=read(D/'retained_outside_trace_stage_01/binding.json');assert all(sha(D/'src'/p)==h for p,h in parent['source_sha256'].items());assert read(D/'outside_dp_core_01/unit_validation.json')['passed'] and read(D/'outside_dp_table_replay_01/analysis.json')['passed']
names=['h3d_partition_dp.h','h3d_independent_plan.h','h3d_routing.h','h3d_routing.cpp','h3d_fast_plan.h','h3d_fast_plan.cpp'];before={n:(R/n).read_text() for n in names}
for n,s in before.items():(out/n).write_text(s)
write(D/'outside_native_experiment_01.json',dict(status='registered_before_implementation',parent='retained_outside_experiment_01.json',question='Does a current-tree-valid bounded-benefit no-new-cross DP option improve actual final routing, across both native stopping rules, with intentional-empty metadata and transaction restoration?',input='same eltwise HybridO P0 W100 seed11 exact paired packed/place/RRG',arms=['C2:eta absent new binary default must exact frozen Qs','Z2:eta0 full plumbing exact C2 including original decisions/query work','N2:eta.25,count2','N1:eta.25,count1 exact same-beta firstlegal prefix N2'],method='Validated optional outside-cost DP core, only at existing finite target refresh; cached valid suffix, currentTdel/current prices and BB/current-tree exclusion; cost max(raw,.75*best physical standalone); physical original candidate probe first then extended solve. No query budget increase. Deliberate empty-guide kind persists in full vector snapshots and is excluded from native soft-preference API.',feedback='At already VPR-selected remaining targets, validate intentional outside anchor/BB/tree exclusions and observe recommended ordinary suffix overuse. Invalid or overused witness may trigger existing cooldown; valid deliberate empty alone is not missing. Criticality/path/native mechanisms retained.',unsupported='During pilot forbid sensitivity/margin/tie-pressure/old timing/bounded/mixed/candidate physical-price scoring modes; independent DP remains supported for later same-table ablation.',validation='Default and eta0 exact gates; fresh extended table/current-prior/acceptance replay, current graph/tree/price and chosen witness checks, actual metadata non-target/best digests. Then forced rollback new and retained outside state when actual opportunities exist, no false coverage claim. Single process1800s64GiB80GiBdisk, all statuses retained.',formal_speedup=False,quality_promoted=False))
for n in ['h3d_partition_dp.h','h3d_independent_plan.h']:shutil.copy2(D/'outside_dp_core_01/src'/n,R/n)
s=before['h3d_routing.h'];a='    std::vector<RRNodeId> preferred;';assert a in s;s=s.replace(a,'    bool retained_outside=false; ///< Intentional no-preference plan, distinct from missing guide.\n    std::vector<RRNodeId> retained_suffix; ///< Current-tree anchor -> target static witness.\n'+a,1);s=s.replace('bool h3d_trace_guide_influence();','double h3d_outside_eta();\nbool h3d_trace_guide_influence();',1);(R/'h3d_routing.h').write_text(s)
s=before['h3d_routing.cpp'];s=s.replace('    int residual_query_mode=-1;','    double outside_eta=-1.;\n    int residual_query_mode=-1;',1)
a='        if(const char* text=std::getenv("VPR_H3D_BOX_GUIDE_ADMISSION"))';x='''        if(std::getenv("VPR_H3D_OUTSIDE_ETA")) {
            result.outside_eta=read_number("VPR_H3D_OUTSIDE_ETA",0.f);
            const char* trace=std::getenv("VPR_H3D_TRACE_OUTSIDE");
            if(result.outside_eta>1. || result.residual_query_mode!=2 || !trace || std::string(trace)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Outside eta must be in[0,1] with reuse mode and outside trace1");
        }
''';assert a in s;s=s.replace(a,x+a,1)
a='/** @brief Persistent exact reachability caches';i=s.index(a)
x='''uint64_t outside_digest(const std::vector<t_h3d_connection_guide>& guides) {
    uint64_t h=14695981039346656037ull;
    auto mix=[&](size_t v){for(int i=0;i<8;++i){h^=v&255;h*=1099511628211ull;v>>=8;}};
    mix(guides.size());
    for(const auto& g:guides){mix(g.retained_outside);mix(g.retained_suffix.size());for(auto n:g.retained_suffix)mix(size_t(n));}
    return h;
}
// Static witnesses never force a branch. Revalidate only a native-selected target.
bool outside_valid(ParentNetId net,size_t pin,const t_h3d_connection_guide& guide,bool& overused) {
    const auto& route=g_vpr_ctx.routing();const auto& graph=g_vpr_ctx.device().rr_graph;
    if(!guide.retained_outside || guide.retained_suffix.empty() || !route.route_trees[net])return false;
    const auto& path=guide.retained_suffix;if(path.back()!=route.net_rr_terminals[net][pin])return false;
    std::set<RRNodeId> owned,seen;bool anchor=false;
    for(const auto& n:route.route_trees[net]->all_nodes()){owned.insert(n.inode);if(n.inode==path.front())anchor=n.re_expand;}
    if(!anchor)return false;
    const auto& bb=route.route_bb[net];const int layer=graph.node_layer_low(path.back());
    for(size_t i=0;i<path.size();++i) {
        const auto n=path[i];if(!seen.insert(n).second || graph.node_layer_low(n)!=layer || !inside_bb(graph,n,bb) || (i && owned.contains(n)))return false;
        if(i && (graph.node_type(n)==e_rr_type::CHANX || graph.node_type(n)==e_rr_type::CHANY) && graph.node_direction(n)!=Direction::NONE)
            overused=overused || route.rr_node_route_inf[n].occ()+1>graph.node_capacity(n);
    }
    return true;
}

''';s=s[:i]+x+s[i:]
a='            bool due = base_due || (settings().planar_feedback && planar_due);';x=a+'''
            if(settings().outside_eta>=0.) {
                size_t invalid=0,overused=0,checked=0;
                for(size_t pin:remaining_targets) {
                    const auto& guide=guides_.at(net).at(pin);
                    if(!guide.retained_outside || criticality.at(pin)<settings().min_criticality)continue;
                    bool price=false;const bool valid=outside_valid(net,pin,guide,price);++checked;invalid+=!valid;overused+=valid && price;
                }
                const bool extra=h3d_feedback_due(iteration,state.last_attempt,settings().cooldown,overused>0,0.,0.,invalid>0);
                if(checked)VTR_LOG("H3D_OUTSIDE_FEEDBACK net=%zu iter=%d last_attempt=%d cooldown=%d targets=%zu checked=%zu invalid=%zu overused=%zu original_due=%d extra_due=%d\\n",size_t(net),iteration,state.last_attempt,settings().cooldown,remaining_targets.size(),checked,invalid,overused,int(due),int(extra));
                due=due || extra;
            }
''';assert a in s;s=s.replace(a,x,1)
# Only eligibility missing predicates are changed; physical guided/adoption counts remain physical-only.
s=s.replace('&& guides_.at(net).at(pin).preferred.empty();','&& guides_.at(net).at(pin).preferred.empty() && !guides_.at(net).at(pin).retained_outside;')
s=s.replace('&& before.bounded_penalty_seconds == after.bounded_penalty_seconds);','&& before.bounded_penalty_seconds == after.bounded_penalty_seconds\n                                   && before.retained_outside == after.retained_outside\n                                   && before.retained_suffix == after.retained_suffix);',1)
a='    void rollback() {';x='''    bool outside_test_rollback(bool retained) const {
        const auto current=guides_.find(captured_net_);if(current==guides_.end() || !backup_had_guide_)return false;
        const auto has=[](const auto& v){return std::any_of(v.begin(),v.end(),[](const auto& g){return g.retained_outside;});};
        const bool before=has(backup_guides_),after=has(current->second);
        if((retained ? before : !before && after) && outside_digest(backup_guides_)!=outside_digest(current->second)) {
            VTR_LOG("H3D_OUTSIDE_TEST_REJECT net=%zu prior_outside=%d current_outside=%d before=%llu current=%llu\\n",size_t(captured_net_),int(before),int(after),(unsigned long long)outside_digest(backup_guides_),(unsigned long long)outside_digest(current->second));return true;
        }
        return false;
    }
'''+a;assert a in s;s=s.replace(a,x,1)
a='            VTR_LOG("H3D_GUIDE_ROLLBACK net=%zu restored=1\\n", size_t(captured_net_));';x=a+'''
            if(settings().outside_eta>=0. && backup_had_guide_) {
                VTR_ASSERT(outside_digest(guides_.at(captured_net_))==outside_digest(backup_guides_));
                VTR_LOG("H3D_OUTSIDE_ROLLBACK net=%zu expected=%llu restored=%llu\\n",size_t(captured_net_),(unsigned long long)outside_digest(backup_guides_),(unsigned long long)outside_digest(guides_.at(captured_net_)));
            }
''';assert a in s;s=s.replace(a,x,1)
a='        best_guides_ = guides_;';x=a+'''
        if(settings().outside_eta>=0.)for(const auto& [net,guides]:best_guides_)
            VTR_LOG("H3D_OUTSIDE_SAVE net=%zu digest=%llu\\n",size_t(net),(unsigned long long)outside_digest(guides));
''';assert a in s;s=s.replace(a,x,1)
a='            const auto& guides = chosen.at(net);';x=a+'''
            if(settings().outside_eta>=0.)VTR_LOG("H3D_FINAL_OUTSIDE_STATE net=%zu digest=%llu\\n",size_t(net),(unsigned long long)outside_digest(guides));
''';assert a in s;s=s.replace(a,x,1)
a='                if (guide.preferred.empty()) continue;';pos=s.index(a,s.index('    void final_trace('));x='''                if(guide.retained_outside) {
                    std::ostringstream suffix;for(auto n:guide.retained_suffix){if(suffix.tellp()>0)suffix<<',';suffix<<size_t(n);}
                    VTR_LOG("H3D_FINAL_OUTSIDE net=%zu pin=%zu path=%s\\n",size_t(net),pin,suffix.str().c_str());
                }
'''+a;s=s[:pos]+s[pos:].replace(a,x,1)
a='bool h3d_trace_guide_influence()';assert a in s;s=s.replace(a,'double h3d_outside_eta() {return settings().outside_eta;}\n'+a,1)
a='bool h3d_test_rollback_once() {';x=a+'''
    static bool outside_used=false;
    if(const char* mode=std::getenv("VPR_H3D_TEST_OUTSIDE_ROLLBACK")) {
        const std::string value=mode;
        if(value!="new" && value!="retained")VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Outside rollback test must be new/retained");
        if(!outside_used && planner && planner->outside_test_rollback(value=="retained")) {outside_used=true;return true;}
    }
''';assert a in s;s=s.replace(a,x,1);(R/'h3d_routing.cpp').write_text(s)
s=before['h3d_fast_plan.h'];s=s.replace('    bool trace_outside_=false;','    double outside_eta_=-1.;\n    bool trace_outside_=false;',1);(R/'h3d_fast_plan.h').write_text(s)
s=before['h3d_fast_plan.cpp'];a='    VTR_LOG("H3D_EXPERIMENT mixed_delay=';i=s.index(a);x='''    outside_eta_=h3d_outside_eta();
    if(outside_eta_>=0. && (!trace_outside_ || trace_dp_sensitivity_ || dp_tie_pressure_ || dp_margin_pressure_ || trace_guide_margin_
        || timing_guide_weight_>0. || timing_regret_ || bounded_critical_guide_ || mixed_delay_ || targeted_delay_
        || candidate_path_score_weight_>0. || candidate_path_delay_weight_>0. || source_empty_reverse_ || source_coverage_skip_))
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Outside pilot requires isolated shared/independent legacy costs without incompatible timing/sensitivity/extra scoring");
''';s=s[:i]+x+s[i:]
a='        if(trace_outside_ && delay_plan_ && delay_plan_->supported()) {';x='''        struct OutsideChoice {double raw=std::numeric_limits<double>::infinity();std::vector<RRNodeId> path;};
        std::unordered_map<int,OutsideChoice> outside_choices;
        size_t outside_event=0;
'''+a;assert a in s;s=s.replace(a,x,1).replace('            const size_t event=++outside_plan_;','            const size_t event=++outside_plan_;outside_event=event;',1)
a='                    VTR_LOG("H3D_OUTSIDE_WITNESS';i=s.index(a);x='''                    if(outside_eta_>=0. && prior_guides && std::string(reason)=="valid" && raw<outside_choices[leaf.pin].raw) {
                        auto& choice=outside_choices[leaf.pin];choice.raw=raw;choice.path={path.anchor};
                        for(auto it=path.reverse_edges.rbegin();it!=path.reverse_edges.rend();++it)choice.path.push_back(RRNodeId(it->from));
                    }
''';s=s[:i]+x+s[i:]
a='        if (prior_guides) {\n            refresh_independent_calls_';x='''        if(outside_eta_>=0. && prior_guides) {
            for(auto& leaf:leaves) {
                double standalone=std::numeric_limits<double>::infinity();
                for(const auto& c:leaf.candidates)standalone=std::min(standalone,openings[c.channel]+c.branch_cost);
                auto found=outside_choices.find(leaf.pin);
                if(found!=outside_choices.end())leaf.outside_cost=std::max(found->second.raw,(1.-outside_eta_)*standalone);
                VTR_LOG("H3D_OUTSIDE_COST event=%zu net=%zu pin=%d eta=%.17g standalone=%.17g raw=%.17g outside=%.17g\\n",outside_event,size_t(net),leaf.pin,outside_eta_,standalone,found==outside_choices.end()?std::numeric_limits<double>::infinity():found->second.raw,leaf.outside_cost);
            }
            planned=independent ? h3d_plan_independent(leaves,openings) : h3d_plan_partition(leaves,openings);
            VTR_LOG("H3D_OUTSIDE_SOLVER event=%zu net=%zu independent=%d cost=%.17g groups=%zu outside=%zu\\n",outside_event,size_t(net),int(independent),planned.cost,planned.groups,planned.outside_leaves);
        }
'''+a;assert a in s;s=s.replace(a,x,1)
a='                if (guide.preferred.size() != 1) continue;';x='''                if(guide.retained_outside) {prior_assignment.emplace_back(leaf.pin,openings.size());continue;}
'''+a;assert a in s;s=s.replace(a,x,1)
a='                    if (guide.preferred.empty()) { result.prior_empty_pins.push_back(leaf.pin); continue; }';x='''                    if(guide.retained_outside) {
                        if(!std::isfinite(leaf.outside_cost))++result.prior_branch_nonfinite;
                        continue;
                    }
'''+a;assert a in s;s=s.replace(a,x,1)
a='            for (const auto& [pin, c] : planned.assignment)\n                result.guides[pin].preferred = {channels_[table[c]]};';x='''            for (const auto& [pin, c] : planned.assignment) {
                auto& guide=result.guides[pin];
                if(c==openings.size()) {
                    VTR_ASSERT(outside_eta_>=0. && outside_choices.contains(pin));
                    guide=t_h3d_connection_guide{};guide.edge_encoding=edge_encoding_;guide.retained_outside=true;guide.retained_suffix=outside_choices.at(pin).path;
                } else {guide.preferred={channels_[table[c]]};guide.retained_outside=false;guide.retained_suffix.clear();}
                if(outside_eta_>=0.) {
                    std::ostringstream path;for(auto node:guide.retained_suffix){if(path.tellp()>0)path<<',';path<<size_t(node);}
                    VTR_LOG("H3D_OUTSIDE_ASSIGN event=%zu net=%zu pin=%d kind=%s resource=%lld path=%s\\n",outside_event,size_t(net),pin,guide.retained_outside?"outside":"physical",guide.retained_outside?-1ll:(long long)size_t(guide.preferred.front()),guide.retained_outside?path.str().c_str():"-");
                }
            }''';assert a in s;s=s.replace(a,x,1);(R/'h3d_fast_plan.cpp').write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},script_sha256=sha(__file__),protocol_sha256=sha(D/'outside_native_experiment_01.json'),core_unit_sha256=sha(D/'outside_dp_core_01/unit_validation.json'),qualification='Native outside DP/intentional-empty metadata and selected-target validity/price feedback, disabled by default. Research trace scans complete cached pool for independent auditing; production lookup filtering can be optimized after quality evidence.'))
(out/'implementation.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names))
