#pragma once
#include "h3d_candidate_path.h"
#include <map>
#include <set>

/** @brief Physical shortest extension from a fixed retained tree.
 * Reverse traversal stops at every retained node. Only eligible branch anchors
 * contribute a terminal edge with their current physical root-to-node prefix.
 * Capacity filtering is a node-occupancy relaxation, not native FULL legality.
 */
template<class Reverse>
H3dCandidatePath::Result query_critical_capacity(size_t count,size_t sink,
    const std::set<size_t>& retained,const std::map<size_t,double>& anchors,
    const std::set<size_t>& blocked,bool enforce_capacity,Reverse reverse,
    size_t budget,size_t labels,size_t heap) {
    auto expand=[&](size_t node,auto visit) {
        if(node==count)return;
        if(enforce_capacity && blocked.count(node))return;
        auto anchor=anchors.find(node);
        if(anchor!=anchors.end())visit(count,anchor->second,0.);
        if(retained.count(node))return;
        reverse(node,[&](size_t predecessor,double weight) {
            if(!enforce_capacity || !blocked.count(predecessor))visit(predecessor,weight,0.);
        });
    };
    return H3dCandidatePath::query(sink,count,budget,labels,heap,expand,[](size_t){return 0.;},false);
}
