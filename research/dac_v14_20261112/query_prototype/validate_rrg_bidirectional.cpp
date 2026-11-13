#include "h3d_bidirectional_delay.h"
#include "h3d_delay_search.h"
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
 using Key=std::pair<size_t,int>;
 std::map<Key,std::unordered_map<size_t,double>> cached;
 std::map<Key,size_t> charged;
 H3dDelaySearch original(2*n);
 size_t endpoint,target,case_id=0,original_work=0,targeted_work=0;
 int backwards;
 std::cout<<"case,endpoint,reverse,target,original_measured,original_seconds,targeted_measured,targeted_seconds,original_new_settled,targeted_new_settled,targeted_endpoint_settled,stop\n";
 while(queries>>endpoint>>backwards>>target) {
  assert(crossing[target]);int die=layer[endpoint];Key key{endpoint,backwards};
  auto terminal=[&](size_t x){return x>=n;};
  auto all_expand=[&](size_t x,auto visit) {
   if(!backwards && crossing[x])visit(n+x,0.);
   for(auto e:backwards?reverse[x]:forward[x]) {
    if(backwards && layer[e.next]!=layer[x])visit(n+e.next,e.delay);
    else if(layer[e.next]==die)visit(e.next,e.delay);
   }
  };
  size_t original_new=0;
  if(!cached.contains(key)) {
   auto r=original.query(endpoint,4096,terminal,all_expand);original_new=r.settled;
   cached.emplace(key,std::unordered_map<size_t,double>(r.terminals.begin(),r.terminals.end()));
  }
  // Only the requested synthetic terminal is retained. Other crossing
  // terminals are dead ends and cannot lie on a path to this goal.
  auto outgoing=[&](size_t x,auto visit) {
   if(x>=n)return;
   if(!backwards && x==target)visit(n+target,0.);
   for(auto e:backwards?reverse[x]:forward[x]) {
    if(backwards && layer[e.next]!=layer[x]) {if(e.next==target)visit(n+target,e.delay);}
    else if(layer[e.next]==die)visit(e.next,e.delay);
   }
  };
  auto incoming=[&](size_t x,auto visit) {
   if(x>=n) {
    if(!backwards)visit(target,0.);
    else for(auto e:forward[target])if(layer[e.next]==die && layer[e.next]!=layer[target])visit(e.next,e.delay);
    return;
   }
   for(auto e:backwards?forward[x]:reverse[x])if(layer[e.next]==die)visit(e.next,e.delay);
  };
  auto answer=H3dBidirectionalDelay::query(endpoint,n+target,4096-charged[key],200000,500000,outgoing,incoming);
  size_t newly=answer.forward_settled+answer.reverse_settled;
  charged[key]+=newly;assert(charged[key]<=4096);
  original_work+=original_new;targeted_work+=newly;
  const auto& values=cached.at(key);auto original_value=values.find(n+target);
  std::cout.precision(17);
  std::cout<<case_id++<<','<<endpoint<<','<<backwards<<','<<target<<','<<(original_value!=values.end())<<','
           <<(original_value!=values.end()?original_value->second:NAN)<<','<<bool(answer.exact)<<','
           <<answer.exact.value_or(NAN)<<','<<original_new<<','<<newly<<','<<charged[key]<<','<<int(answer.stop)<<'\n';
 }
 std::cerr<<"nodes="<<n<<" edges="<<edge_count<<" requests="<<case_id<<" endpoint_keys="<<cached.size()
          <<" original_work="<<original_work<<" targeted_work="<<targeted_work<<'\n';
}
