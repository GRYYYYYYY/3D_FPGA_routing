#include "h3d_reachability.h"

#include <cassert>
#include <iostream>
#include <random>

int main() {
    std::mt19937 random(20261022);
    for (int trial = 0; trial < 300; ++trial) {
        size_t n = 1 + random() % 12;
        std::vector<std::pair<size_t, size_t>> edges;
        std::vector<std::vector<bool>> closure(n, std::vector<bool>(n, false));
        for (size_t a = 0; a < n; ++a) {
            closure[a][a] = true;
            for (size_t b = 0; b < n; ++b) {
                if (random() % 5 == 0) {
                    edges.emplace_back(a, b);
                    closure[a][b] = true;
                }
            }
        }
        // Independent Floyd-Warshall Boolean transitive closure.
        for (size_t k = 0; k < n; ++k)
            for (size_t a = 0; a < n; ++a)
                for (size_t b = 0; b < n; ++b)
                    closure[a][b] = closure[a][b] || (closure[a][k] && closure[k][b]);
        H3dReachabilityIndex index(n, edges);
        for (size_t target = 0; target < n; ++target) {
            auto can_reach_target = index.mark({index.component(target)}, true);
            auto reachable_from_target = index.mark({index.component(target)}, false);
            for (size_t source = 0; source < n; ++source) {
                auto fwd = index.relevant_components(source, false, can_reach_target);
                auto rev = index.relevant_components(source, true, reachable_from_target);
                assert(std::binary_search(fwd.begin(), fwd.end(), index.component(target)) == closure[source][target]);
                assert(std::binary_search(rev.begin(), rev.end(), index.component(target)) == closure[target][source]);
                assert((index.component(source) == index.component(target)) == (closure[source][target] && closure[target][source]));
            }
        }
    }
    std::cout << "SCC: 300 directed graphs agree with independent all-pairs closure in both directions\n";
}
