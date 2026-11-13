#include "h3d_feedback_policy.h"
#include "h3d_partition_dp.h"
#include <cassert>
#include <random>
int main() {
 assert(!h3d_feedback_due(3,1,3,true,0,0));
 assert(h3d_feedback_due(4,1,3,true,0,0));
 assert(!h3d_feedback_due(9,1,3,false,.149,.249));
 assert(h3d_feedback_due(9,1,3,false,.15,0));
 assert(h3d_feedback_due(9,1,3,false,0,.25));
 assert(!h3d_accept_refresh(100,95,.05));
 assert(h3d_accept_refresh(100,94,.05));
 assert(!h3d_accept_refresh(0,0,.05));
 assert(h3d_accept_refresh(INFINITY,100,.05));
 assert(!h3d_accept_refresh(INFINITY,INFINITY,.05));
 std::vector<t_h3d_plan_leaf> leaves={{1,0,0,{{0,0},{1,10}}},{2,1,0,{{0,10},{1,0}}}};
 assert(h3d_assignment_cost(leaves,{20,20},{{1,0},{2,0}})==30);
 assert(h3d_assignment_cost(leaves,{20,20},{{1,0},{2,1}})==40);
 assert(!std::isfinite(h3d_assignment_cost(leaves,{20,20},{{1,0}})));
 std::mt19937 rng(20261113);
 for(int t=0;t<500;++t) {
  int n=1+rng()%8,k=1+rng()%5;std::vector<double> opening(k);
  for(auto& x:opening)x=rng()%12;
  leaves.clear();
  for(int i=0;i<n;++i){t_h3d_plan_leaf leaf{i,int(rng()%20),int(rng()%20),{}};for(int c=0;c<k;++c)if(rng()%5)leaf.candidates.push_back({size_t(c),double(rng()%15)});leaves.push_back(leaf);}
  auto optimum=h3d_plan_partition(leaves,opening);
  assert(h3d_assignment_cost(leaves,opening,optimum.assignment)==optimum.cost);
 }
}
