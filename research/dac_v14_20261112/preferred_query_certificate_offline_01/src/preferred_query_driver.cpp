#include "preferred_query_adapter.h"
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
struct Node {int32_t x,y,dx,dy,layer;};
struct Edge {uint32_t node;double weight;};
template<class T> T take(std::istream& s) {T v{};s.read(reinterpret_cast<char*>(&v),sizeof(v));if(!s)throw std::runtime_error("truncated graph");return v;}
void optional(const std::optional<double>& v) {if(v)std::cout<<*v;else std::cout<<'-';}
int main(int argc,char** argv) {
    if(argc!=4)throw std::invalid_argument("graph,cases,budget required");
    std::ifstream f(argv[1],std::ios::binary);char magic[8];f.read(magic,8);assert(std::memcmp(magic,"H3DRQ001",8)==0);
    auto n=take<uint32_t>(f);auto m=take<uint64_t>(f);double unit=take<double>(f),span=take<double>(f);
    std::vector<Node> nodes;nodes.reserve(n);
    for(uint32_t i=0;i<n;++i)nodes.push_back({take<int32_t>(f),take<int32_t>(f),take<int32_t>(f),take<int32_t>(f),take<int32_t>(f)});
    std::vector<std::vector<Edge>> rev(n);
    for(uint64_t i=0;i<m;++i){auto u=take<uint32_t>(f),v=take<uint32_t>(f);auto w=take<double>(f);assert(u<n&&v<n&&std::isfinite(w)&&w>=0);rev[v].push_back({u,w});}
    assert(f.peek()==std::char_traits<char>::eof());std::ifstream cases(argv[2]);size_t count;cases>>count;std::cout<<std::setprecision(17);
    for(size_t i=0;i<count;++i) {
        size_t search,sink,num,np;int xmin,xmax,ymin,ymax,lmin,lmax;
        cases>>search>>sink>>xmin>>xmax>>ymin>>ymax>>lmin>>lmax>>num>>np;assert(cases&&sink<n);
        std::vector<std::pair<size_t,double>> seeds;for(size_t j=0;j<num;++j){size_t k;double t;cases>>k>>t;assert(cases);seeds.emplace_back(k,t);}
        std::set<size_t> preferred;for(size_t j=0;j<np;++j){size_t k;cases>>k;assert(cases&&k<n);preferred.insert(k);}
        auto inside=[&](size_t k){auto a=nodes[k];return a.dx>=xmin&&a.dx<=xmax&&a.dy>=ymin&&a.dy<=ymax&&a.layer>=lmin&&a.layer<=lmax;};
        auto layer=[&](size_t k){return nodes[k].layer;};
        auto reverse=[&](size_t k,auto visit){for(auto e:rev[k])visit(size_t(e.node),e.weight);};
        auto order=[&](size_t k,size_t s){return 4.*unit*(std::abs(nodes[k].x-nodes[s].x)+std::abs(nodes[k].y-nodes[s].y))/std::max(1.,span);};
        for(int mode=0;mode<3;++mode){
            auto start=std::chrono::steady_clock::now();auto a=query_preferred(n,sink,seeds,preferred,layer,inside,reverse,order,mode!=0,mode==2,std::stoull(argv[3]));
            auto& r=a.result;double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            std::cout<<"RESULT "<<search<<' '<<mode<<' '<<int(r.stop)<<' '<<r.expansions<<' '<<r.labels<<' '<<r.peak_heap<<' ';optional(r.priced_upper_seconds);std::cout<<' ';optional(r.physical_path_seconds);std::cout<<' ';optional(r.lower_seconds);std::cout<<' '<<elapsed<<' '<<r.edges.size()<<' '<<a.seed_floor<<' '<<a.admissible_seeds<<'\n';
            size_t index=0;for(auto e:r.edges)std::cout<<"EDGE "<<search<<' '<<mode<<' '<<index++<<' '<<e.from<<' '<<e.to<<' '<<e.physical_seconds<<' '<<e.toll_seconds<<'\n';
        }
    }
    assert(cases);return 0;
}
