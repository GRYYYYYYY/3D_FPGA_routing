/** @file Independent full Dijkstra oracle; does not include production search code.
 * Graph export: int32 layers; uint32 source/dest + float32 switch delay.
 * Forward answers stop at a crossing entry. Reverse answers include one crossing
 * edge into the sink layer. Physical RC must be zero, as certified by exporter.
 */
#include <algorithm>
#include <bit>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <string>
#include <vector>
struct Edge { uint32_t next; float delay; };
int main(int argc, char** argv) {
    assert(argc == 3 && std::endian::native == std::endian::little);
    std::ifstream nodes(std::string(argv[1])+"/layers.bin", std::ios::binary);
    std::ifstream edges(std::string(argv[1])+"/edges.bin", std::ios::binary), requests(argv[2]);
    assert(nodes && edges && requests);
    std::vector<int32_t> layers; int32_t layer;
    while (nodes.read(reinterpret_cast<char*>(&layer),4)) layers.push_back(layer);
    assert(nodes.eof() && nodes.gcount()==0 && !layers.empty());
    size_t n=layers.size(); std::vector<std::vector<Edge>> forward(n), reverse(n);
    uint32_t u,v; float w; size_t edge_count=0;
    while (edges.read(reinterpret_cast<char*>(&u),4)) {
        assert(edges.read(reinterpret_cast<char*>(&v),4));
        assert(edges.read(reinterpret_cast<char*>(&w),4));
        assert(u<n && v<n && std::isfinite(w) && w>=0);
        forward[u].push_back({v,w}); reverse[v].push_back({u,w}); ++edge_count;
    }
    assert(edges.eof() && edges.gcount()==0);
    using Key=std::pair<uint32_t,int>;
    std::map<Key,std::set<uint32_t>> groups;
    int backwards;
    while (requests>>u>>backwards>>v) {
        assert(u<n && v<n && (backwards==0 || backwards==1)); groups[{u,backwards}].insert(v);
    }
    assert(requests.eof() && !groups.empty());
    size_t group_count=0,total_settled=0,answers=0;
    std::cout<<"endpoint,reverse,target,seconds\n"; std::cout.precision(17);
    for (const auto& [key,targets]:groups) {
        auto [endpoint,back]=key;
        std::vector<double> distance(n,std::numeric_limits<double>::infinity());
        using Item=std::pair<double,uint32_t>;
        std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;
        distance[endpoint]=0;heap.push({0,endpoint});size_t settled=0;
        const auto& graph=back?reverse:forward;
        while (!heap.empty()) {
            auto [cost,node]=heap.top();heap.pop();
            if (cost!=distance[node]) continue;
            ++settled;
            for (const Edge& edge:graph[node]) {
                if (layers[edge.next]!=layers[endpoint]) continue;
                double next=cost+double(edge.delay);
                if (next<distance[edge.next]) {distance[edge.next]=next;heap.push({next,edge.next});}
            }
        }
        for (uint32_t target:targets) {
            double answer=std::numeric_limits<double>::infinity();bool crossing=false;
            for (const Edge& edge:forward[target]) if (layers[target]!=layers[edge.next]) {
                crossing=true;
                if (back && layers[edge.next]==layers[endpoint]) answer=std::min(answer,double(edge.delay)+distance[edge.next]);
            }
            assert(crossing);
            if (!back && layers[target]==layers[endpoint]) answer=distance[target];
            std::cout<<endpoint<<','<<back<<','<<target<<','<<answer<<'\n';++answers;
        }
        total_settled+=settled;++group_count;
        if (group_count%25==0) std::cerr<<"groups="<<group_count<<'/'<<groups.size()<<" settled="<<total_settled<<'\n';
    }
    std::cerr<<"complete nodes="<<n<<" edges="<<edge_count<<" groups="<<group_count<<" answers="<<answers<<" settled="<<total_settled<<'\n';
}
