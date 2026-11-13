#!/usr/bin/env python3
"""Read-only trace at successful serial seed pushes and actual search entry."""
import difflib
from retained_prefix_workflow import D,read,write,sha
R=D/'src/vpr/src/route';out=D/'search_domain_implementation_01';out.mkdir(exist_ok=False)
names=['h3d_routing.cpp','h3d_routing.h','connection_router.tpp','serial_connection_router.cpp'];before={n:(R/n).read_text() for n in names}
for n,s in before.items():(out/n).write_text(s)
write(D/'search_domain_experiment_01.json',dict(status='registered_before_implementation',question='Are preferred crossing resources inside the actual search bounding box, and are partial-tree nodes on the sink layer actually pushed as sources? Read-only diagnostics distinguish full pruned-tree presence from queued search seeds.',input='eltwise_layer HybridO P0 W100 seed11 exact frozen packed/place/RRG',arms=['C:trace-domain0 exact frozen cap C control','T:trace-domain1 exact C route/guide/cost/query/heap records'],max_convergences=2,candidate='unchanged Tf baseline; bounded flag absent, path-price/physical-delay scoring0; influence trace1',native_per_process_timeout_seconds=1800,native_memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3,guards='Control must reproduce frozen C, trace-on must reproduce trace-off; no new algorithm efficacy claim. No source reverse skip.',sampling=dict(domain_rows=20000,seed_rows=6000,seed_rows_per_focus_search=100),qualification='Native successful seed pushes, including HF subset and full-tree retry separately. BB admission is native drivepoint test, not connectivity or complete route feasibility. RCV BB bypass explicitly recorded. Fixed focus IDs inherited from diagnostic only and do not affect routing decisions.'))
s=before['h3d_routing.h'];anchor='bool h3d_trace_guide_influence();';s=s.replace(anchor,anchor+'\nbool h3d_trace_search_domain();\nvoid h3d_domain_reset();\nvoid h3d_domain_seed(RRNodeId node,float delay,float backward,float total,bool rcv);\nvoid h3d_domain_search(RRNodeId sink,float criticality,const t_h3d_connection_guide* guide,const t_bb& bb,bool rcv);');(R/'h3d_routing.h').write_text(s)
s=before['h3d_routing.cpp'];s=s.replace('bool trace_guide_influence = false;', 'bool trace_search_domain = false;\n    bool trace_guide_influence = false;',1)
anchor='        if(result.trace_guide_influence && (!result.edge_encoding || result.mode==e_h3d_mode::OFF))'
insert='''        if(const char* text=std::getenv("VPR_H3D_TRACE_SEARCH_DOMAIN")) {
            if(std::string(text)!="0" && std::string(text)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_TRACE_SEARCH_DOMAIN must be 0 or 1");
            result.trace_search_domain=std::string(text)=="1";
        }
        if(result.trace_search_domain && !result.trace_guide_influence)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Search domain tracing requires influence tracing");
''';assert anchor in s;s=s.replace(anchor,insert+anchor)
s=s.replace('struct InfluenceState {','''struct DomainLayer {
    size_t pushes=0;
    double minimum_delay=std::numeric_limits<double>::infinity();
    double minimum_backward=std::numeric_limits<double>::infinity();
    double minimum_total=std::numeric_limits<double>::infinity();
};
struct InfluenceState {
    size_t domain_searches=0,domain_rows=0,domain_omitted=0,domain_seed_rows=0,domain_seed_omitted=0,domain_local_seed_rows=0;
    std::vector<DomainLayer> domain_layers;
''',1)
s=s.replace('    const auto& s=*influence;\n    VTR_LOG("H3D_GUIDE_INFLUENCE_SUMMARY', '''    const auto& s=*influence;
    if(settings().trace_search_domain)
        VTR_LOG("H3D_SEARCH_DOMAIN_SUMMARY searches=%zu rows=%zu omitted=%zu seed_rows=%zu seed_omitted=%zu row_cap=20000 seed_cap=6000\\n",
                s.domain_searches,s.domain_rows,s.domain_omitted,s.domain_seed_rows,s.domain_seed_omitted);
    VTR_LOG("H3D_GUIDE_INFLUENCE_SUMMARY''',1)
