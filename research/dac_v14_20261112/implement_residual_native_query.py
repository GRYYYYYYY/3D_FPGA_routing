#!/usr/bin/env python3
import difflib
from retained_prefix_workflow import D,read,write,sha
R=D/'src/vpr/src/route';out=D/'residual_native_implementation_01';out.mkdir(exist_ok=False)
parent=read(D/'box_guide_stage_01/binding.json');assert all(sha(D/'src'/p)==h for p,h in parent['source_sha256'].items());assert read(D/'residual_query_offline_01/analysis.json')['passed'] and read(D/'residual_query_adapter_unit_01/validation.json')['passed']
names=['h3d_routing.cpp','h3d_delay_plan.h','h3d_delay_plan.cpp','h3d_fast_plan.h'];before={n:(R/n).read_text() for n in names}
for n,s in before.items():(out/n).write_text(s)
write(D/'residual_native_experiment_01.json',dict(status='registered_before_implementation',question='Do fixed-budget residual queries and chronological physical suffix reuse improve useful coverage in actual guided searches while preserving every native routing decision, and what online cost/work do they add?',input='eltwise_layer HybridO P0 W100 seed11 exact frozen packed/place/RRG,count2',arms=['C:off exact box-guide default0 control','Q0:zero heuristic query-only','Qh:spatial multi-target query-only','Qs:spatial, reuse prior static physical suffix if valid for current actual seed; otherwise query'],fixed='No scoring or guide decisions consume result; box-admission0, bounded absent, pathprice/delay0; all legacy4096/fresh256 controls fixed; current SCC/DP/target update unchanged.',scope='Actual guided native search after successful seed heap pushes, same-layer sources only, RCV excluded, no seeds skip. Per-search new query256, label16384/heap65536, at most2048unique same-layer sources (explicit resource skip). This additional work is separate from legacy query work and not claimed free.',cache='Only Qs: query-produced static physical suffixes keyed sink/source, max16variants/key and16384total; no dynamic sourceTdel/occupancy/prices. Check current source membership/current prefix/layer/native BB every lookup. Cache reset each fixedwidth trial. No repeated future path data.',trace='All query attempts (including skips/cache hits) and full current source IDs/Tdel. Path rows cap200000real+virtual edges cumulative, omitted counts explicit; online old trace separate. Current source set collected only when queryflag enabled. Whole native route/guide/originalcost/query/heap/prefix/numericrows must reproduce C; otherwise diagnose before scoring.',validation='Independent RRG every returned edge, current seed/prefix/BB/layer, chronological cache prior origin. Fresh reverse adapter exactly same existing tested generic engine. Static graph reverse index reused via existing H3dDelayPlan. Actual costs recorded online. Follow separately registered scoring only after validation.',limits=dict(seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),quality_claim=False,formal_timing_claim=False))
s=before['h3d_delay_plan.h'];a='    void log() const;';x='''    struct ResidualAnswer {
        int status=-4; bool cache_hit=false; size_t origin=0,cache_records=0,cache_stops=0;
        H3dCandidatePath::Result query{H3dCandidatePath::Stop::WORK_LIMIT,std::nullopt,std::nullopt,std::nullopt,std::nullopt,{},0,0,0};
    };
    ResidualAnswer probe_residual_sources(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,
        const t_bb& box,int mode,double heuristic_per_grid,size_t search);
''';assert a in s;s=s.replace(a,x+a,1)
a='    struct Predecessor {';x='''    struct ResidualSuffix { size_t origin;std::vector<H3dCandidatePath::Edge> reverse_edges; };
    std::map<std::pair<RRNodeId,RRNodeId>,std::vector<ResidualSuffix>> residual_cache_;
    size_t residual_cache_records_=0,residual_cache_stops_=0;
''';s=s.replace(a,x+a,1);(R/'h3d_delay_plan.h').write_text(s)
s=before['h3d_delay_plan.cpp'];s+='''

H3dDelayPlan::ResidualAnswer H3dDelayPlan::probe_residual_sources(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,
    const t_bb& box,int mode,double heuristic_per_grid,size_t search) {
    ResidualAnswer answer;
    if(!supported_ || !edge_encoding_)return answer;
    if(sources.empty()) {answer.status=-2;return answer;}
    if(sources.size()>2048) {answer.status=-3;return answer;}
    const size_t virtual_target=graph_.num_nodes();const auto layer=graph_.node_layer_low(sink);
    std::unordered_map<size_t,double> seeds;
    for(auto [node,delay]:sources) {
        VTR_ASSERT(graph_.node_layer_low(node)==layer && std::isfinite(delay) && delay>=0.);
        auto found=seeds.find(size_t(node));if(found==seeds.end() || delay<found->second)seeds[size_t(node)]=delay;
    }
    if(mode==2) {
        double best=std::numeric_limits<double>::infinity();const ResidualSuffix* chosen=nullptr;RRNodeId selected;
        for(auto [raw,prefix]:seeds) {
            const auto found=residual_cache_.find({sink,RRNodeId(raw)});if(found==residual_cache_.end())continue;
            for(const auto& candidate:found->second) {
                VTR_ASSERT(candidate.origin<search);double cost=prefix;bool valid=true;
                for(const auto& edge:candidate.reverse_edges) {
                    valid=valid && inside_bb(graph_,RRNodeId(edge.from),box) && inside_bb(graph_,RRNodeId(edge.to),box);
                    cost+=edge.physical_seconds;
                }
                if(valid && cost<best) {best=cost;chosen=&candidate;selected=RRNodeId(raw);}
            }
        }
        if(chosen) {
            answer.status=1;answer.cache_hit=true;answer.origin=chosen->origin;
            answer.query.stop=H3dCandidatePath::Stop::FOUND_PATH;answer.query.priced_upper_seconds=best;answer.query.physical_path_seconds=best;answer.query.toll_path_seconds=0.;
            answer.query.edges=chosen->reverse_edges;answer.query.edges.push_back({size_t(selected),virtual_target,seeds.at(size_t(selected)),0.});
            answer.cache_records=residual_cache_records_;answer.cache_stops=residual_cache_stops_;return answer;
        }
    }
    auto expand=[&](size_t raw,auto visit) {
        if(raw==virtual_target)return;
        auto seed=seeds.find(raw);if(seed!=seeds.end())visit(virtual_target,seed->second,0.);
        for(size_t i=reverse_start_[raw];i<reverse_start_[raw+1];++i) {
            const auto& edge=predecessors_[i];
            if(graph_.node_layer_low(edge.node)==layer && inside_bb(graph_,edge.node,box))visit(size_t(edge.node),double(edge.delay),0.);
        }
    };
    auto heuristic=[&](size_t raw) {
        if(mode==0 || raw==virtual_target)return 0.;
        const auto node=RRNodeId(raw);double best=std::numeric_limits<double>::infinity();
        for(auto [seed,prefix]:seeds) {
            const auto target=RRNodeId(seed);int d=std::abs(graph_.node_xlow(node)-graph_.node_xlow(target))+std::abs(graph_.node_ylow(node)-graph_.node_ylow(target));
            best=std::min(best,prefix+heuristic_per_grid*d);
        }
        return best;
    };
    answer.query=H3dCandidatePath::query(size_t(sink),virtual_target,256,16384,65536,expand,heuristic,true);
    answer.status=int(answer.query.stop);answer.origin=search;
    if(mode==2 && answer.query.physical_path_seconds) {
        const auto& path=answer.query.edges;VTR_ASSERT(!path.empty() && path.back().to==virtual_target);
        for(size_t count=0;count<path.size();++count) {
            const auto source=count ? RRNodeId(path[count-1].to) : sink;
            auto& variants=residual_cache_[{sink,source}];bool duplicate=false;
            for(const auto& variant:variants) {
                if(variant.reverse_edges.size()!=count)continue;
                bool same=true;for(size_t i=0;i<count;++i)same=same && variant.reverse_edges[i].from==path[i].from && variant.reverse_edges[i].to==path[i].to && variant.reverse_edges[i].physical_seconds==path[i].physical_seconds;
                duplicate=duplicate || same;
            }
            if(duplicate)continue;
            if(variants.size()>=16 || residual_cache_records_>=16384) {++residual_cache_stops_;continue;}
            variants.push_back({search,{path.begin(),path.begin()+count}});++residual_cache_records_;
        }
    }
    answer.cache_records=residual_cache_records_;answer.cache_stops=residual_cache_stops_;return answer;
}
''';(R/'h3d_delay_plan.cpp').write_text(s)
s=before['h3d_fast_plan.h'];a='    void log() const;';x='''    H3dDelayPlan::ResidualAnswer probe_residual(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,const t_bb& bb,int mode,size_t search) {
        if(!delay_plan_)return {};
        return delay_plan_->probe_residual_sources(sink,sources,bb,mode,4.*delay_plan_->delay_unit()/std::max(1.,mean_span_),search);
    }
''';assert a in s;s=s.replace(a,x+a,1);(R/'h3d_fast_plan.h').write_text(s)
s=before['h3d_routing.cpp'];s=s.replace('    bool box_guide_admission = false;', '    int residual_query_mode=-1;\n    bool box_guide_admission = false;',1)
a='        if(const char* text=std::getenv("VPR_H3D_BOX_GUIDE_ADMISSION"))';x='''        if(const char* text=std::getenv("VPR_H3D_RESIDUAL_QUERY")) {
            const std::string value=text;
            if(value=="off")result.residual_query_mode=-1;
            else if(value=="zero")result.residual_query_mode=0;
            else if(value=="spatial")result.residual_query_mode=1;
            else if(value=="reuse")result.residual_query_mode=2;
            else VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"VPR_H3D_RESIDUAL_QUERY must be off/zero/spatial/reuse");
            const char* domain=std::getenv("VPR_H3D_TRACE_SEARCH_DOMAIN");
            if(result.residual_query_mode>=0 && (!domain || std::string(domain)!="1" || !result.use_scc || !result.delay_cost))
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE,"Residual query diagnostic requires domain trace, SCC and delay planner");
        }
''';assert a in s;s=s.replace(a,x+a,1)
a='    const t_h3d_connection_guide* guide(ParentNetId net, int pin) const {';x='''    H3dDelayPlan::ResidualAnswer probe_residual(RRNodeId sink,const std::vector<std::pair<RRNodeId,double>>& sources,const t_bb& bb,int mode,size_t search) {
        if(!fast_plan_)return {};
        return fast_plan_->probe_residual(sink,sources,bb,mode,search);
    }
''';assert a in s;s=s.replace(a,x+a,1)
s=s.replace('    size_t box_suppressed=0,box_rows=0;', '''    size_t residual_requests=0,residual_queries=0,residual_hits=0,residual_paths=0,residual_work=0,residual_labels=0,residual_edges=0,residual_edge_omitted=0;
    double residual_seconds=0.;
    std::vector<std::pair<RRNodeId,double>> residual_sources;
    size_t box_suppressed=0,box_rows=0;''',1)
