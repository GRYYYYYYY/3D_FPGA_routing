#include "h3d_delay_frontier_cache.h"
#include <fstream>
#include <iostream>
#include <cassert>
#include <cstdint>
#include <string>
#include <algorithm>
#include <map>
#include <memory>
struct Edge {size_t next; double delay;};
int main(int argc,char**argv) {
 assert(argc==3);std::string dir=argv[1];size_t slots=std::stoul(argv[2]);
 std::ifstream nodes(dir+"/layers.bin",std::ios::binary),edges(dir+"/edges.bin",std::ios::binary),queries(dir+"/queries.txt");
 assert(nodes && edges && queries);
 std::vector<int32_t> layer;int32_t z;while(nodes.read(reinterpret_cast<char*>(&z),4))layer.push_back(z);
 size_t n=layer.size();std::vector<std::vector<Edge>> forward(n),reverse(n);std::vector<bool> crossing(n,false);
 uint32_t u,v;float w;size_t edge_count=0;
 while(edges.read(reinterpret_cast<char*>(&u),4)) {
  assert(edges.read(reinterpret_cast<char*>(&v),4));assert(edges.read(reinterpret_cast<char*>(&w),4));assert(u<n && v<n);
  forward[u].push_back({v,w});reverse[v].push_back({u,w});crossing[u]=crossing[u] || layer[u]!=layer[v];++edge_count;
 }
 H3dDelayFrontierCache cache({slots,16,200000,500000,4096,16*4096});
 std::map<size_t,size_t> charged;
 size_t endpoint,target,case_id=0;int backwards;
 std::cout<<"case,endpoint,reverse,target,measured,measured_seconds,reference_seconds,settled,newly_settled,stop\n";
 while(queries>>endpoint>>backwards>>target) {
  assert(crossing[target]);int die=layer[endpoint];
  auto terminal=[&](size_t x){return x>=n;};
  auto expand=[&](size_t x,auto visit) {
   if(!backwards && crossing[x])visit(n+x,0.);
   for(auto e:backwards?reverse[x]:forward[x]) {
    if(backwards && layer[e.next]!=layer[x])visit(n+e.next,e.delay);
    else if(layer[e.next]==die)visit(e.next,e.delay);
   }
  };
  size_t key=2*endpoint+backwards,newly=0;
  H3dDelayFrontierCache::Result result;
  do {
   result=cache.query(key,endpoint,{n+target},256,terminal,expand);
   newly+=result.newly_settled;
  } while(result.stop==H3dDelayFrontierCache::Stop::SEARCH && result.search_stop==H3dResumableDelaySearch::e_stop::QUOTA);
  charged[key]+=newly;
  // Independent reference: ordinary same-layer graph, no synthetic terminals,
  // record crossing-edge identities directly and run to completion.
  std::vector<double> distance(n,INFINITY);using Item=std::pair<double,size_t>;
  std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;
  distance[endpoint]=0;heap.emplace(0,endpoint);double truth=INFINITY;
  while(!heap.empty()) {
   auto [cost,x]=heap.top();heap.pop();if(cost!=distance[x])continue;
   if(!backwards && x==target)truth=std::min(truth,cost);
   for(auto e:backwards?reverse[x]:forward[x]) {
    if(backwards && layer[e.next]!=layer[x]) {if(e.next==target)truth=std::min(truth,cost+e.delay);continue;}
    if(layer[e.next]!=die)continue;
    if(cost+e.delay<distance[e.next]){distance[e.next]=cost+e.delay;heap.emplace(distance[e.next],e.next);}
   }
  }
  auto measured=result.distances.at(0);
  assert(std::isfinite(truth));if(measured)assert(std::abs(*measured-truth)<1.e-18);
  assert(charged[key]<=4096 && cache.stats().live_states<=slots);
  std::cout.precision(17);
  std::cout<<case_id++<<','<<endpoint<<','<<backwards<<','<<target<<','<<bool(measured)<<','<<(measured?*measured:std::numeric_limits<double>::quiet_NaN())<<','<<truth<<','<<charged[key]<<','<<newly<<','<<int(result.stop)<<'\n';
 }
 std::cerr<<"nodes="<<n<<" edges="<<edge_count<<" queries="<<case_id<<" total_work="<<cache.stats().work<<" evictions="<<cache.stats().evictions<<" restarts="<<cache.stats().restarts<<'\n';
}
