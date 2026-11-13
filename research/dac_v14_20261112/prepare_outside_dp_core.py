#!/usr/bin/env python3
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
out=D/'outside_dp_core_01';out.mkdir(exist_ok=False);(out/'src').mkdir();R=D/'src/vpr/src/route'
assert read(D/'retained_outside_trace_eltwise_dev_01/outside_trace_analysis.json')['passed']
write(out/'registration.json',dict(status='registered_before_implementation',question='Does an explicit no-new-cross leaf outside option preserve eta0 old DP behavior and optimize the registered fixed-hierarchy surrogate, with correct prior-assignment reevaluation and physical group accounting?',source_sha256={str(R/n):sha(R/n) for n in ['h3d_partition_dp.h','h3d_independent_plan.h']},validation='Independent enumeration of every fixed-hierarchy cut on random small tables; physical/outside/empty/invalid prior assignments; original eta0 cost/assignment tie behavior. Captured real finite tables replay before native mutation. No native quality claim.'))
s=(R/'h3d_partition_dp.h').read_text();s=s.replace('    std::vector<t_h3d_candidate_cost> candidates;', '    double outside_cost=std::numeric_limits<double>::infinity(); ///< Optional existing-tree continuation; no crossing opened.\n    std::vector<t_h3d_candidate_cost> candidates;',1)
# Keep old four-field aggregate initialization stable: place the optional field after candidates.
s=s.replace('    double outside_cost=std::numeric_limits<double>::infinity(); ///< Optional existing-tree continuation; no crossing opened.\n','',1)
a='    std::vector<t_h3d_candidate_cost> candidates; ///< Sorted by channel, with no duplicate channels.';assert a in s;s=s.replace(a,a+'\n    double outside_cost=std::numeric_limits<double>::infinity(); ///< Optional existing-tree continuation; no crossing opened.',1)
s=s.replace('    size_t groups = 0;                                     ///< Number of shared groups in the hierarchical partition.','    size_t groups = 0;                                     ///< Number of physical crossing groups.\n    size_t outside_leaves = 0; ///< Outside assignments use channel==opening_cost.size(), not a real channel.')
s=s.replace('            result.best.groups = left.best.groups + right.best.groups;','            result.best.groups = left.best.groups + right.best.groups;\n            result.best.outside_leaves=left.best.outside_leaves+right.best.outside_leaves;',1)
s=s.replace('            result.best.groups = 1;','            result.best.groups = 1;\n            result.best.outside_leaves=0;',1)
a='    return result;\n}\n\n} // namespace h3d_detail';x='''    if(leaves.size()==1 && leaves.front().outside_cost<result.best.cost) {
        result.best.cost=leaves.front().outside_cost;
        result.best.assignment={{leaves.front().pin,opening_cost.size()}};
        result.best.groups=0;result.best.outside_leaves=1;
    }
'''+a;assert a in s;s=s.replace(a,x,1)
a='    for (const auto& leaf : leaves) {\n        for (size_t i = 0;';x='    for (const auto& leaf : leaves) {\n        VTR_ASSERT(!std::isnan(leaf.outside_cost) && leaf.outside_cost>=0.);\n        for (size_t i = 0;';assert a in s;s=s.replace(a,x,1)
a=s.index('    size_t shared = opening.size();',s.index('inline double h3d_assignment_cost'));z=s.index('    int xmin = leaves.front().x',a)
s=s[:a]+'''    size_t shared=opening.size();bool physical_seen=false,common=true;double branches=0.;
    for(const auto& leaf:leaves) {
        auto selected=std::find_if(assignment.begin(),assignment.end(),[&](const auto& a){return a.first==leaf.pin;});
        if(selected==assignment.end())return std::numeric_limits<double>::infinity();
        if(selected->second==opening.size()) {
            if(!std::isfinite(leaf.outside_cost))return std::numeric_limits<double>::infinity();
            if(leaves.size()==1)return leaf.outside_cost;
            common=false;continue;
        }
        auto candidate=std::find_if(leaf.candidates.begin(),leaf.candidates.end(),[&](const auto& c){return c.channel==selected->second;});
        if(candidate==leaf.candidates.end())return std::numeric_limits<double>::infinity();
        if(!physical_seen){shared=selected->second;physical_seen=true;}
        common=common && shared==selected->second;branches+=candidate->branch_cost;
    }
    if(common && physical_seen)return opening.at(shared)+branches;
'''+s[z:]
(out/'src/h3d_partition_dp.h').write_text(s)
s=(R/'h3d_independent_plan.h').read_text().replace('        if (!std::isfinite(best)) return {};','        if(leaf.outside_cost<best) {best=leaf.outside_cost;chosen=opening.size();}\n        if (!std::isfinite(best)) return {};',1).replace('        ++result.groups;','        if(chosen==opening.size())++result.outside_leaves;else ++result.groups;',1);(out/'src/h3d_independent_plan.h').write_text(s)
write(out/'implementation_binding.json',dict(status='implemented_uncompiled_isolated_core',source_sha256={str(out/'src'/n):sha(out/'src'/n) for n in ['h3d_partition_dp.h','h3d_independent_plan.h']},qualification='Not integrated into mutable router yet. Sentinel is explicit outside-kind channel==opening.size(); physical channel accesses remain invalid for it and must be handled at native integration. Outside chosen only if strictly cheaper at leaf; eta0 tie preserves physical.'))
print('isolated extended DP core written')
