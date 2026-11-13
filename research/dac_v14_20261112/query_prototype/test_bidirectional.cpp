#include "h3d_bidirectional_delay.h"
#include <cassert>
#include <iostream>
#include <random>
using Search=H3dBidirectionalDelay;
int main() {
    using Edge=std::pair<size_t,double>;
    std::vector<std::vector<Edge>> out,in;
    auto forward=[&](size_t u,auto visit){for(auto [v,w]:out[u])visit(v,w);};
    auto reverse=[&](size_t u,auto visit){for(auto [v,w]:in[u])visit(v,w);};
    auto link=[&](size_t u,size_t v,double w){out[u].push_back({v,w});in[v].push_back({u,w});};
    // First meeting costs 10; a later path costs 3. A budget-truncated upper
    // bound must not be promoted to an exact measured distance.
    out.resize(4);in.resize(4);link(0,3,10);link(0,1,1);link(1,2,1);link(2,3,1);
    auto partial=Search::query(0,3,1,100,100,forward,reverse);
    assert(partial.stop==Search::Stop::WORK_LIMIT && !partial.exact);
    assert(Search::query(0,3,8,100,100,forward,reverse).exact==3.);
    auto limited=Search::query(0,3,8,2,100,forward,reverse);
    assert(limited.stop==Search::Stop::MEMORY_LIMIT && !limited.exact);
    std::mt19937 rng(20261113);size_t full=0,bounded=0;
    for(size_t graph=0;graph<200;++graph) {
        size_t n=8+rng()%23;out.assign(n,{});in.assign(n,{});
        std::vector<std::vector<double>> truth(n,std::vector<double>(n,INFINITY));
        for(size_t u=0;u<n;++u){truth[u][u]=0.;for(size_t v=0;v<n;++v)if(u!=v && rng()%9==0){double w=rng()%12;link(u,v,w);truth[u][v]=w;}}
        // Independent all-pairs dynamic program, no frontier or meet condition.
        for(size_t k=0;k<n;++k)for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)
            truth[u][v]=std::min(truth[u][v],truth[u][k]+truth[k][v]);
        for(size_t pair=0;pair<100;++pair) {
            size_t u=rng()%n,v=rng()%n;
            auto check=[&](auto r){
                if(r.exact)assert(*r.exact==truth[u][v]);
                if(r.stop==Search::Stop::UNREACHABLE)assert(!std::isfinite(truth[u][v]));
                assert(r.peak_labels<=2*n && r.peak_heap<=2*n*n);
            };
            auto r=Search::query(u,v,2*n,2*n,2*n*n,forward,reverse);check(r);
            assert(bool(r.exact)==std::isfinite(truth[u][v]));++full;
            size_t budget=rng()%(2*n+1);
            auto b=Search::query(u,v,budget,2*n,2*n*n,forward,reverse);check(b);
            assert(b.forward_settled+b.reverse_settled<=budget);++bounded;
        }
    }
    std::cout<<"full_oracle_pairs="<<full<<" bounded_oracle_pairs="<<bounded<<'\n';
}
