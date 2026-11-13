#include "h3d_resumable_delay_search.h"
#include "h3d_delay_search.h"
#include <cassert>
#include <iostream>
#include <random>
using Search=H3dResumableDelaySearch;
int main() {
 // A cheaper path is found after a tentative goal label: that label must stay hidden.
 std::vector<std::vector<std::pair<size_t,double>>> graph={{{1,10},{2,1}}, {}, {{1,1}}};
 auto terminal=[](size_t n){return n==1;};
 auto expand=[&](size_t n,auto visit){for(auto [v,w]:graph[n])visit(v,w);};
 Search s(0,3,10,10);
 assert(s.query({1},1,terminal,expand).stop==Search::e_stop::QUOTA);
 assert(!s.terminal_distance(1));
 auto r=s.query({1},2,terminal,expand);assert(r.total_settled==3 && *s.terminal_distance(1)==2);
 assert(s.query({1,1},100,terminal,expand).newly_settled==0);
 Search bounded(0,1,10,10);assert(bounded.query({1},10,terminal,expand).stop==Search::e_stop::TOTAL_BUDGET);
 assert(!bounded.terminal_distance(1));
 Search capped(0,3,1,10);assert(capped.query({1},10,terminal,expand).stop==Search::e_stop::MEMORY_LIMIT);
 assert(capped.query({1},10,terminal,expand).newly_settled==0);
 std::mt19937 rng(20261112);size_t checked=0;
 for(int trial=0;trial<500;++trial) {
  size_t n=10+rng()%40;graph.assign(n,{});
  for(size_t u=0;u<n-4;++u)for(size_t v=0;v<n;++v)if(u!=v && rng()%7==0)graph[u].push_back({v,double(rng()%8)});
  auto end=[&](size_t x){return x>=n-4;};
  H3dDelaySearch oracle(n);auto truth=oracle.query(0,n,end,expand);
  std::unordered_map<size_t,double> expected(truth.terminals.begin(),truth.terminals.end());
  Search state(0,n,n,4*n*n);
  size_t charged=0;
  for(size_t goal=n-4;goal<n;++goal) {
   for(size_t step=0;step<=n;++step) {
    auto answer=state.query({goal},1+rng()%5,end,expand);charged+=answer.newly_settled;
    assert(charged==answer.total_settled && charged<=n);
    if(answer.stop!=Search::e_stop::QUOTA)break;
   }
   auto measured=state.terminal_distance(goal);
   assert(bool(measured)==expected.contains(goal));
   if(measured)assert(*measured==expected.at(goal));
   ++checked;
  }
 }
 // Two nearby terminal requests reuse the frontier and stay under one budget.
 graph.assign(20,{});for(size_t i=0;i<19;++i)graph[i].push_back({i+1,1});
 graph[1].push_back({18,0});graph[4].push_back({19,0});
 auto goals=[](size_t n){return n>=18;};Search reused(0,20,20,100);
 auto first=reused.query({18},20,goals,expand);auto second=reused.query({19},20,goals,expand);
 Search restart(0,20,20,100);auto repeated=restart.query({19},20,goals,expand);
 assert(first.newly_settled+second.newly_settled<first.newly_settled+repeated.newly_settled);
 std::cout<<"oracle_terminal_checks="<<checked<<" reuse_settled="<<first.newly_settled+second.newly_settled<<" restart_settled="<<first.newly_settled+repeated.newly_settled<<"\n";
}
