#!/usr/bin/env python3
import difflib
from retained_prefix_workflow import D,read,write,sha
R=D/'src/vpr/src/route';out=D/'box_guide_implementation_01';out.mkdir(exist_ok=False);names=['h3d_routing.cpp','h3d_routing.h','connection_router.tpp'];before={n:(R/n).read_text() for n in names}
assert read(D/'search_domain_eltwise_dev_01/search_domain_analysis.json')['passed']
write(D/'box_guide_experiment_01.json',dict(status='registered_before_implementation',hypothesis='A guide with zero preferred crossing edges admitted by the actual per-search BB can charge misses with no preferred option. Suppress only that search-local soft preference; recompute for each HF/full-tree retry.',input='same eltwise_layer HybridO P0 W100 seed11 packed/place/RRG',arms=['C2:flag0 exact frozen C count2','B2:flag1 count2','B1:flag1 firstlegal, exact prefix B2 required'],references='Strict reuse count1/count2 A0/R1/Tf/A1 and C controls from sealed cap-range registration; no formal timing reuse.',fixed='same Tf shared-DP/delay budgets4096/fresh256; path-score/delay0; bounded critical flag absent; domain/influence trace1; original source reverse skip0',guard=dict(timeout_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),method='Only edge-encoded guides; require no preferred source/head pair passes native inside_bb drivepoint checks. Disable for RCV bypass. Copy search cost params locally after heap build; no guide/planner/physicalTdel/STA/native congestion/tree/transaction state mutation. Keep all native search branches.',validation='Defaultoff exact frozen C, all three statuses retained; independent native graph/guide audit, actual decision RRG+BB tests, same-enabled firstlegal replay; no candidate promotion from count2 alone.',evidence='search_domain_eltwise_dev_01/search_domain_analysis.json:27/3809 searches locally BB-exclude all preferred heads; this is not a reachability test or explanation of focus misses.'))
for n,s in before.items():(out/n).write_text(s)
s=before['h3d_routing.h'].replace('void h3d_domain_reset();','bool h3d_box_guide_admission();\nbool h3d_box_guide_available(const t_h3d_connection_guide& guide,const t_bb& bb);\nvoid h3d_box_guide_suppressed();\nvoid h3d_domain_reset();');(R/'h3d_routing.h').write_text(s)
s=before['h3d_routing.cpp'].replace('bool trace_search_domain = false;','bool box_guide_admission = false;\n    bool trace_search_domain = false;',1)
a='        if(const char* text=std::getenv("VPR_H3D_TRACE_SEARCH_DOMAIN"))'
x='''        if(const char* text=std::getenv("VPR_H3D_BOX_GUIDE_ADMISSION")) {
            if(std::string(text)!="0" && std::string(text)!="1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_BOX_GUIDE_ADMISSION must be 0 or 1");
            result.box_guide_admission=std::string(text)=="1";
        }
        if(result.box_guide_admission && !result.edge_encoding)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Box guide admission requires edge encoding");
''';assert a in s;s=s.replace(a,x+a,1)
s=s.replace('size_t domain_searches=0,','size_t box_suppressed=0,box_rows=0;\n    size_t domain_searches=0,',1)
s=s.replace('    if(settings().trace_search_domain)\n        VTR_LOG', '''    if(settings().box_guide_admission)
        VTR_LOG("H3D_BOX_GUIDE_SUMMARY suppressed=%zu rows=%zu omitted=%zu\\n",s.box_suppressed,s.box_rows,s.box_suppressed-s.box_rows);
    if(settings().trace_search_domain)
        VTR_LOG''',1)
a='bool h3d_trace_search_domain()'
x='''bool h3d_box_guide_admission() {return settings().box_guide_admission;}
bool h3d_box_guide_available(const t_h3d_connection_guide& guide,const t_bb& bb) {
    const auto& graph=g_vpr_ctx.device().rr_graph;
    for(auto node:guide.preferred) {
        if(!inside_bb(graph,node,bb))continue;
        for(auto edge:graph.edges(node)) {
            const auto head=graph.edge_sink_node(node,edge);
            if(h3d_crosses_layers(graph,node,head) && inside_bb(graph,head,bb))return true;
        }
    }
    return false;
}
void h3d_box_guide_suppressed() {
    if(!influence)return;auto& s=*influence;++s.box_suppressed;
    if(s.box_rows>=2000)return;
    ++s.box_rows;
    VTR_LOG("H3D_BOX_GUIDE_SUPPRESSED iter=%d attempt=%zu search=%zu net=%zu pin=%d\\n",s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin);
}

''';assert a in s;s=s.replace(a,x+a,1);s=s.replace('    if(!influence)return;auto& s=*influence;++s.box_suppressed;','    if(!influence)return;\n    auto& s=*influence;++s.box_suppressed;');(R/'h3d_routing.cpp').write_text(s)
s=before['connection_router.tpp'];a='    timing_driven_find_single_shortest_path_from_heap(sink_node, cost_params, bounding_box, target_bb);'
x='''    // Search-local fallback: no guide metadata or native physical cost is changed.
    auto search_cost_params=cost_params;
    if(h3d_box_guide_admission() && cost_params.h3d_guide
       && cost_params.h3d_guide->edge_encoding && !rcv_path_manager.is_enabled()
       && !h3d_box_guide_available(*cost_params.h3d_guide,bounding_box)) {
        search_cost_params.h3d_guide=nullptr;
        h3d_box_guide_suppressed();
    }
    timing_driven_find_single_shortest_path_from_heap(sink_node, search_cost_params, bounding_box, target_bb);''';assert a in s;s=s.replace(a,x,1);(R/'connection_router.tpp').write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},protocol_sha256=sha(D/'box_guide_experiment_01.json'),script_sha256=sha(__file__)))
(out/'implementation.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names))
