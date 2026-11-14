#include "critical_capacity_adapter.h"
#include <cassert>
#include <iostream>
#include <random>

/** @brief Independent forward Floyd tests retained-tree and capacity constraints. */
int main() {
    std::mt19937 random(94171);size_t checks=0,paths=0,unreachable=0;
    for(size_t trial=0;trial<1000;++trial) {
        size_t n=3+random()%11,sink=random()%n;
        std::set<size_t> retained,blocked;std::map<size_t,double> anchors;
        std::vector<std::vector<std::pair<size_t,double>>> reverse(n);
        std::vector<std::tuple<size_t,size_t,double>> edges;
        for(size_t i=0;i<n;++i) {
            if(random()%3==0){retained.insert(i);if(random()%2)anchors[i]=random()%8;}
            if(random()%4==0)blocked.insert(i);
        }
        for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)if(random()%4==0) {
            double w=random()%5;edges.emplace_back(u,v,w);reverse[v].emplace_back(u,w);
        }
        for(int mode=0;mode<2;++mode) {
            double inf=std::numeric_limits<double>::infinity();
            std::vector<std::vector<double>> d(n+1,std::vector<double>(n+1,inf));
            for(size_t i=0;i<=n;++i)d[i][i]=0.;
            for(auto [node,delay]:anchors)if(!mode||!blocked.count(node))d[n][node]=delay;
            for(auto [u,v,w]:edges)if(!retained.count(v) && (!mode || (!blocked.count(u)&&!blocked.count(v))))d[u][v]=std::min(d[u][v],w);
            for(size_t k=0;k<=n;++k)for(size_t u=0;u<=n;++u)for(size_t v=0;v<=n;++v)d[u][v]=std::min(d[u][v],d[u][k]+d[k][v]);
            auto r=query_critical_capacity(n,sink,retained,anchors,blocked,mode,
                [&](size_t node,auto visit){for(auto [u,w]:reverse[node])visit(u,w);},n+1,n*n+n+1,2*(n*n+n+1));
            ++checks;double oracle=d[n][sink];
            if(std::isfinite(oracle)) {
                ++paths;assert(r.stop==H3dCandidatePath::Stop::EXACT&&r.physical_path_seconds&&r.lower_seconds);
                assert(*r.physical_path_seconds==oracle&&*r.lower_seconds==oracle);
                double sum=0.;size_t node=sink;
                for(auto e:r.edges) {
                    assert(e.from==node&&e.toll_seconds==0.);sum+=e.physical_seconds;node=e.to;
                    assert(!mode||!blocked.count(e.from));
                    if(e.to==n)assert(anchors.at(e.from)==e.physical_seconds);
                    else {
                        assert(!retained.count(e.from)&&(!mode||!blocked.count(e.to)));
                        bool found=false;for(auto [u,w]:reverse[e.from])found|=u==e.to&&w==e.physical_seconds;assert(found);
                    }
                }
                assert(node==n&&sum==oracle);
            } else {
                ++unreachable;assert(r.stop==H3dCandidatePath::Stop::UNREACHABLE&&!r.physical_path_seconds&&r.lower_seconds&&std::isinf(*r.lower_seconds));
            }
        }
    }
    assert(paths&&unreachable);std::cout<<"checks="<<checks<<" paths="<<paths<<" unreachable="<<unreachable<<'\n';
}
