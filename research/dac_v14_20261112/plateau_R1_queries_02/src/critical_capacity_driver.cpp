#include "critical_capacity_adapter.h"
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>

struct CapacityEdge {uint32_t node;double weight;};
/** @brief Read a little-endian scalar on the explicitly supported x86 host. */
template<class T>T read_scalar(std::istream& stream) {
    T value{};stream.read(reinterpret_cast<char*>(&value),sizeof(value));
    if(!stream)throw std::runtime_error("Truncated input");
    return value;
}
int main(int argc,char** argv) {
    assert(argc==3 || (argc==4 && std::string(argv[3])=="capacity"));std::ifstream input(argv[1],std::ios::binary);
    char magic[8];input.read(magic,8);assert(std::memcmp(magic,"H3DRQ001",8)==0);
    size_t n=read_scalar<uint32_t>(input),m=read_scalar<uint64_t>(input);
    read_scalar<double>(input);read_scalar<double>(input);
    for(size_t i=0;i<5*n;++i)read_scalar<int32_t>(input);
    std::vector<std::vector<CapacityEdge>> reverse(n);
    for(size_t i=0;i<m;++i) {
        auto u=read_scalar<uint32_t>(input),v=read_scalar<uint32_t>(input);auto w=read_scalar<double>(input);
        assert(u<n&&v<n&&std::isfinite(w)&&w>=0.);reverse[v].push_back({u,w});
    }
    assert(input.peek()==std::char_traits<char>::eof());
    std::ifstream cases(argv[2]);size_t count;cases>>count;std::cout<<std::setprecision(17);
    for(size_t i=0;i<count;++i) {
        size_t net,pin,sink,nt,na,nb;cases>>net>>pin>>sink>>nt>>na>>nb;assert(cases&&sink<n);
        std::set<size_t> retained,blocked;std::map<size_t,double> anchors;
        for(size_t j=0;j<nt;++j){size_t node;cases>>node;retained.insert(node);}
        for(size_t j=0;j<na;++j){size_t node;double delay;cases>>node>>delay;assert(retained.count(node));anchors[node]=delay;}
        for(size_t j=0;j<nb;++j){size_t node;cases>>node;blocked.insert(node);}
        assert(cases);
        for(int mode=(argc==4?1:0);mode<2;++mode) {
            auto start=std::chrono::steady_clock::now();
            auto r=query_critical_capacity(n,sink,retained,anchors,blocked,mode,
                [&](size_t node,auto visit){for(auto e:reverse[node])visit(size_t(e.node),e.weight);},
                n+1,m+n+1,2*(m+n+1));
            double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            std::cout<<"RESULT "<<net<<' '<<pin<<' '<<mode<<' '<<int(r.stop)<<' '
                <<r.expansions<<' '<<r.labels<<' '<<r.peak_heap<<' '
                <<r.physical_path_seconds.value_or(-1.)<<' '<<r.lower_seconds.value_or(-1.)<<' '<<elapsed<<' '<<r.edges.size()<<'\n';
            size_t seq=0;for(auto e:r.edges)std::cout<<"EDGE "<<net<<' '<<pin<<' '<<mode<<' '<<seq++<<' '<<e.from<<' '<<e.to<<' '<<e.physical_seconds<<'\n';
        }
    }
}
