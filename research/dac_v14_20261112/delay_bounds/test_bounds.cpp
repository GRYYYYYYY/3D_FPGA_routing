#include "../src/vpr/src/route/h3d_persistent_bidirectional.h"
#include <cassert>
#include <iostream>
#include <random>
#include <memory>
using Search=H3dPersistentBidirectional;
int main() {
    using Edge=std::pair<size_t,double>;
    std::mt19937 random(20261114);size_t queries=0,labels=0,memory_stops=0,bound_checks=0,positive_bounds=0,evictions=0;
    for(size_t graph=0;graph<400;++graph) {
        size_t physical=8+random()%30,terminals=2+random()%10,n=physical+terminals;
        std::vector<std::vector<Edge>> out(n),in(n);
        std::vector<std::vector<double>> truth(n,std::vector<double>(n,INFINITY));
        for(size_t u=0;u<n;++u)truth[u][u]=0;
        auto link=[&](size_t u,size_t v,double w){out[u].push_back({v,w});in[v].push_back({u,w});truth[u][v]=std::min(truth[u][v],w);};
        for(size_t u=0;u<physical;++u)for(size_t v=0;v<n;++v)
            if(u!=v && random()%7==0)link(u,v,random()%12);
        for(size_t k=0;k<n;++k)for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)
            truth[u][v]=std::min(truth[u][v],truth[u][k]+truth[k][v]);
        auto terminal=[&](size_t u){return u>=physical;};
        auto forward=[&](size_t u,auto visit){for(auto [v,w]:out[u])visit(v,w);};
        auto reverse=[&](size_t u,auto visit){for(auto [v,w]:in[u])visit(v,w);};
        for(size_t trial=0;trial<10;++trial) {
            size_t source=random()%physical,used=0,limit=random()%(4*n);
            Search full(source),bounded(source),limited(source);
            auto evicted=std::make_unique<Search>(source);size_t eviction_work=0;
            std::unordered_set<size_t> full_known,bounded_known,limited_known,evicted_known;
            double full_lower=0.,bounded_lower=0.,limited_lower=0.,evicted_lower=0.;
            auto check_bound=[&](Search& search,auto& known,double& lower,const auto& answer,size_t target) {
                for(auto [node,value]:answer.new_terminals)known.insert(node);
                if(answer.exact)known.insert(target);
                auto current=search.unsettled_lower_bound();if(current)lower=std::max(lower,*current);
                positive_bounds+=lower>0.;
                for(size_t node=physical;node<n;++node)if(!known.contains(node)) {
                    assert(lower<=truth[source][node]);++bound_checks;
                }
            };
            for(size_t request=0;request<40;++request) {
                size_t target=physical+random()%terminals;
                auto verify=[&](auto r){
                    if(r.exact)assert(*r.exact==truth[source][target]);
                    if(r.stop==Search::Stop::UNREACHABLE)assert(!std::isfinite(truth[source][target]));
                    for(auto [t,d]:r.new_terminals){assert(terminal(t) && d==truth[source][t]);++labels;}
                    ++queries;
                };
                auto a=full.query(target,2*n,2*n,2*n*n,terminal,forward,reverse);verify(a);
                assert(bool(a.exact)==std::isfinite(truth[source][target]));
                size_t allowance=std::min(limit-used,size_t(random()%9));
                auto b=bounded.query(target,allowance,2*n,2*n*n,terminal,forward,reverse);verify(b);
                assert(b.forward_settled+b.reverse_settled<=allowance);used+=b.forward_settled+b.reverse_settled;assert(used<=limit);
                auto m=limited.query(target,7,8,8,terminal,forward,reverse);verify(m);
                memory_stops+=m.stop==Search::Stop::MEMORY_LIMIT;
                check_bound(full,full_known,full_lower,a,target);
                check_bound(bounded,bounded_known,bounded_lower,b,target);
                check_bound(limited,limited_known,limited_lower,m,target);
                if(random()%4==0){evicted=std::make_unique<Search>(source);++evictions;}
                size_t slice=std::min(limit-eviction_work,size_t(random()%9));
                auto e=evicted->query(target,slice,2*n,2*n*n,terminal,forward,reverse);verify(e);
                eviction_work+=e.forward_settled+e.reverse_settled;assert(eviction_work<=limit);
                check_bound(*evicted,evicted_known,evicted_lower,e,target);
            }
        }
    }
    std::cout<<"sequential_queries="<<queries<<" incidental_certificates="<<labels<<" memory_stops="<<memory_stops<<" bound_constraints="<<bound_checks<<" positive_bound_checks="<<positive_bounds<<" forced_evictions="<<evictions<<'\n';
}
