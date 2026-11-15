#include "preferred_query_adapter.h"
#include <cassert>
#include <iostream>
#include <random>
/** @brief Independent forward phase-graph Floyd oracle tests the reverse adapter. */
int main(){
    std::mt19937 rng(18521);size_t checks=0,exact=0,storage=0;
    for(size_t trial=0;trial<240;++trial){
        size_t n=4+rng()%9,sink=rng()%n;std::vector<int> layers(n);std::vector<bool> allowed(n);
        for(size_t i=0;i<n;++i){layers[i]=rng()%2;allowed[i]=rng()%5!=0;}allowed[sink]=true;
        std::vector<std::vector<std::pair<size_t,double>>> rev(n);
        std::vector<std::tuple<size_t,size_t,double>> edges;
        for(size_t u=0;u<n;++u)for(size_t v=0;v<n;++v)if(rng()%4==0){double w=rng()%5;rev[v].emplace_back(u,w);edges.emplace_back(u,v,w);}
        std::set<size_t> preferred;for(size_t i=0;i<n;++i)if(rng()%3==0)preferred.insert(i);
        std::vector<std::pair<size_t,double>> seeds;for(size_t i=0;i<n;++i)if(rng()%2==0){seeds.emplace_back(i,double(rng()%5));if(rng()%3==0)seeds.emplace_back(i,double(rng()%9));}
        const size_t size=2*n+1;double inf=std::numeric_limits<double>::infinity();std::vector<std::vector<double>> dist(size,std::vector<double>(size,inf));
        for(size_t i=0;i<size;++i)dist[i][i]=0.;
        for(auto [s,d]:seeds)if(allowed[s]&&layers[s]!=layers[sink])dist[2*n][s]=std::min(dist[2*n][s],d);
        for(auto [u,v,w]:edges)if(allowed[u]&&allowed[v]){
            if(layers[u]==layers[v]){size_t phase=layers[u]==layers[sink]?n:0;dist[u+phase][v+phase]=std::min(dist[u+phase][v+phase],w);}
            else if(layers[u]!=layers[sink]&&layers[v]==layers[sink]&&preferred.count(u))dist[u][v+n]=std::min(dist[u][v+n],w);
        }
        for(size_t k=0;k<size;++k)for(size_t i=0;i<size;++i)for(size_t j=0;j<size;++j)dist[i][j]=std::min(dist[i][j],dist[i][k]+dist[k][j]);
        double oracle=dist[2*n][sink+n];
        for(int mode=0;mode<3;++mode)for(size_t budget:{size_t(0),size_t(2),size_t(10000)})for(bool limited:{false,true}){
            auto a=query_preferred(n,sink,seeds,preferred,[&](size_t i){return layers[i];},[&](size_t i){return allowed[i];},[&](size_t i,auto visit){for(auto [u,w]:rev[i])visit(u,w);},[&](size_t i,size_t s){return double((i+3*s)%7)*11.;},mode!=0,mode==2,budget,limited?3:16384,limited?6:65536);
            auto& r=a.result;++checks;assert(r.expansions<=budget);
            if(r.lower_seconds)assert(*r.lower_seconds<=oracle);
            if(r.priced_upper_seconds){assert(*r.priced_upper_seconds>=oracle);double value=a.seed_floor;for(auto e:r.edges)value+=e.physical_seconds;assert(value==*r.physical_path_seconds);}
            if(r.stop==H3dCandidatePath::Stop::EXACT){++exact;assert(r.priced_upper_seconds&&*r.priced_upper_seconds==oracle&&r.lower_seconds&&*r.lower_seconds==oracle);}
            if(r.stop==H3dCandidatePath::Stop::UNREACHABLE)assert(!std::isfinite(oracle)&&!r.priced_upper_seconds);
            if(r.stop==H3dCandidatePath::Stop::MEMORY_LIMIT){++storage;assert(!r.lower_seconds);}
            if(!limited&&budget==10000)assert((!std::isfinite(oracle)&&r.stop==H3dCandidatePath::Stop::UNREACHABLE)||r.priced_upper_seconds);
        }
    }
    assert(exact&&storage);std::cout<<"checks="<<checks<<" exact="<<exact<<" memory_limits="<<storage<<'\n';
}
