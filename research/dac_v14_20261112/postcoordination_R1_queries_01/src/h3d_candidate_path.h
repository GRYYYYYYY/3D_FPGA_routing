#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <queue>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/** @brief Bounded directed path discovery with an independently certified bound.
 * Heuristic values need not be admissible: they only order expansion. Every
 * label is an immutable path prefix, so reopening does not corrupt witnesses.
 * Only the minimum pending g-cost, never g+h, can certify optimality. Expand
 * must describe one fixed graph/price snapshot throughout the call.
 */
class H3dCandidatePath {
  public:
    enum class Stop { EXACT, FOUND_PATH, UNREACHABLE, WORK_LIMIT, MEMORY_LIMIT };
    struct Edge { size_t from, to; double physical_seconds, toll_seconds; };
    struct Result {
        Stop stop;
        std::optional<double> priced_upper_seconds, physical_path_seconds, toll_path_seconds;
        std::optional<double> lower_seconds;
        std::vector<Edge> edges;
        size_t expansions=0, labels=0, peak_heap=0;
    };

    template<typename Expand, typename Heuristic>
    static Result query(size_t source, size_t target, size_t budget,
                        size_t label_limit, size_t heap_limit,
                        Expand expand, Heuristic heuristic, bool stop_at_first_path=true) {
        if (!label_limit || heap_limit<2) throw std::invalid_argument("candidate path storage must admit root and two queues");
        constexpr size_t none=std::numeric_limits<size_t>::max();
        struct Label {
            size_t node, parent;
            double g, physical, toll, edge_physical, edge_toll;
            bool expanded=false;
        };
        using Priority=std::tuple<double,double,size_t,size_t>; // priority,g,node,label
        using Lower=std::tuple<double,size_t,size_t>; // g,node,label
        std::priority_queue<Priority,std::vector<Priority>,std::greater<Priority>> open;
        std::priority_queue<Lower,std::vector<Lower>,std::greater<Lower>> lower;
        std::vector<Label> labels;
        labels.reserve(std::min(label_limit,size_t(16384)));
        std::unordered_map<size_t,size_t> best;
        auto h=[&](size_t node) {
            double value=node==target ? 0. : heuristic(node);
            if (!std::isfinite(value) || value<0.) throw std::invalid_argument("finite nonnegative heuristic required");
            return value;
        };
        labels.push_back({source,none,0.,0.,0.,0.,0.});best[source]=0;
        open.emplace(h(source),0.,source,0);lower.emplace(0.,source,0);
        size_t used=0,peak_heap=2,goal=source==target ? 0 : none;
        bool memory_hit=false,goal_expanded=false;
        auto pending=[&](size_t id) {
            return !labels[id].expanded && best.at(labels[id].node)==id;
        };
        auto finish=[&](Stop stop,std::optional<double> bound) {
            Result answer{stop,std::nullopt,std::nullopt,std::nullopt,bound,{},used,labels.size(),peak_heap};
            if (goal==none) return answer;
            const auto& chosen=labels[goal];
            answer.priced_upper_seconds=chosen.g;answer.physical_path_seconds=chosen.physical;answer.toll_path_seconds=chosen.toll;
            std::unordered_set<size_t> seen;
            for (size_t id=goal;labels[id].parent!=none;id=labels[id].parent) {
                const auto& x=labels[id];
                if (!seen.insert(x.node).second || x.parent>=id) throw std::logic_error("invalid candidate path ancestry");
                answer.edges.push_back({labels[x.parent].node,x.node,x.edge_physical,x.edge_toll});
            }
            std::reverse(answer.edges.begin(),answer.edges.end());
            return answer;
        };
        while (true) {
            while (!open.empty() && !pending(std::get<3>(open.top()))) open.pop();
            while (!lower.empty() && !pending(std::get<2>(lower.top()))) lower.pop();
            // A dropped relaxation can conceal a cheaper path; expose no lower
            // certificate after storage loss, even when a valid witness exists.
            if (memory_hit) return finish(Stop::MEMORY_LIMIT,std::nullopt);
            double frontier=lower.empty() ? std::numeric_limits<double>::infinity() : std::get<0>(lower.top());
            if (goal!=none && labels[goal].g<=frontier) return finish(Stop::EXACT,labels[goal].g);
            if (open.empty()) return finish(Stop::UNREACHABLE,std::numeric_limits<double>::infinity());
            if (goal_expanded && stop_at_first_path) return finish(Stop::FOUND_PATH,frontier);
            if (used>=budget) return finish(Stop::WORK_LIMIT,frontier);
            size_t id=std::get<3>(open.top());open.pop();
            // Copy before relaxations: labels can reallocate while expanding.
            Label active=labels[id];labels[id].expanded=true;++used;
            if (active.node==target) { goal_expanded=true;continue; }
            expand(active.node,[&](size_t next,double physical,double toll) {
                if (!std::isfinite(physical) || physical<0. || !std::isfinite(toll) || toll<0.)
                    throw std::invalid_argument("finite nonnegative physical delay and price toll required");
                if (memory_hit) return;
                double value=active.g+(physical+toll);
                double p=active.physical+physical,t=active.toll+toll;
                if (!std::isfinite(value) || !std::isfinite(p) || !std::isfinite(t)) throw std::overflow_error("candidate path cost overflow");
                auto old=best.find(next);
                if (old!=best.end() && labels[old->second].g<=value) return;
                double priority=value+h(next);
                if (!std::isfinite(priority)) throw std::overflow_error("candidate priority overflow");
                if (labels.size()>=label_limit || open.size()+lower.size()+2>heap_limit) { memory_hit=true;return; }
                size_t new_id=labels.size();
                labels.push_back({next,id,value,p,t,physical,toll});best[next]=new_id;
                open.emplace(priority,value,next,new_id);lower.emplace(value,next,new_id);
                peak_heap=std::max(peak_heap,open.size()+lower.size());
                if (next==target) goal=new_id;
            });
        }
    }
};
