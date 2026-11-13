#include "h3d_reachability.h"
#include "h3d_visit_epoch.h"
#include <random>
#include <cassert>
#include <iostream>
#include <set>
int main() {
 std::mt19937 rng(20261112); H3dVisitEpoch<uint8_t> small(37);
 for(size_t trial=0;trial<1000;++trial) {
  small.begin();std::set<size_t> seen;
  for(size_t i=0;i<200;++i){size_t node=rng()%37;assert(small.insert(node)==seen.insert(node).second);}
 }
 size_t checks=0;
 for(size_t trial=0;trial<200;++trial) {
  size_t n=5+rng()%70;std::vector<std::pair<size_t,size_t>> edges;
  std::vector<std::vector<size_t>> forward(n),reverse(n);
  for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)if(rng()%23==0){edges.emplace_back(u,v);forward[u].push_back(v);reverse[v].push_back(u);}
  H3dReachabilityIndex old(n,edges),generation(n,edges,true);
  for(size_t u=0;u<n;++u)assert(old.component(u)==generation.component(u));
  for(size_t q=0;q<100;++q) {
   bool backwards=rng()%2;size_t root=rng()%n;
   std::vector<int> seeds;for(size_t c=0;c<old.num_components();++c)if(rng()%3==0)seeds.push_back(c);
   auto allowed=old.mark(seeds,!backwards);
   auto a=old.relevant_components(root,backwards,allowed,true);
   auto b=generation.relevant_components(root,backwards,allowed,true);
   std::vector<bool> seen(n,false);std::vector<size_t> queue;
   if(allowed[old.component(root)]){queue.push_back(root);seen[root]=true;}
   for(size_t i=0;i<queue.size();++i)for(size_t next:(backwards?reverse:forward)[queue[i]])
    if(allowed[old.component(next)] && !seen[next]){seen[next]=true;queue.push_back(next);}
   std::set<int> components;for(size_t vertex:queue)components.insert(old.component(vertex));
   std::vector<int> truth(components.begin(),components.end());assert(a==truth && b==truth);++checks;
  }
 }
 std::cout<<"closure_oracle_checks="<<checks<<" small_epoch_generations=1000 including_rollover=1\n";
}