anchor='bool h3d_bounded_critical_stage_active()'
functions='''bool h3d_trace_search_domain() {return settings().trace_search_domain;}
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
    VTR_LOG("H3D_SEARCH_DOMAIN_SEED iter=%d attempt=%zu search=%zu net=%zu pin=%d node=%zu layer=%zu delay_seconds=%.17g backward=%.17g total=%.17g rcv=%d\\n",
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
            const auto head=graph.edge_sink_node(edge);
            if(!h3d_crosses_layers(graph,node,head))continue;
            ++preferred_cross_heads;
            admitted_cross_heads+=from_inside && (rcv || inside_bb(graph,head,bb));
        }
    }
    std::ostringstream layers;layers<<std::setprecision(17);
    for(size_t i=0;i<s.domain_layers.size();++i) {
        if(i)layers<<';';const auto& l=s.domain_layers[i];
        layers<<i<<','<<l.pushes<<','<<l.minimum_delay<<','<<l.minimum_backward<<','<<l.minimum_total;
    }
    VTR_LOG("H3D_SEARCH_DOMAIN iter=%d attempt=%zu search=%zu net=%zu pin=%d sink=%zu sink_layer=%d guide=%d criticality=%.17g preferred=%s preferred_inside=%zu crossing_heads=%zu admitted_heads=%zu xmin=%d xmax=%d ymin=%d ymax=%d layer_min=%d layer_max=%d rcv=%d layers=%s\\n",
        s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin,size_t(sink),int(graph.node_layer_low(sink)),int(guide!=nullptr),double(criticality),influence_preferences(guide).c_str(),preferred_inside,preferred_cross_heads,admitted_cross_heads,bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.layer_min,bb.layer_max,int(rcv),layers.str().c_str());
}

''';assert anchor in s;s=s.replace(anchor,functions+anchor,1);(R/'h3d_routing.cpp').write_text(s)
s=before['connection_router.tpp'];s=s.replace('    t_bb high_fanout_bb = add_high_fanout_route_tree_to_heap','    if(h3d_trace_search_domain())h3d_domain_reset();\n    t_bb high_fanout_bb = add_high_fanout_route_tree_to_heap',1);s=s.replace('    add_route_tree_to_heap(rt_root, sink_node, cost_params, bounding_box);','    if(h3d_trace_search_domain())h3d_domain_reset();\n    add_route_tree_to_heap(rt_root, sink_node, cost_params, bounding_box);',1)
anchor='    VTR_ASSERT_SAFE(heap_.is_valid());';s=s.replace(anchor,anchor+'\n    if(h3d_trace_search_domain())\n        h3d_domain_search(sink_node,cost_params.criticality,cost_params.h3d_guide,bounding_box,rcv_path_manager.is_enabled());',1);(R/'connection_router.tpp').write_text(s)
s=before['serial_connection_router.cpp'];s=s.replace('#include "vpr_context.h"','#include "vpr_context.h"\n#include "h3d_routing.h"',1);s=s.replace('        this->heap_.push_back({tot_cost, inode});','        this->heap_.push_back({tot_cost, inode});\n        if(h3d_trace_search_domain())h3d_domain_seed(inode,rt_node.Tdel,backward_path_cost,tot_cost,false);',1);s=s.replace('        this->heap_.push_back({expected_total_cost, inode});','        this->heap_.push_back({expected_total_cost, inode});\n        if(h3d_trace_search_domain())h3d_domain_seed(inode,rt_node.Tdel,backward_path_cost,expected_total_cost,true);',1);(R/'serial_connection_router.cpp').write_text(s)
patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names);(out/'implementation.patch').write_text(patch)
write(out/'binding.json',dict(status='implemented_not_built',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},protocol_sha256=sha(D/'search_domain_experiment_01.json'),script_sha256=sha(__file__),qualification='Only trace callbacks and state. No queue iteration/pop, no lookahead recomputation, no native routing-cost/state writes.'))
print('implemented read-only search-domain diagnostic')
