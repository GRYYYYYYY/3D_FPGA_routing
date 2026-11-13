#include "src/vpr/src/route/h3d_compact_witness.h"
#include <cassert>
#include <iostream>
#include <random>
#include <set>
#include <map>
using Step=H3dDelaySearch::WitnessStep;
std::vector<std::tuple<size_t,size_t,double>> path(const std::vector<Step>& forest,size_t node) {
    std::map<size_t,Step> index;for(auto s:forest)assert(index.emplace(s.node,s).second);
    std::vector<std::tuple<size_t,size_t,double>> answer;
    while(true) {auto s=index.at(node);answer.emplace_back(s.node,s.parent,s.edge_weight);if(node==s.parent)break;node=s.parent;assert(answer.size()<=forest.size());}
    return answer;
}
int main() {
    std::mt19937_64 rng(142638);
    size_t queries=0,full_records=0,compact_records=0,terminal_paths=0;
    for(size_t g=0;g<250;++g) {
        size_t n=5+rng()%150;std::vector<std::vector<std::pair<size_t,double>>> edges(n);
        for(size_t e=0;e<6*n;++e)edges[rng()%n].emplace_back(rng()%n,double(rng()%6)/4.);
        H3dDelaySearch search(n),off(n);
        for(size_t q=0;q<40;++q) {
            size_t source=rng()%n,budget=rng()%(n+1);std::set<size_t> terminals;
            for(size_t t=0;t<rng()%12;++t)terminals.insert(rng()%n);
            auto is_terminal=[&](size_t node){return terminals.contains(node);};
            auto expand=[&](size_t node,auto visit){for(auto [next,w]:edges[node])visit(next,w);};
            auto result=search.query(source,budget,is_terminal,expand,true);auto control=off.query(source,budget,is_terminal,expand);
            assert(result.terminals==control.terminals && result.settled==control.settled && result.budget_exhausted==control.budget_exhausted);
            auto compact=h3d_compact_witness(result);assert(compact.size()<=result.witness.size());
            std::set<size_t> needed,retained;
            for(auto [node,delay]:result.terminals) {
                auto a=path(result.witness,node),b=path(compact,node);assert(a==b);double sum=0;
                for(auto [x,parent,w]:a){needed.insert(x);sum+=w;}assert(sum==delay);++terminal_paths;
            }
            size_t cursor=0;for(auto s:compact) {
                assert(retained.insert(s.node).second);
                while(result.witness.at(cursor).node!=s.node)++cursor;
                auto original=result.witness.at(cursor++);assert(original.parent==s.parent && original.edge_weight==s.edge_weight);
            }
            assert(needed==retained);full_records+=result.witness.size();compact_records+=compact.size();++queries;
        }
    }
    // Most settled work is unrelated to the only measured terminal.
    H3dDelaySearch search(1001);auto result=search.query(0,1001,[](size_t n){return n==1;},[](size_t n,auto visit){if(n==0)for(size_t x=1;x<=1000;++x)visit(x,double(x));},true);
    assert(result.settled==1001 && h3d_compact_witness(result).size()==2);
    bool threw=false;try{H3dDelaySearch::Result bad;bad.terminals={{2,0}};bad.witness={{2,3,0},{3,2,0}};h3d_compact_witness(bad);}catch(const std::logic_error&){threw=true;}assert(threw);
    std::cout<<"queries="<<queries<<" terminal_paths="<<terminal_paths<<" full_records="<<full_records<<" compact_records="<<compact_records<<" passed\n";
}
