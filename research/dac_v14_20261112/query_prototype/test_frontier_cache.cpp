#include "h3d_delay_frontier_cache.h"
#include <cassert>
#include <iostream>
#include <random>

using Cache = H3dDelayFrontierCache;
int main() {
    auto terminal=[](size_t x){return x==10;};
    auto expand=[](size_t x,auto visit){if(x<10)visit(x+1,1.);};
    Cache cache({1,2,20,20,15,100});
    assert(cache.query(0,0,{10},3,terminal,expand).newly_settled==3);
    assert(cache.query(1,1,{10},1,terminal,expand).newly_settled==1);
    auto completed=cache.query(0,0,{10},20,terminal,expand);
    assert(completed.distances[0]==10. && completed.newly_settled==11);
    assert(cache.query(0,0,{10},20,terminal,expand).newly_settled==0);
    assert(cache.query(2,2,{10},20,terminal,expand).stop==Cache::Stop::KEY_LIMIT);
    cache.query(1,1,{10},1,terminal,expand);
    auto evicted=cache.query(0,0,{10},20,terminal,expand);
    assert(evicted.newly_settled==1 && !evicted.distances[0]); // only 1 of 15 remains
    cache.query(1,1,{10},1,terminal,expand);
    assert(cache.query(0,0,{10},20,terminal,expand).stop==Cache::Stop::WORK_LIMIT);
    assert(cache.stats().live_states==1 && cache.stats().ledger_keys==2);
    Cache global({2,3,20,20,100,11});
    assert(global.query(0,0,{10},30,terminal,expand).distances[0]==10.);
    assert(global.query(0,0,{10},30,terminal,expand).distances[0]==10.);
    assert(global.query(1,1,{10},30,terminal,expand).stop==Cache::Stop::WORK_LIMIT);
    assert(global.stats().work==11);
    bool threw=false;
    try {global.query(0,2,{10},1,terminal,expand);}catch(const std::invalid_argument&){threw=true;}
    assert(threw);
    Cache invalid({1,1,20,20,10,10});
    threw=false;
    try {invalid.query(0,0,{10},5,terminal,[](size_t,auto visit){visit(10,-1.);});}
    catch(const std::invalid_argument&){threw=true;}
    assert(threw && invalid.stats().work==10);
    assert(invalid.query(0,0,{10},10,terminal,expand).stop==Cache::Stop::WORK_LIMIT);
    // Adversarial key alternation: eviction cannot replenish endpoint work.
    Cache stress({3,20,20,20,40,230});
    std::mt19937 rng(20261112); size_t charged=0, measured=0;
    std::vector<size_t> per_key(20,0);
    for(size_t i=0;i<10000;++i) {
        size_t key=rng()%20,source=key%10;
        auto result=stress.query(key,source,{10},1+rng()%8,terminal,expand);
        charged+=result.newly_settled;per_key[key]+=result.newly_settled;
        assert(per_key[key]<=40 && charged<=230 && charged==stress.stats().work);
        assert(stress.stats().live_states<=3 && stress.stats().ledger_keys<=20);
        if(result.distances[0]) {assert(*result.distances[0]==10.-source);++measured;}
    }
    std::cout<<"cache_requests=10000 measured_exact="<<measured<<" charged="<<charged
             <<" evictions="<<stress.stats().evictions<<" restarts="<<stress.stats().restarts<<'\n';
}
