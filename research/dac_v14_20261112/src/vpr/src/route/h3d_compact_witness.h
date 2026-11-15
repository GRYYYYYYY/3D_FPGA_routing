#pragma once
#include "h3d_delay_search.h"
#include <unordered_map>

/** Ancestor union of returned terminals in the already settled forest.
 * Stable filtering preserves canonical physical paths and edge weights.
 * No search is performed; no tentative parent can enter the cache. */
inline std::vector<H3dDelaySearch::WitnessStep> h3d_compact_witness(const H3dDelaySearch::Result& result) {
    if (result.terminals.empty()) return {};
    std::unordered_map<size_t,size_t> index;
    index.reserve(result.witness.size());
    for(size_t i=0;i<result.witness.size();++i)
        if(!index.emplace(result.witness[i].node,i).second)
            throw std::logic_error("Duplicate settled witness node");
    std::vector<bool> retained(result.witness.size(),false);
    for(const auto& terminal:result.terminals) {
        size_t node=terminal.first;
        while(true) {
            auto found=index.find(node);
            if(found==index.end())throw std::logic_error("Missing settled witness ancestor");
            size_t i=found->second;
            if(retained[i])break;
            retained[i]=true;
            size_t parent=result.witness[i].parent;
            if(parent==node)break;
            auto ancestor=index.find(parent);
            if(ancestor==index.end() || ancestor->second>=i)
                throw std::logic_error("Witness ancestor must have settled earlier");
            node=parent;
        }
    }
    std::vector<H3dDelaySearch::WitnessStep> answer;
    for(size_t i=0;i<result.witness.size();++i)
        if(retained[i])answer.push_back(result.witness[i]);
    return answer;
}
