#!/usr/bin/env python3
"""Read-only complete actual-search seed/tree trace, separate from planner snapshots."""
import difflib
from retained_prefix_workflow import D,read,write,sha,require_formal_terminal
require_formal_terminal();parent=read(D/'current_eligibility_stage_02/binding.json');assert all(sha(D/'src'/p)==h for p,h in parent['source_sha256'].items())
out=D/'actual_search_tree_implementation_01';out.mkdir(exist_ok=False);p=D/'src/vpr/src/route/h3d_routing.cpp';before=p.read_text();(out/p.name).write_text(before)
s=before;a='    bool trace_search_domain = false;';assert a in s;s=s.replace(a,a+'\n    bool trace_actual_search_tree = false; ///< Read-only full guided-search roots/current tree.',1)
a='        if (result.feedback && (!result.use_scc || result.mode != e_h3d_mode::STATIC))';assert a in s;s=s.replace(a,'''        if (const char* text = std::getenv("VPR_H3D_TRACE_ACTUAL_SEARCH_TREE")) {
            if (std::string(text) != "0" && std::string(text) != "1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_TRACE_ACTUAL_SEARCH_TREE must be 0 or 1");
            result.trace_actual_search_tree = std::string(text) == "1";
        }
        if (result.trace_actual_search_tree
            && (!result.trace_search_domain || result.residual_query_mode != 2
                || result.current_guide_eligibility || result.box_guide_admission || result.outside_eta >= 0.))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Actual tree trace requires domain/reuse mode and isolated default guide policy");
'''+a,1)
a='    size_t box_suppressed=0,box_rows=0;';assert a in s;s=s.replace(a,a+'''
    size_t actual_contexts=0,actual_complete=0,actual_seed_rows=0,actual_tree_rows=0; ///< Full guided-search trace totals.
    size_t actual_seed_omitted=0,actual_tree_omitted=0; ///< Explicit incomplete-trace counts.
''',1)
a='    if(settings().box_guide_admission)\n';assert a in s;s=s.replace(a,'''    if (settings().trace_actual_search_tree)
        VTR_LOG("H3D_ACTUAL_SUMMARY contexts=%zu complete=%zu seed_rows=%zu tree_rows=%zu seed_omitted=%zu tree_omitted=%zu seed_cap=1000000 tree_cap=5000000\\n",
                s.actual_contexts,s.actual_complete,s.actual_seed_rows,s.actual_tree_rows,s.actual_seed_omitted,s.actual_tree_omitted);
'''+a,1)
a='    if(settings().residual_query_mode>=0 && guide && !rcv) {';assert s.count(a)==1;s=s.replace(a,'''    if (settings().trace_actual_search_tree && guide) {
        ++s.actual_contexts;
        const auto& tree = g_vpr_ctx.routing().route_trees[ParentNetId(s.current_net)];
        size_t tree_nodes=0;
        if (tree) for (const auto& node : tree->all_nodes()) { (void)node; ++tree_nodes; }
        const bool complete=tree.has_value() && !rcv
            && s.residual_sources.size() <= 1000000-s.actual_seed_rows
            && tree_nodes <= 5000000-s.actual_tree_rows;
        VTR_LOG("H3D_ACTUAL_SEARCH iter=%d attempt=%zu search=%zu net=%zu pin=%d sink=%zu criticality=%.17g preferred=%s rcv=%d tree_present=%d complete=%d seeds=%zu seed_rows=%zu tree_nodes=%zu tree_rows=%zu\\n",
                s.iteration,s.attempts,s.domain_searches,s.current_net,s.current_pin,size_t(sink),double(criticality),
                influence_preferences(guide).c_str(),int(rcv),int(tree.has_value()),int(complete),s.residual_sources.size(),
                complete?s.residual_sources.size():0,tree_nodes,complete?tree_nodes:0);
        if (complete) {
            ++s.actual_complete;
            size_t seq=0;
            for (auto [node,delay] : s.residual_sources) {
                VTR_LOG("H3D_ACTUAL_SEED search=%zu seq=%zu node=%zu layer=%zu delay=%.17g\\n",
                        s.domain_searches,seq++,size_t(node),size_t(graph.node_layer_low(node)),delay);
            }
            s.actual_seed_rows+=s.residual_sources.size();seq=0;
            for (const auto& node : tree->all_nodes()) {
                auto parent=node.parent();
                VTR_LOG("H3D_ACTUAL_TREE search=%zu seq=%zu node=%zu expand=%d delay=%.17g parent=%lld switch=%lld pin=%d\\n",
                        s.domain_searches,seq++,size_t(node.inode),int(node.re_expand),double(node.Tdel),
                        parent?static_cast<long long>(size_t(parent->inode)):-1ll,
                        parent?static_cast<long long>(size_t(node.parent_switch)):-1ll,node.net_pin_index);
            }
            s.actual_tree_rows+=tree_nodes;
        } else {
            s.actual_seed_omitted+=s.residual_sources.size();s.actual_tree_omitted+=tree_nodes;
        }
    }
'''+a,1);p.write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',parent='current_eligibility_stage_02',source_binding={p.name:dict(before_sha256=sha(out/p.name),after_sha256=sha(p))},script_sha256=sha(__file__),protocol_sha256=sha(D/'actual_search_tree_experiment_01.json'),qualification='Only read-only outputs and counters; no new query, cost, stored-guide, routing-tree or native Tdel modification. All-or-none context trace under explicit total row caps. Actual seeds preserve duplicate successful pushes for independent layer-count reconciliation.'))
(out/'implementation.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/'+p.name,tofile='b/'+p.name)))
s=(D/'prepare_current_eligibility_v2.py').read_text().replace('current_eligibility_stage_02','actual_search_tree_stage_01').replace('current_eligibility_implementation_02','actual_search_tree_implementation_01').replace('prepare_current_eligibility_v2.py','prepare_actual_search_tree.py').replace('current_guide_eligibility_experiment_01.json','actual_search_tree_experiment_01.json').replace('VPR_H3D_CURRENT_GUIDE_ELIGIBILITY','VPR_H3D_TRACE_ACTUAL_SEARCH_TREE').replace('Build search-local current-criticality guide gate; defaultoff exact frozen control and same-setting count1/count2 quality required.','Build read-only actual guided-search full seed/tree capture; off/on exact frozen route/query/cost/prefix/heap controls required.').replace('Frozen current-criticality eligibility candidate; defaultoff equivalence and gate-on paired quality pending.','Frozen actual-search tree/seed trace candidate; defaultoff and traceon exact equivalence pending.')
(D/'prepare_actual_search_tree.py').write_text(s)
print('Implemented read-only actual tree/seed trace')
