#include "tree_preferred_query_adapter.h"
#include "preferred_query_adapter.h"
#include "tree_lower_audit.h"
#include <cassert>
#include <iostream>
#include <random>

/** @brief Forward phase-graph Floyd independently checks all four reverse models.
 * Terminal-tree semantics forbid incoming physical edges into retained nodes
 * in the forward graph. Actual queued seeds may start there. Random inherited
 * masks model preverified tree ancestry; real ancestry is checked separately.
 */
int main() {
    std::mt19937 rng(73191);
    size_t checks=0,exact=0,storage=0,controls=0,paths=0,inherited_paths=0;
    for(size_t trial=0;trial<600;++trial) {
        size_t n=4+rng()%9,sink=rng()%n;
        std::vector<int> layers(n);std::vector<bool> allowed(n);
        std::set<size_t> tree,inherited,preferred;
        for(size_t i=0;i<n;++i) {
            layers[i]=rng()%2;allowed[i]=rng()%5!=0;
            if(rng()%3==0)tree.insert(i);
            if(rng()%3==0)preferred.insert(i);
        }
        allowed[sink]=true;
        std::vector<std::vector<std::pair<size_t,double>>> rev(n);
        std::vector<std::tuple<size_t,size_t,double>> edges;
        for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)if(rng()%4==0) {
            double w=rng()%5;rev[v].emplace_back(u,w);edges.emplace_back(u,v,w);
        }
        std::vector<std::pair<size_t,double>> seeds;
        for(size_t i=0;i<n;++i)if(rng()%2==0) {
            seeds.emplace_back(i,double(rng()%5));tree.insert(i);
            if(rng()%2==0)inherited.insert(i);
            if(rng()%3==0)seeds.emplace_back(i,double(rng()%9));
        }
        auto layer=[&](size_t i){return layers[i];};
        auto inside=[&](size_t i){return allowed[i];};
        auto reverse=[&](size_t i,auto visit){for(auto [u,w]:rev[i])visit(u,w);};
        auto order=[&](size_t i,size_t s){return double((i+3*s)%7)*11.;};
        struct AuditNode {int dx,dy,layer;};
        struct AuditEdge {size_t node;double weight;};
        std::vector<AuditNode> audit_nodes;
        std::vector<std::vector<AuditEdge>> audit_reverse(n);
        for(size_t i=0;i<n;++i) {
            audit_nodes.push_back({allowed[i]?0:-1,0,layers[i]});
            for(auto [u,w]:rev[i])audit_reverse[i].push_back({u,w});
        }
        for(int mode=0;mode<4;++mode) {
            const size_t size=2*n+1;
            double inf=std::numeric_limits<double>::infinity();
            std::vector<std::vector<double>> dist(size,std::vector<double>(size,inf));
            for(size_t i=0;i<size;++i)dist[i][i]=0.;
            for(auto [seed,delay]:seeds)if(allowed[seed]) {
                if(layers[seed]!=layers[sink])dist[2*n][seed]=std::min(dist[2*n][seed],delay);
                else if((mode&1) && inherited.count(seed))dist[2*n][seed+n]=std::min(dist[2*n][seed+n],delay);
            }
            for(auto [u,v,w]:edges)if(allowed[u]&&allowed[v] && !((mode&2)&&tree.count(v))) {
                if(layers[u]==layers[v]) {
                    size_t phase=layers[u]==layers[sink]?n:0;
                    dist[u+phase][v+phase]=std::min(dist[u+phase][v+phase],w);
                } else if(layers[u]!=layers[sink]&&layers[v]==layers[sink]&&preferred.count(u))
                    dist[u][v+n]=std::min(dist[u][v+n],w);
            }
            for(size_t k=0;k<size;++k)for(size_t i=0;i<size;++i)for(size_t j=0;j<size;++j)
                dist[i][j]=std::min(dist[i][j],dist[i][k]+dist[k][j]);
            double oracle=dist[2*n][sink+n];
            for(size_t budget:{size_t(0),size_t(2),size_t(10000)})for(bool limited:{false,true}) {
                auto a=query_tree_preferred(n,sink,seeds,preferred,tree,inherited,mode&1,mode&2,
                    layer,inside,reverse,order,true,false,budget,limited?3:16384,limited?6:65536,edges,true);
                auto& r=a.result;++checks;assert(r.expansions<=budget);
                verify_tree_lower(audit_nodes,audit_reverse,sink,seeds,preferred,tree,inherited,
                    mode,0,0,0,0,0,1,r.lower_seconds);
                if(r.lower_seconds)assert(*r.lower_seconds<=oracle);
                if(r.priced_upper_seconds) {
                    ++paths;assert(*r.priced_upper_seconds>=oracle);
                    double value=0.;size_t cursor=sink,crosses=0;
                    for(auto e:r.edges) {
                        assert(e.from==cursor);cursor=e.to;value+=e.physical_seconds;assert(e.toll_seconds==0.);
                        if(e.to==n) {
                            assert(allowed[e.from]);
                            bool found=false;for(auto [s,d]:seeds)found|=(s==e.from&&d==e.physical_seconds);assert(found);
                        } else {
                            assert(allowed[e.from]&&allowed[e.to]);assert(!(mode&2)||!tree.count(e.from));
                            bool found=false;for(auto [u,w]:rev[e.from])found|=u==e.to&&w==e.physical_seconds;assert(found);
                            if(layers[e.from]!=layers[e.to]){++crosses;assert(preferred.count(e.to));}
                        }
                    }
                    assert(cursor==n&&value==*r.physical_path_seconds&&value==*r.priced_upper_seconds);
                    size_t anchor=r.edges.back().from;
                    assert(crosses==1 || (crosses==0&&(mode&1)&&inherited.count(anchor)));
                    inherited_paths+=crosses==0;
                }
                if(r.stop==H3dCandidatePath::Stop::EXACT){++exact;assert(r.priced_upper_seconds&&*r.priced_upper_seconds==oracle&&r.lower_seconds&&*r.lower_seconds==oracle);}
                if(r.stop==H3dCandidatePath::Stop::UNREACHABLE)assert(!std::isfinite(oracle)&&!r.priced_upper_seconds);
                if(r.stop==H3dCandidatePath::Stop::MEMORY_LIMIT){++storage;assert(!r.lower_seconds);}
                if(!limited&&budget==10000)assert((!std::isfinite(oracle)&&r.stop==H3dCandidatePath::Stop::UNREACHABLE)||r.priced_upper_seconds);
                if(mode==0) {
                    auto old=query_preferred(n,sink,seeds,preferred,layer,inside,reverse,order,true,false,budget,limited?3:16384,limited?6:65536,edges,true);
                    const auto& x=old.result;++controls;
                    assert(x.stop==r.stop&&x.expansions==r.expansions&&x.labels==r.labels&&x.peak_heap==r.peak_heap);
                    assert(x.priced_upper_seconds==r.priced_upper_seconds&&x.lower_seconds==r.lower_seconds&&x.edges.size()==r.edges.size());
                    for(size_t i=0;i<x.edges.size();++i)assert(x.edges[i].from==r.edges[i].from&&x.edges[i].to==r.edges[i].to&&x.edges[i].physical_seconds==r.edges[i].physical_seconds);
                }
            }
        }
    }
    assert(exact&&storage&&inherited_paths);
    std::cout<<"checks="<<checks<<" controls="<<controls<<" exact="<<exact<<" memory_limits="<<storage<<" paths="<<paths<<" inherited_paths="<<inherited_paths<<'\n';
}
