#include "h3d_delay_search.h"
#include <cassert>
#include <iostream>
#include <random>

int main() {
    std::mt19937 rng(20261027);
    const double inf = std::numeric_limits<double>::infinity();
    for (int trial = 0; trial < 250; ++trial) {
        size_t n = 3 + rng()%13;
        std::vector<std::vector<double>> weights(n, std::vector<double>(n, inf));
        std::vector<bool> terminal(n, false);
        terminal[n-1] = true;
        terminal[n-2] = true;
        for (size_t u=0; u<n; ++u)
            for (size_t v=0; v<n; ++v)
                if (u!=v && rng()%5==0) weights[u][v] = rng()%7;
        H3dDelaySearch search(n);
        for (bool reverse : {false, true}) {
            auto distance = weights;
            if (reverse)
                for (size_t u=0; u<n; ++u)
                    for (size_t v=0; v<n; ++v) distance[u][v]=weights[v][u];
            for (size_t u=0; u<n; ++u) distance[u][u]=0.;
            // Independent all-pairs oracle: no terminal may be intermediate.
            for (size_t k=0; k<n; ++k) if (!terminal[k])
                for (size_t u=0; u<n; ++u)
                    for (size_t v=0; v<n; ++v)
                        distance[u][v]=std::min(distance[u][v],distance[u][k]+distance[k][v]);
            auto expand = [&](size_t u, auto visit) {
                for (size_t v=0; v<n; ++v) {
                    double w = reverse ? weights[v][u] : weights[u][v];
                    if (std::isfinite(w)) visit(v,w);
                }
            };
            for (size_t source=0; source<n-2; ++source) {
                auto result=search.query(source,n, [&](size_t u){return terminal[u];},expand);
                std::vector<double> observed(n,inf);
                for (auto [u,d] : result.terminals) observed[u]=d;
                for (size_t target=n-2; target<n; ++target) assert(observed[target]==distance[source][target]);
                // Bounded output may omit reachable terminals, but every
                // returned value must still equal the full shortest distance.
                auto bounded=search.query(source,1+rng()%3,[&](size_t u){return terminal[u];},expand);
                for (auto [u,d] : bounded.terminals) assert(d==distance[source][u]);
            }
        }
    }
    H3dDelaySearch search(3);
    auto stopped=search.query(0,1,[](size_t n){return n==2;},[](size_t u, auto visit){if(u<2)visit(u+1,1.);});
    assert(stopped.budget_exhausted && stopped.terminals.empty());
    bool rejected=false;
    try { search.query(0,3,[](size_t){return false;},[](size_t,auto visit){visit(1,-1.);}); }
    catch (const std::invalid_argument&) {rejected=true;}
    assert(rejected);
    std::cout << "250 directed weighted graphs: forward/reverse first-crossing distances match Floyd-Warshall; bounded settled distances and negative-weight guard pass\n";
}
