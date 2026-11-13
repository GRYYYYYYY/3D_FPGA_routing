#include "../src/vpr/src/route/h3d_persistent_bidirectional.h"
#include "../src/vpr/src/route/h3d_delay_search.h"
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
 assert(argc==3);std::string dir=argv[1];size_t slots=std::stoul(argv[2]);assert(slots>0);
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
 struct State {std::unique_ptr<H3dPersistentBidirectional> search;size_t used;};
 std::map<Key,State> states;std::map<Key,std::unordered_map<size_t,double>> measured;size_t tick=0,evictions=0,restarts=0;
 std::map<Key,size_t> charged;
 std::map<Key,std::unordered_map<size_t,double>> oracle;size_t exported=0,certified=0;
 H3dDelaySearch original(2*n);
 size_t endpoint,target,case_id=0,original_work=0,targeted_work=0;
 int backwards;
 std::cout<<"case,endpoint,reverse,target,original_measured,original_seconds,targeted_measured,targeted_seconds,original_new_settled,targeted_new_settled,targeted_endpoint_settled,stop\n";
 std::vector<std::tuple<size_t,int,size_t>> requests;while(queries>>endpoint>>backwards>>target)requests.emplace_back(endpoint,backwards,target);
 for(size_t repeat=0;repeat<3;++repeat)for(auto request:requests) {
  std::tie(endpoint,backwards,target)=request;
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
  auto incoming=[&](size_t x,auto visit) {
   if(x>=n) {
    size_t entry=x-n;
    if(!backwards)visit(entry,0.);
    else for(auto e:forward[entry])if(layer[e.next]==die && layer[e.next]!=layer[entry])visit(e.next,e.delay);
    return;
   }
   for(auto e:backwards?forward[x]:reverse[x])if(layer[e.next]==die)visit(e.next,e.delay);
  };
  if(!states.contains(key)) {
   if(states.size()>=slots) {
    auto victim=std::min_element(states.begin(),states.end(),[](const auto&a,const auto&b){return a.second.used<b.second.used;});states.erase(victim);++evictions;
   }
   restarts+=charged[key]>0;states.emplace(key,State{std::make_unique<H3dPersistentBidirectional>(endpoint),0});
  }
  states.at(key).used=++tick;
  auto answer=states.at(key).search->query(n+target,std::min(size_t(256),4096-charged[key]),200000,500000,terminal,all_expand,incoming);
  if(!oracle.contains(key)) {
   auto full=original.query(endpoint,2*n,terminal,all_expand);assert(!full.budget_exhausted);
   oracle.emplace(key,std::unordered_map<size_t,double>(full.terminals.begin(),full.terminals.end()));
  }
  if(answer.exact) {auto truth=oracle.at(key).find(n+target);assert(truth!=oracle.at(key).end());assert(std::abs(truth->second-*answer.exact)<1e-18);}
  for(auto [raw,cost]:answer.new_terminals) {auto truth=oracle.at(key).find(raw);assert(truth!=oracle.at(key).end());assert(std::abs(truth->second-cost)<1e-18);++certified;}
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
          <<" slots="<<slots<<" evictions="<<evictions<<" restarts="<<restarts<<" exported_labels="<<exported<<" certified_crossing_distances="<<certified<<" original_work="<<original_work<<" targeted_work="<<targeted_work<<'\n';
}
