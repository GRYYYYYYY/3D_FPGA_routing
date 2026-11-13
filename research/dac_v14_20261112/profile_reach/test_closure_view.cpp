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
 size_t checks=0, intersections=0;
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
   auto forward_allowed=old.mark(seeds,true),reverse_allowed=old.mark(seeds,false);
   size_t cap=q%3==0?0:(q%3==1?7:10000);
   generation.configure_shared_closures(forward_allowed,reverse_allowed,cap,8,1,true);
   assert(generation.shared_entries()<=cap);
   auto shared=generation.shared_relevant_components(root,backwards);
   auto view=generation.shared_relevant_view(root,backwards);
   // Owned masks cannot be invalidated by caller mutation after configuration.
   forward_allowed.assign(n,false);reverse_allowed.assign(n,false);
   assert(shared==generation.shared_relevant_components(root,backwards));
   std::vector<bool> seen(n,false);std::vector<size_t> queue;
   if(allowed[old.component(root)]){queue.push_back(root);seen[root]=true;}
   for(size_t i=0;i<queue.size();++i)for(size_t next:(backwards?reverse:forward)[queue[i]])
    if(allowed[old.component(next)] && !seen[next]){seen[next]=true;queue.push_back(next);}
   std::set<int> components;for(size_t vertex:queue)components.insert(old.component(vertex));
   std::vector<int> truth(components.begin(),components.end());assert(a==truth && b==truth && shared==truth);++checks;
   assert(view.materialize()==truth);
   for(int id=-1;id<=int(old.num_components());++id) {
    assert(view.intersects({id})==components.contains(id));++intersections;
   }
   std::vector<int> targets;bool expected=false;
   for(int i=0;i<10;++i){int id=int(rng()%(old.num_components()+2))-1;targets.push_back(id);expected|=components.contains(id);}
   assert(view.intersects(targets)==expected);assert(!view.intersects({}));++intersections;
   // A stored snapshot remains valid after masks and owned hub sets are replaced.
   generation.configure_shared_closures(std::vector<bool>(old.num_components(),false),std::vector<bool>(old.num_components(),false),0,0,1,true);
   assert(view.materialize()==truth);assert(view.intersects(targets)==expected);
  }
 }
 auto snapshot=[] {
  H3dReachabilityIndex index(6,{{0,1},{1,0},{1,2},{2,3},{3,2},{3,4},{4,5}},true);
  std::vector<bool> all(index.num_components(),true);index.configure_shared_closures(all,all,100,8,1,true);
  auto view=index.shared_relevant_view(0,false);auto truth=view.materialize();
  return std::make_pair(std::move(view),std::move(truth));
 }();
 assert(snapshot.first.materialize()==snapshot.second);
 std::cout<<"view_intersection_checks="<<intersections<<" snapshot_after_reconfigure_and_owner_destruction=passed ";
 std::cout<<"view_closure_oracle_checks="<<checks<<" small_epoch_generations=1000 including_rollover=1\n";
}
