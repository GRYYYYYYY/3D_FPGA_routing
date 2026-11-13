#include "h3d_resumable_delay_search.h"
#include <fstream>
#include <iostream>
#include <cassert>
#include <cstdint>
#include <string>
#include <algorithm>
struct Edge {size_t next; double delay;};
int main(int argc,char**argv) {
 assert(argc==2);std::string dir=argv[1];
 std::ifstream nodes(dir+"/layers.bin",std::ios::binary),edges(dir+"/edges.bin",std::ios::binary),queries(dir+"/queries.txt");
 assert(nodes && edges && queries);
 std::vector<int32_t> layer;int32_t z;while(nodes.read(reinterpret_cast<char*>(&z),4))layer.push_back(z);
 size_t n=layer.size();std::vector<std::vector<Edge>> forward(n),reverse(n);std::vector<bool> crossing(n,false);
 uint32_t u,v;float w;size_t edge_count=0;
 while(edges.read(reinterpret_cast<char*>(&u),4)) {
  assert(edges.read(reinterpret_cast<char*>(&v),4));assert(edges.read(reinterpret_cast<char*>(&w),4));assert(u<n && v<n);
  forward[u].push_back({v,w});reverse[v].push_back({u,w});crossing[u]=crossing[u] || layer[u]!=layer[v];++edge_count;
 }
 size_t endpoint,target,case_id=0;int backwards;
 std::cout<<"case,endpoint,reverse,target,measured,measured_seconds,reference_seconds,settled,stop\n";
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
  H3dResumableDelaySearch state(endpoint,4096,200000,500000);
  H3dResumableDelaySearch::Result result;
  do {result=state.query({n+target},256,terminal,expand);} while(result.stop==H3dResumableDelaySearch::e_stop::QUOTA);
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
  auto measured=state.terminal_distance(n+target);
  assert(std::isfinite(truth));if(measured)assert(std::abs(*measured-truth)<1.e-18);
  assert(result.total_settled<=4096);
  std::cout.precision(17);
  std::cout<<case_id++<<','<<endpoint<<','<<backwards<<','<<target<<','<<bool(measured)<<','<<(measured?*measured:std::numeric_limits<double>::quiet_NaN())<<','<<truth<<','<<result.total_settled<<','<<int(result.stop)<<'\n';
 }
 std::cerr<<"nodes="<<n<<" edges="<<edge_count<<" queries="<<case_id<<'\n';
}
