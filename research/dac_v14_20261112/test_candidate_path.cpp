#include "src/vpr/src/route/h3d_candidate_path.h"
#include <cassert>
#include <iostream>
#include <random>

using Search=H3dCandidatePath;
struct Arc {size_t to;double physical,toll;};
using Graph=std::vector<std::vector<Arc>>;

void validate(const Graph& graph,size_t source,size_t target,double optimum,const Search::Result& r) {
    if (r.lower_seconds) assert(*r.lower_seconds<=optimum);
    if (!r.priced_upper_seconds) {assert(r.edges.empty());return;}
    assert(*r.priced_upper_seconds>=optimum);
    size_t node=source;double cost=0.,physical=0.,toll=0.;std::unordered_set<size_t> seen{source};
    for (const auto& e:r.edges) {
        assert(e.from==node && seen.insert(e.to).second);
        bool present=false;
        for (const auto& a:graph[node]) present|=a.to==e.to && a.physical==e.physical_seconds && a.toll==e.toll_seconds;
        assert(present);node=e.to;cost+=e.physical_seconds+e.toll_seconds;physical+=e.physical_seconds;toll+=e.toll_seconds;
    }
    assert(node==target && cost==*r.priced_upper_seconds && physical==*r.physical_path_seconds && toll==*r.toll_path_seconds);
    if (r.stop==Search::Stop::EXACT) assert(cost==optimum && *r.lower_seconds==optimum);
}

int main() {
    size_t queries=0,exact=0,witnesses=0;
    std::mt19937 random(20261114);
    for (size_t trial=0;trial<200;++trial) {
        size_t n=1+random()%18;Graph graph(n);
        for (size_t u=0;u<n;++u) for (size_t v=0;v<n;++v)
            if (random()%4==0) graph[u].push_back({v,double(random()%7),double(random()%9)/4.});
        if (n>1) {graph[0].push_back({1,0.,0.});graph[1].push_back({0,0.,0.});graph[0].push_back({1,5.,0.});}
        double infinity=std::numeric_limits<double>::infinity();
        std::vector<std::vector<double>> floyd(n,std::vector<double>(n,infinity));
        for (size_t u=0;u<n;++u) {
            floyd[u][u]=0.;for (auto e:graph[u]) floyd[u][e.to]=std::min(floyd[u][e.to],e.physical+e.toll);
        }
        for (size_t k=0;k<n;++k) for (size_t u=0;u<n;++u) for (size_t v=0;v<n;++v)
            floyd[u][v]=std::min(floyd[u][v],floyd[u][k]+floyd[k][v]);
        for (size_t sample=0;sample<20;++sample) {
            size_t source=random()%n,target=random()%n;
            std::vector<double> estimates(n);for (double& value:estimates)value=random()%200;
            auto expand=[&](size_t u,auto visit){for (auto a:graph[u])visit(a.to,a.physical,a.toll);};
            for (bool spatial:{false,true}) for (bool first:{false,true}) for (size_t budget:{size_t(0),size_t(random()%(n+1)),size_t(20000)}) {
                auto h=[&](size_t u){return spatial ? estimates[u] : 0.;};
                auto r=Search::query(source,target,budget,200000,800000,expand,h,first);
                validate(graph,source,target,floyd[source][target],r);
                assert(r.expansions<=budget && r.labels<=200000 && r.peak_heap<=800000);
                if (budget==20000) assert(r.stop==Search::Stop::EXACT || r.stop==Search::Stop::UNREACHABLE || (first && r.stop==Search::Stop::FOUND_PATH));
                if (!spatial) assert(r.stop!=Search::Stop::FOUND_PATH);
                exact+=r.stop==Search::Stop::EXACT;witnesses+=r.priced_upper_seconds.has_value();++queries;
            }
            for (size_t labels:{size_t(1),size_t(2),size_t(5)}) {
                auto r=Search::query(source,target,100,labels,2*labels+2,expand,[&](size_t u){return estimates[u];},false);
                validate(graph,source,target,floyd[source][target],r);
                assert(r.labels<=labels && r.peak_heap<=2*labels+2);
                if (r.stop==Search::Stop::MEMORY_LIMIT) assert(!r.lower_seconds);
                ++queries;
            }
        }
    }
    // Deliberately non-admissible ordering: first path costs11, true optimum3.
    Graph misleading={{{1,10,0},{2,1,0}},{{3,1,0}},{{1,1,0}},{}};
    auto expand=[&](size_t u,auto visit){for(auto a:misleading[u])visit(a.to,a.physical,a.toll);};
    auto h=[](size_t u){return u==2 ? 100. : 0.;};
    auto fast=Search::query(0,3,100,100,400,expand,h,true);
    assert(fast.stop==Search::Stop::FOUND_PATH && *fast.priced_upper_seconds==11. && *fast.lower_seconds==1.);
    auto proven=Search::query(0,3,100,100,400,expand,h,false);
    assert(proven.stop==Search::Stop::EXACT && *proven.priced_upper_seconds==3.);validate(misleading,0,3,3.,proven);
    // Optimal priced path need not be a shortest physical-delay path.
    Graph parallel={{{1,0,7},{1,5,0}},{}};
    auto p=Search::query(0,1,10,10,40,[&](size_t u,auto visit){for(auto a:parallel[u])visit(a.to,a.physical,a.toll);},[](size_t){return 0.;});
    assert(p.stop==Search::Stop::EXACT && *p.priced_upper_seconds==5. && *p.physical_path_seconds==5.);
    // Storage loss after discovering a path must invalidate lower certification.
    Graph lost={{{2,10,0},{1,1,0}},{{2,1,0}},{}};
    auto m=Search::query(0,2,10,2,20,[&](size_t u,auto visit){for(auto a:lost[u])visit(a.to,a.physical,a.toll);},[](size_t){return 0.;});
    assert(m.stop==Search::Stop::MEMORY_LIMIT && *m.priced_upper_seconds==10. && !m.lower_seconds);
    bool rejected=false;
    try {Search::query(0,1,1,10,40,[](size_t,auto visit){visit(1,-1.,0.);},[](size_t){return 0.;});}
    catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected);
    std::cout<<"random_queries="<<queries<<" exact="<<exact<<" witnesses="<<witnesses<<" targeted_fixtures=4 passed\n";
}
