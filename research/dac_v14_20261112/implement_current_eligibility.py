#!/usr/bin/env python3
"""Bind and implement search-local current criticality eligibility."""
import difflib
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal
require_formal_terminal()
parent=read(D/'outside_native_stage_01/binding.json')
assert all(sha(D/'src'/p)==h for p,h in parent['source_sha256'].items())
for name in ['outside_native_eltwise_dev_01','outside_native_eltwise_dev_02','outside_rollback_dev_01']:
    r=read(D/name/'registration.json');proc=__import__('pathlib').Path('/proc')/str(r['pid'])/'stat'
    assert not proc.exists() or proc.read_text().split(') ',1)[1].split()[19]!=r['start_ticks']
    assert read(D/name/'input_seal.json')['passed']
out=D/'current_eligibility_implementation_01';out.mkdir(exist_ok=False)
R=D/'src/vpr/src/route';names=['h3d_routing.h','h3d_routing.cpp','connection_router.tpp'];before={n:(R/n).read_text() for n in names}
for n,t in before.items():(out/n).write_text(t)
s=before['h3d_routing.h'];a='bool h3d_box_guide_admission();';assert a in s;s=s.replace(a,a+'''
/** @brief Whether the stored soft guide may affect this actual setup search.
 * Disabled by default; never mutates the stored guide, Tdel, or native costs.
 */
bool h3d_current_guide_eligible(float criticality, const t_h3d_connection_guide* guide, bool rcv);
''',1);(R/'h3d_routing.h').write_text(s)
s=before['h3d_routing.cpp'];a='    bool box_guide_admission = false;';assert a in s;s=s.replace(a,a+'\n    bool current_guide_eligibility = false; ///< Gate soft preference by actual setup criticality.',1)
a='        if (result.feedback && (!result.use_scc || result.mode != e_h3d_mode::STATIC))';assert a in s;s=s.replace(a,'''        if (const char* text = std::getenv("VPR_H3D_CURRENT_GUIDE_ELIGIBILITY")) {
            if (std::string(text) != "0" && std::string(text) != "1")
                VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_CURRENT_GUIDE_ELIGIBILITY must be 0 or 1");
            result.current_guide_eligibility = std::string(text) == "1";
        }
        if (result.current_guide_eligibility
            && (!result.trace_search_domain || !result.edge_encoding || result.outside_eta >= 0. || result.box_guide_admission))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Current eligibility pilot requires domain trace and edge guides, without outside or box-admission policies");
'''+a,1)
a='    size_t box_suppressed=0,box_rows=0;';assert a in s;s=s.replace(a,a+'''
    size_t eligibility_checks=0,eligibility_guided=0,eligibility_suppressed=0,eligibility_rows=0; ///< Search-local gate counters.
''',1)
a='    if(settings().box_guide_admission)\n';assert a in s;s=s.replace(a,'''    if (settings().current_guide_eligibility)
        VTR_LOG("H3D_CURRENT_ELIGIBILITY_SUMMARY checks=%zu guided=%zu suppressed=%zu rows=%zu omitted=%zu threshold=%.17g\\n",
                s.eligibility_checks, s.eligibility_guided, s.eligibility_suppressed, s.eligibility_rows,
                s.eligibility_checks-s.eligibility_rows, double(settings().min_criticality));
'''+a,1)
a='bool h3d_box_guide_admission()';assert a in s;s=s.replace(a,'''bool h3d_current_guide_eligible(float criticality, const t_h3d_connection_guide* guide, bool rcv) {
    if (!settings().current_guide_eligibility) return true;
    VTR_ASSERT(influence);
    auto& s = *influence;
    // Both operands are native floats, identical to planning's threshold type.
    const bool suppressed = guide && !rcv && criticality < settings().min_criticality;
    ++s.eligibility_checks;
    s.eligibility_guided += guide != nullptr;
    s.eligibility_suppressed += suppressed;
    if (s.eligibility_rows < 20000) {
        ++s.eligibility_rows;
        VTR_LOG("H3D_CURRENT_ELIGIBILITY iter=%d attempt=%zu search=%zu net=%zu pin=%d guide=%d criticality=%.17g threshold=%.17g rcv=%d suppressed=%d\\n",
                s.iteration, s.attempts, s.domain_searches, s.current_net, s.current_pin,
                int(guide != nullptr), double(criticality), double(settings().min_criticality), int(rcv), int(suppressed));
    }
    return !suppressed;
}

'''+a,1);(R/'h3d_routing.cpp').write_text(s)
s=before['connection_router.tpp'];a='    timing_driven_find_single_shortest_path_from_heap(sink_node, search_cost_params, bounding_box, target_bb);';assert s.count(a)==1;s=s.replace(a,'''    if (!h3d_current_guide_eligible(cost_params.criticality, search_cost_params.h3d_guide,
                                   rcv_path_manager.is_enabled())) {
        search_cost_params.h3d_guide = nullptr;
    }
'''+a,1);(R/'connection_router.tpp').write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',parent='outside_native_stage_01',source_binding={n:dict(before_sha256=sha(out/n),after_sha256=sha(R/n)) for n in names},script_sha256=sha(__file__),protocol_sha256=sha(D/'current_guide_eligibility_experiment_01.json'),qualification='Only local cost-parameter guide pointer can be suppressed. Stored plans, native physics/RCV/congestion and query budgets unchanged. Defaultoff old-record/route gate required.'))
(out/'implementation.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),(R/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names))
print('Implemented',out)
