#pragma once
#include <cassert>
#include <map>
#include <queue>
#include <set>
#include <optional>
#include <cmath>
#include <limits>
#include <unordered_map>

/** @brief Independent Dijkstra lower-threshold check, with no adapter callbacks.
 * All states strictly cheaper than the claimed lower bound are settled. A
 * virtual seed goal cheaper than that bound is a contradiction. An infinite
 * claim requires exhausting reachable states. Missing claims are not checked.
 * Cost comparisons permit 1e-24 seconds plus 1e-12 relative roundoff; this is
 * numerical verification of the modeled graph, not exact real arithmetic/STA.
 */
template<class Nodes, class ReverseEdges>
long long verify_tree_lower(const Nodes& nodes, const ReverseEdges& rev, size_t sink,
    const std::vector<std::pair<size_t,double>>& seeds,
    const std::set<size_t>& preferred, const std::set<size_t>& tree,
    const std::set<size_t>& inherited, int mode,
    int xmin,int xmax,int ymin,int ymax,int lmin,int lmax,
    const std::optional<double>& claim) {
    if (!claim) return -1;
    const double bound=*claim;
    assert(bound>=0. && !std::isnan(bound));
    const int sink_layer=nodes[sink].layer;
    auto admissible=[&](size_t id) {
        const auto& node=nodes[id];
        return node.dx>=xmin && node.dx<=xmax && node.dy>=ymin && node.dy<=ymax
            && node.layer>=lmin && node.layer<=lmax;
    };
    std::map<size_t,double> goals;
    for (auto [id,delay]:seeds) {
        if (!admissible(id)) continue;
        if (nodes[id].layer==sink_layer && (!(mode&1) || !inherited.count(id))) continue;
        auto pos=goals.find(id);
        if (pos==goals.end() || delay<pos->second) goals[id]=delay;
    }
    // No permitted virtual terminal proves unreachable without graph traversal.
    if (goals.empty()) return 0;
    using Item=std::pair<double,size_t>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
    std::unordered_map<size_t,double> distances;
    queue.emplace(0.,sink);distances[sink]=0.;long long settled=0;
    while (!queue.empty()) {
        auto [cost,node]=queue.top();queue.pop();
        if(cost!=distances.at(node))continue;
        if(cost>=bound)break;
        ++settled;
        auto terminal=goals.find(node);
        if(terminal!=goals.end()) {
            double value=cost+terminal->second;
            assert(std::isfinite(bound));
            assert(value+1e-24+1e-12*std::max(std::abs(value),std::abs(bound))>=bound);
        }
        if ((mode&2) && tree.count(node))continue;
        for (auto edge:rev[node]) {
            const size_t predecessor=edge.node;
            if(!admissible(predecessor))continue;
            const int from_layer=nodes[predecessor].layer, to_layer=nodes[node].layer;
            if(from_layer!=to_layer && !(to_layer==sink_layer && from_layer!=sink_layer && preferred.count(predecessor)))continue;
            double next=cost+edge.weight;
            if(next>=bound)continue;
            auto pos=distances.find(predecessor);
            if(pos==distances.end() || next<pos->second) {
                distances[predecessor]=next;queue.emplace(next,predecessor);
            }
        }
    }
    return settled;
}
