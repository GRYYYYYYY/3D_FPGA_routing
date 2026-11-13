#!/usr/bin/env python3
import difflib
from retained_prefix_workflow import D,read,write,sha
R=D/'src/vpr/src/route';out=D/'retained_outside_trace_implementation_01';out.mkdir(exist_ok=False)
binding=read(D/'residual_native_stage_03/binding.json');assert all(sha(D/'src'/p)==h for p,h in binding['source_sha256'].items());names=['h3d_delay_plan.h','h3d_fast_plan.h','h3d_fast_plan.cpp'];before={n:(R/n).read_text() for n in names}
for n,s in before.items():(out/n).write_text(s)
write(D/'retained_outside_trace_experiment_01.json',dict(status='registered_before_implementation',parent='retained_outside_experiment_01.json',question='At actual selected-net finite DP tables, which chronological physical residual suffixes still legally extend the current pruned tree, and what are their current physical-plus-price surrogate costs?',input='same eltwise HybridO P0 W100 seed11 frozen packed/place/RRG,count2',arms=['C:outside trace0 exact frozen Qs','D:outside trace1 exact C including residual query decisions/work/cache'],trace='Every finite table gets plan/net/tree/leaf context and cache counts. If cached witnesses exist, complete current tree parent/switch/re_expand/Tdel records and all cached witness reverse edges with current occ/cap/acc/ordinary snapshots are emitted. No new query, cache insert or scoring decision. Tree context cap32768nodes per table and cumulative2000000tree+path rows: guarded skip is explicit unknown, not invalidity.',validation='Independent actual RRG physical/tree-edge/switch delay and f32 prefix check; anchor membership/re_expand/sink-layer/BB, simple path and no intersection after anchor; all exclusion reasons, current price and physical surrogate reconstructed. C/D complete native route/guide/cost/query/heap/prefix/native numeric rows and residual non-time decisions/counters exact.',limits=dict(seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),claim='Read-only feasibility/current-cost diagnosis before the registered outside-DP quality pilot. Native congestion, Tdel/STA, guide, transactions and legacy query caches unchanged.'))
s=before['h3d_delay_plan.h'];a='    void log() const;';x='''    struct RetainedSuffix { RRNodeId anchor;size_t origin;std::vector<H3dCandidatePath::Edge> reverse_edges; };
    std::vector<RetainedSuffix> retained_suffixes(RRNodeId sink) const {
        std::vector<RetainedSuffix> result;
        auto found=residual_cache_.lower_bound({sink,RRNodeId(0)});
        for(;found!=residual_cache_.end() && found->first.first==sink;++found)
            for(const auto& v:found->second)result.push_back({found->first.second,v.origin,v.reverse_edges});
        return result;
    }
''';assert a in s;s=s.replace(a,x+a,1);(R/'h3d_delay_plan.h').write_text(s)
s=before['h3d_fast_plan.h'];a='    H3dPlanProfile profile_;';assert a in s;s=s.replace(a,'    bool trace_outside_=false;\n    size_t outside_plan_=0,outside_trace_rows_=0;\n'+a,1);(R/'h3d_fast_plan.h').write_text(s)
s=before['h3d_fast_plan.cpp'];a='    const char* profile = std::getenv("VPR_H3D_PLAN_PROFILE");';x='''    if(const char* value=std::getenv("VPR_H3D_TRACE_OUTSIDE")) {
        if(std::string(value)!="0" && std::string(value)!="1")VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_TRACE_OUTSIDE must be0/1");
        trace_outside_=std::string(value)=="1";
        const char* query=std::getenv("VPR_H3D_RESIDUAL_QUERY");
        if(trace_outside_ && (!query || std::string(query)!="reuse" || !delay_cost || !edge_encoding))VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Outside trace requires zeroRC delay planner, edge encoding and residual reuse mode");
    }
''';assert a in s;s=s.replace(a,x+a,1)
a='        // Diagnostic-only exact-cost fingerprint, before either solver.'
x='''        if(trace_outside_ && delay_plan_ && delay_plan_->supported()) {
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
            VTR_LOG("H3D_OUTSIDE_CONTEXT event=%zu net=%zu refresh=%d leaves=%zu tree_nodes=%zu witnesses=%zu edges=%zu guard=%d pres=%.17g opening=%.17g unit=%.17g xmin=%d xmax=%d ymin=%d ymax=%d layer_min=%d layer_max=%d\\n",event,size_t(net),int(prior_guides!=nullptr),leaves.size(),tree_order.size(),witnesses,edges,int(guard),double(pres_fac),double(opening_weight),delay_plan_->delay_unit(),bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.layer_min,bb.layer_max);
            if(witnesses && !guard) {
                for(size_t seq=0;seq<tree_order.size();++seq) {
                    const auto& node=*tree_order[seq];const auto parent=node.parent();
                    VTR_LOG("H3D_OUTSIDE_TREE event=%zu seq=%zu node=%zu expand=%d delay=%.17g parent=%lld switch=%lld\\n",event,seq,size_t(node.inode),int(node.re_expand),double(node.Tdel),parent?static_cast<long long>(size_t(parent->inode)):-1ll,parent?static_cast<long long>(size_t(node.parent_switch)):-1ll);
                }
                outside_trace_rows_+=tree_order.size()+edges;
            }
            for(const auto& leaf:leaves) {
                const RRNodeId sink=terminals[leaf.pin];double standalone=std::numeric_limits<double>::infinity();
                for(const auto& c:leaf.candidates)standalone=std::min(standalone,openings[c.channel]+c.branch_cost);
                VTR_LOG("H3D_OUTSIDE_LEAF event=%zu net=%zu pin=%d sink=%zu criticality=%.17g standalone=%.17g witnesses=%zu\\n",event,size_t(net),leaf.pin,size_t(sink),double(criticality[leaf.pin]),standalone,cached.at(leaf.pin).size());
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
                        VTR_LOG("H3D_OUTSIDE_EDGE event=%zu pin=%d witness=%zu index=%zu from=%zu to=%zu delay=%.17g occ=%d capacity=%d acc=%.17g ordinary=%d price=%.17g premium=%.17g\\n",event,leaf.pin,number,i,e.from,e.to,e.physical_seconds,occ,capacity,double(info.acc_cost),int(ordinary),price,toll);
                    }
                    simple=simple && previous==size_t(path.anchor) && !visited.contains(size_t(path.anchor));
                    if(std::string(reason)=="valid") {
                        if(!simple)reason="not_simple";
                        else if(!bb_ok)reason="outside_bb";
                        else if(tree_hit)reason="tree_intersection";
                    }
                    const double prefix=anchor==tree_nodes.end()?0.:anchor->second.delay;
                    const double raw=(1.+4.*double(criticality[leaf.pin]))*(prefix+physical)/delay_plan_->delay_unit()+double(opening_weight)*premium;
                    VTR_LOG("H3D_OUTSIDE_WITNESS event=%zu net=%zu pin=%d witness=%zu anchor=%zu origin=%zu edges=%zu reason=%s prefix=%.17g physical=%.17g premium=%.17g raw=%.17g\\n",event,size_t(net),leaf.pin,number++,size_t(path.anchor),path.origin,path.reverse_edges.size(),reason,prefix,physical,premium,raw);
                }
            }
        }
''';assert a in s;s=s.replace(a,x+a,1);(R/'h3d_fast_plan.cpp').write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},script_sha256=sha(__file__),protocol_sha256=sha(D/'retained_outside_trace_experiment_01.json'),qualification='Read-only static cache lookup/context/price observation, no fresh query or DP/route mutation.'))
(out/'implementation.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names))
