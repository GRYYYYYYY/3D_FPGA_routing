#include "h3d_independent_plan.h"
#include <cassert>
#include <random>
#include <functional>
int main() {
 std::vector<t_h3d_plan_leaf> leaves={{1,0,0,{{0,0},{1,10}}},{2,1,0,{{0,10},{1,0}}}};
 auto independent=h3d_plan_independent(leaves,{20,20});
 assert(independent.cost==40 && independent.groups==2);
 assert(h3d_plan_partition(leaves,{20,20}).cost==30);
 leaves[0].candidates.clear();
 assert(!std::isfinite(h3d_plan_independent(leaves,{20,20}).cost));
 assert(h3d_plan_independent({},{}).cost==0);
 std::mt19937 rng(20261112);
 for(int t=0;t<250;++t) {
  int n=1+rng()%5,k=1+rng()%4;std::vector<double> opening(k);
  for(auto& x:opening)x=rng()%12;
  leaves.clear();
  for(int i=0;i<n;++i){t_h3d_plan_leaf leaf{i,i,0,{}};for(int c=0;c<k;++c)if(rng()%5)leaf.candidates.push_back({size_t(c),double(rng()%15)});leaves.push_back(leaf);}
  double oracle=std::numeric_limits<double>::infinity();
  std::function<void(int,double)> enumerate=[&](int i,double total){if(i==n){oracle=std::min(oracle,total);return;}for(auto c:leaves[i].candidates)enumerate(i+1,total+opening[c.channel]+c.branch_cost);};
  enumerate(0,0);auto a=h3d_plan_independent(leaves,opening);assert(a.cost==oracle);
  assert(std::isfinite(a.cost)==std::isfinite(h3d_plan_partition(leaves,opening).cost));
 }
}
