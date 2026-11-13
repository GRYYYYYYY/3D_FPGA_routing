#include "../src/vpr/src/route/h3d_persistent_bidirectional.h"
#include <cassert>
#include <iostream>
#include <random>
using Search=H3dPersistentBidirectional;
int main() {
    using Edge=std::pair<size_t,double>;
    std::mt19937 random(20261114);size_t queries=0,labels=0,memory_stops=0;
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
            }
        }
    }
    std::cout<<"sequential_queries="<<queries<<" incidental_certificates="<<labels<<" memory_stops="<<memory_stops<<'\n';
}