a='    if(settings().box_guide_admission)\n        VTR_LOG';x='''    if(settings().residual_query_mode>=0)
        VTR_LOG("H3D_RESIDUAL_SUMMARY mode=%d requests=%zu queries=%zu hits=%zu paths=%zu expansions=%zu labels=%zu edges=%zu edge_omitted=%zu seconds=%.17g\\n",settings().residual_query_mode,s.residual_requests,s.residual_queries,s.residual_hits,s.residual_paths,s.residual_work,s.residual_labels,s.residual_edges,s.residual_edge_omitted,s.residual_seconds);
''';assert a in s;s=s.replace(a,x+a,1)
s=s.replace('    ++s.domain_searches;s.domain_local_seed_rows=0;', '    ++s.domain_searches;s.domain_local_seed_rows=0;s.residual_sources.clear();',1)
a='    const size_t layer=graph.node_layer_low(node);VTR_ASSERT(layer<s.domain_layers.size());';x=a+'\n    if(settings().residual_query_mode>=0)s.residual_sources.emplace_back(node,double(delay));';assert a in s;s=s.replace(a,x,1)
a='    ++s.domain_rows;const auto& graph=g_vpr_ctx.device().rr_graph;';x=a+'''
    if(settings().residual_query_mode>=0 && guide && !rcv) {
        std::map<RRNodeId,double> unique;
        for(auto [node,delay]:s.residual_sources) {
            if(graph.node_layer_low(node)!=graph.node_layer_low(sink))continue;
            auto found=unique.find(node);if(found==unique.end() || delay<found->second)unique[node]=delay;
        }
        const std::vector<std::pair<RRNodeId,double>> sources(unique.begin(),unique.end());
        auto start=std::chrono::steady_clock::now();const auto r=planner->probe_residual(sink,sources,bb,settings().residual_query_mode,s.domain_searches);
        const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        ++s.residual_requests;s.residual_queries+=r.query.expansions>0;s.residual_hits+=r.cache_hit;s.residual_paths+=r.query.physical_path_seconds.has_value();
        s.residual_work+=r.query.expansions;s.residual_labels+=r.query.labels;s.residual_seconds+=seconds;
        std::ostringstream seed_text;seed_text<<std::setprecision(17);size_t seed_rows=0;
        for(auto [node,delay]:sources) {if(seed_rows>=2048)break;if(seed_rows++)seed_text<<';';seed_text<<size_t(node)<<','<<delay;}
        const size_t path_rows=r.query.edges.size()<=200000-s.residual_edges ? r.query.edges.size() : 0;
        s.residual_edge_omitted+=r.query.edges.size()-path_rows;
        VTR_LOG("H3D_RESIDUAL_QUERY iter=%d attempt=%zu search=%zu net=%zu pin=%d sink=%zu mode=%d criticality=%.17g status=%d hit=%d origin=%zu sources=%zu source_rows=%zu seeds=%s expansions=%zu labels=%zu peak_heap=%zu has_path=%d upper_seconds=%.17g has_lower=%d lower_seconds=%.17g path_edges=%zu edge_rows=%zu cache_records=%zu cache_stops=%zu seconds=%.17g\\n",
            s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin,size_t(sink),settings().residual_query_mode,double(criticality),r.status,int(r.cache_hit),r.origin,sources.size(),seed_rows,seed_rows?seed_text.str().c_str():"-",r.query.expansions,r.query.labels,r.query.peak_heap,int(r.query.physical_path_seconds.has_value()),r.query.physical_path_seconds.value_or(0.),int(r.query.lower_seconds.has_value()),r.query.lower_seconds.value_or(0.),r.query.edges.size(),path_rows,r.cache_records,r.cache_stops,seconds);
        for(size_t i=0;i<path_rows;++i) {
            const auto& e=r.query.edges[i];
            VTR_LOG("H3D_RESIDUAL_EDGE search=%zu index=%zu from=%zu to=%zu physical_seconds=%.17g toll_seconds=%.17g\\n",s.domain_searches,i,e.from,e.to,e.physical_seconds,e.toll_seconds);
        }
        s.residual_edges+=path_rows;
    }
''';assert a in s;s=s.replace(a,x,1);(R/'h3d_routing.cpp').write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},script_sha256=sha(__file__),protocol_sha256=sha(D/'residual_native_experiment_01.json'),qualification='Query-only callbacks cannot modify search costs, guides, RR graph/route state or old query ledgers; cache physical suffixes only.'))
(out/'implementation.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names))
