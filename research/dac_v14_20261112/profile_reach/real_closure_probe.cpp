#include "h3d_reachability.h"
#include <fstream>
#include <iostream>
#include <cstdint>
#include <chrono>
#include <set>
#include <map>
#include <memory>
#include <cassert>
int main(int argc,char**argv) {
 assert(argc==2);std::string dir=argv[1];
 std::ifstream nodes(dir+"/layers.bin",std::ios::binary),edges_file(dir+"/edges.bin",std::ios::binary),queries(dir+"/queries.txt");assert(nodes&&edges_file&&queries);
 std::vector<int32_t> layer;int32_t z;while(nodes.read(reinterpret_cast<char*>(&z),4))layer.push_back(z);
 std::vector<std::pair<size_t,size_t>> planar,crossing;uint32_t u,v;float w;
 while(edges_file.read(reinterpret_cast<char*>(&u),4)) {assert(edges_file.read(reinterpret_cast<char*>(&v),4));assert(edges_file.read(reinterpret_cast<char*>(&w),4));(layer[u]==layer[v]?planar:crossing).emplace_back(u,v);}
 using Clock=std::chrono::steady_clock;
 auto start=Clock::now();H3dReachabilityIndex baseline(layer.size(),planar);double constructor=std::chrono::duration<double>(Clock::now()-start).count();
 H3dReachabilityIndex generation(layer.size(),planar,true);
 std::vector<int> entries,exits;for(auto [a,b]:crossing){entries.push_back(baseline.component(a));exits.push_back(baseline.component(b));}
 auto forward=baseline.mark(entries,true),reverse=baseline.mark(exits,false);
 std::map<std::pair<size_t,int>,std::vector<int>> values;size_t endpoint,target;int backward;
 std::cout<<"endpoint,reverse,layer,closure_size,hash_seconds,generation_seconds\n";
 while(queries>>endpoint>>backward>>target) {
  auto key=std::make_pair(endpoint,backward);if(values.contains(key))continue;
  const auto& allowed=backward?reverse:forward;
  start=Clock::now();auto old=baseline.relevant_components(endpoint,backward,allowed,true);double old_time=std::chrono::duration<double>(Clock::now()-start).count();
  start=Clock::now();auto now=generation.relevant_components(endpoint,backward,allowed,true);double new_time=std::chrono::duration<double>(Clock::now()-start).count();assert(old==now);
  std::cout.precision(9);std::cout<<endpoint<<','<<backward<<','<<layer[endpoint]<<','<<old.size()<<','<<old_time<<','<<new_time<<'\n';values[key]=std::move(old);
 }
 std::map<std::pair<int,int>,std::vector<int>> common;std::map<std::pair<int,int>,size_t> counts;
 for(const auto& [key,val]:values) {
  auto group=std::make_pair(layer[key.first],key.second);
  if(!counts[group]++)common[group]=val;
  else {std::vector<int> intersection;std::set_intersection(common[group].begin(),common[group].end(),val.begin(),val.end(),std::back_inserter(intersection));common[group]=std::move(intersection);}
 }
 std::cerr<<"nodes="<<layer.size()<<" planar_edges="<<planar.size()<<" components="<<baseline.num_components()<<" constructor_seconds="<<constructor<<'\n';
 for(const auto& [key,val]:common)std::cerr<<"layer="<<key.first<<" reverse="<<key.second<<" endpoints="<<counts[key]<<" common_components="<<val.size()<<'\n';
 std::vector<size_t> members(baseline.num_components());for(size_t x=0;x<layer.size();++x)++members[baseline.component(x)];
 std::vector<std::pair<size_t,int>> ranked;for(size_t c=0;c<members.size();++c)ranked.emplace_back(members[c],c);std::sort(ranked.rbegin(),ranked.rend());
 for(size_t i=0;i<std::min(size_t(4),ranked.size());++i)std::cerr<<"large_scc="<<ranked[i].second<<" members="<<ranked[i].first<<'\n';
}
