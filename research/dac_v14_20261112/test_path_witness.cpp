#include "src/vpr/src/route/h3d_delay_search.h"
#include <cassert>
#include <iostream>
#include <map>
#include <random>
#include <set>

int main() {
    std::mt19937 random(20261113);
    size_t queries=0, checked_steps=0, checked_terminals=0;
    for (size_t trial=0;trial<100;++trial) {
        const size_t n=1+random()%18;
        std::vector<std::vector<std::pair<size_t,double>>> graph(n);
        for (size_t a=0;a<n;++a)
            for (size_t b=0;b<n;++b)
                if (random()%4==0) graph[a].emplace_back(b,random()%10);
        if (n>1) {
            graph[0].emplace_back(1,0.);graph[1].emplace_back(0,0.);
            graph[0].emplace_back(1,7.); // Parallel edges with unequal weights.
        }
        H3dDelaySearch plain(n),traced(n);
        for (size_t epoch=0;epoch<25;++epoch) {
            const size_t root=random()%n,budget=random()%(n+4);
            std::vector<bool> terminal(n,false);
            for (size_t a=0;a<n;++a) terminal[a]=random()%3==0;
            constexpr double infinity=1e100;
            std::vector<std::vector<double>> floyd(n,std::vector<double>(n,infinity));
            for (size_t a=0;a<n;++a) {
                floyd[a][a]=0.;
                if (!terminal[a]) for (auto [b,w]:graph[a]) floyd[a][b]=std::min(floyd[a][b],w);
            }
            for (size_t k=0;k<n;++k) for (size_t a=0;a<n;++a) for (size_t b=0;b<n;++b)
                floyd[a][b]=std::min(floyd[a][b],floyd[a][k]+floyd[k][b]);
            auto is_terminal=[&](size_t a){return terminal[a];};
            auto expand=[&](size_t a,auto visit){for (auto [b,w]:graph[a]) visit(b,w);};
            auto a=plain.query(root,budget,is_terminal,expand);
            auto b=traced.query(root,budget,is_terminal,expand,true);
            assert(a.terminals==b.terminals && a.settled==b.settled && a.budget_exhausted==b.budget_exhausted);
            assert(a.witness.empty() && b.witness.size()==b.settled);
            std::map<size_t,H3dDelaySearch::WitnessStep> forest;
            for (auto step:b.witness) {
                assert(!forest.contains(step.node));
                if (step.node==root) assert(step.parent==root && step.edge_weight==0.);
                else {
                    assert(forest.contains(step.parent)); // Parent settled earlier: no zero-cycle ambiguity.
                    bool edge=false;
                    for (auto [next,w]:graph[step.parent]) edge|=next==step.node && w==step.edge_weight;
                    assert(edge && !terminal[step.parent]);
                }
                forest.emplace(step.node,step);
                std::set<size_t> seen;size_t node=step.node;double cost=0.;
                while (node!=root) {
                    assert(seen.insert(node).second && forest.contains(node));
                    cost+=forest.at(node).edge_weight;node=forest.at(node).parent;
                }
                assert(cost==floyd[root][step.node]);++checked_steps;
            }
            for (auto [node,cost]:b.terminals) {
                assert(terminal[node] && forest.contains(node) && cost==floyd[root][node]);++checked_terminals;
            }
            if (!b.budget_exhausted && budget>0) {
                size_t expected=0;
                for (size_t node=0;node<n;++node) expected+=terminal[node] && floyd[root][node]<infinity;
                assert(expected==b.terminals.size());
            }
            // A later disabled query on the trace-enabled instance must also
            // avoid exposing old parent records from a previous epoch.
            auto next=traced.query(root,budget,is_terminal,expand);
            assert(next.witness.empty() && next.terminals==a.terminals && next.settled==a.settled);
            ++queries;
        }
    }
    std::cout<<"query_pairs="<<queries<<" witness_steps="<<checked_steps<<" terminals="<<checked_terminals<<" passed\n";
}
