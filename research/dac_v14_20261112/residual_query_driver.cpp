#include "h3d_candidate_path.h"
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
struct Node { int32_t x,y,dx,dy,layer; };
struct Edge { uint32_t node;double weight; };
template<class T> T take(std::istream& s){T value{};s.read(reinterpret_cast<char*>(&value),sizeof(value));if(!s)throw std::runtime_error("truncated input");return value;}
void optional(const std::optional<double>& v){if(v)std::cout<<*v;else std::cout<<'-';}
int main(int argc,char** argv) {
    if(argc!=4)throw std::runtime_error("graph cases budget required");
    std::ifstream f(argv[1],std::ios::binary);char magic[8];f.read(magic,8);assert(std::memcmp(magic,"H3DRQ001",8)==0);
    uint32_t n=take<uint32_t>(f);uint64_t m=take<uint64_t>(f);double unit=take<double>(f),span=take<double>(f);
    std::vector<Node> nodes;nodes.reserve(n);for(uint32_t i=0;i<n;++i)nodes.push_back({take<int32_t>(f),take<int32_t>(f),take<int32_t>(f),take<int32_t>(f),take<int32_t>(f)});
    std::vector<std::vector<Edge>> rev(n);
    for(uint64_t i=0;i<m;++i){auto u=take<uint32_t>(f),v=take<uint32_t>(f);double w=take<double>(f);assert(u<n&&v<n&&std::isfinite(w)&&w>=0);rev[v].push_back({u,w});}
    assert(f.peek()==std::char_traits<char>::eof());std::ifstream cases(argv[2]);size_t count;cases>>count;size_t budget=std::stoull(argv[3]);
    std::cout<<std::setprecision(17);
    for(size_t i=0;i<count;++i){
        size_t search,sink,num;int xmin,xmax,ymin,ymax,lmin,lmax;cases>>search>>sink>>xmin>>xmax>>ymin>>ymax>>lmin>>lmax>>num;assert(cases&&sink<n);
        std::unordered_map<size_t,double> seeds;
        auto inside=[&](size_t k){auto a=nodes[k];return a.dx>=xmin&&a.dx<=xmax&&a.dy>=ymin&&a.dy<=ymax&&a.layer>=lmin&&a.layer<=lmax;};
        for(size_t j=0;j<num;++j){size_t k;double t;cases>>k>>t;assert(cases&&k<n&&std::isfinite(t)&&t>=0);if(nodes[k].layer!=nodes[sink].layer)continue;auto old=seeds.find(k);if(old==seeds.end()||t<old->second)seeds[k]=t;}
        for(int mode=0;mode<2;++mode){
            auto expand=[&](size_t k,auto visit){
                if(k==n)return;
                auto s=seeds.find(k);if(s!=seeds.end())visit(size_t(n),s->second,0.);
                for(auto e:rev[k])if(nodes[e.node].layer==nodes[sink].layer&&inside(e.node))visit(size_t(e.node),e.weight,0.);
            };
            auto heuristic=[&](size_t k){
                if(mode==0||k==n||seeds.empty())return 0.;
                double best=std::numeric_limits<double>::infinity();
                for(auto s:seeds){double dist=std::abs(nodes[k].x-nodes[s.first].x)+std::abs(nodes[k].y-nodes[s.first].y);best=std::min(best,s.second+4.*unit*dist/std::max(1.,span));}
                return best;
            };
            auto start=std::chrono::steady_clock::now();auto r=H3dCandidatePath::query(sink,n,budget,16384,65536,expand,heuristic,true);auto elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            std::cout<<"RESULT "<<search<<' '<<mode<<' '<<int(r.stop)<<' '<<r.expansions<<' '<<r.labels<<' '<<r.peak_heap<<' ';optional(r.priced_upper_seconds);std::cout<<' ';optional(r.physical_path_seconds);std::cout<<' ';optional(r.lower_seconds);std::cout<<' '<<elapsed<<' '<<r.edges.size()<<'\n';
            size_t index=0;for(auto e:r.edges)std::cout<<"EDGE "<<search<<' '<<mode<<' '<<index++<<' '<<e.from<<' '<<e.to<<' '<<e.physical_seconds<<' '<<e.toll_seconds<<'\n';
        }
    }
    assert(cases);return 0;
}
