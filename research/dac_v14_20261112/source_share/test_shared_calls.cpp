#include "../src/vpr/src/route/h3d_persistent_bidirectional.h"
#include <cassert>
#include <iostream>
#include <memory>
#include <random>
#include <unordered_map>
using Search = H3dPersistentBidirectional;
int main() {
    using Edge = std::pair<size_t,double>;
    std::mt19937 random(20261120);
    size_t calls=0,queries=0,certificates=0,evictions=0,memory_stops=0,zero_shares=0,unused=0;
    for (size_t graph=0;graph<1200;++graph) {
        size_t physical=8+random()%30, terminals=2+random()%12, n=physical+terminals;
        std::vector<std::vector<Edge>> out(n),in(n);
        std::vector<std::vector<double>> truth(n,std::vector<double>(n,INFINITY));
        for(size_t u=0;u<n;++u)truth[u][u]=0.;
        for(size_t u=0;u<physical;++u)for(size_t v=0;v<n;++v)
            if(u!=v && random()%6==0){double w=random()%11;out[u].emplace_back(v,w);in[v].emplace_back(u,w);truth[u][v]=w;}
        for(size_t k=0;k<n;++k)for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)
            truth[u][v]=std::min(truth[u][v],truth[u][k]+truth[k][v]);
        auto terminal=[&](size_t u){return u>=physical;};
        auto forward=[&](size_t u,auto visit){for(auto [v,w]:out[u])visit(v,w);};
        auto reverse=[&](size_t u,auto visit){for(auto [v,w]:in[u])visit(v,w);};
        for(size_t trial=0;trial<12;++trial) {
            size_t source=random()%physical, used=0, budget=trial==0?0:trial==1?SIZE_MAX:random()%(8*n), users=1+random()%25;
            std::unique_ptr<Search> search=std::make_unique<Search>(source);
            std::unordered_map<size_t,double> cached;
            for(size_t user=0;user<users;++user) {
                size_t before=used, left=budget-used, remaining_users=users-user;
                size_t share=left/remaining_users+(left%remaining_users!=0), end=used+share;
                assert(end<=budget);++calls;zero_shares+=share==0;
                size_t requests=1+random()%16;
                for(size_t request=0;request<requests;++request) {
                    size_t target=physical+random()%terminals;
                    if(cached.contains(target)){assert(cached.at(target)==truth[source][target]);continue;}
                    if(used>=end)continue;
                    if(random()%9==0){search=std::make_unique<Search>(source);++evictions;}
                    size_t allowance=std::min(size_t(1+random()%32),end-used);
                    bool tight=trial%3==0;
                    auto r=search->query(target,allowance,tight?8:2*n,tight?8:2*n*n,terminal,forward,reverse);
                    ++queries;size_t charged=r.forward_settled+r.reverse_settled;
                    assert(charged<=allowance);used+=charged;assert(used<=end && used<=budget);
                    if(r.exact){assert(*r.exact==truth[source][target]);cached[target]=*r.exact;}
                    if(r.stop==Search::Stop::UNREACHABLE)assert(!std::isfinite(truth[source][target]));
                    memory_stops+=r.stop==Search::Stop::MEMORY_LIMIT;
                    for(auto [t,d]:r.new_terminals){assert(terminal(t) && d==truth[source][t]);cached[t]=d;++certificates;}
                }
                assert(used-before<=share);unused+=used<end;
            }
        }
    }
    assert(certificates>1000 && zero_shares>0 && evictions>0 && memory_stops>0 && unused>0);
    std::cout<<"shared_calls="<<calls<<" queries="<<queries<<" certificates="<<certificates<<" forced_evictions="<<evictions<<" memory_stops="<<memory_stops<<" zero_shares="<<zero_shares<<" unused_calls="<<unused<<'\n';
}
