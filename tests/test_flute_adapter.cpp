#include "h3d_flute.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <set>
#include <utility>
#include <vector>

// Known rectilinear optima and structural checks for the imported LUT/code pair.
int main(int argc, char** argv) {
    assert(argc == 2);
    Flute::readLUT(argv[1]);
    for (const auto& [points, optimum] : std::vector<std::pair<std::vector<std::pair<int, int>>, int>>{
             {{{0, 0}, {4, 0}}, 4},
             {{{0, 0}, {4, 0}, {2, 3}}, 7},
             {{{0, 0}, {4, 0}, {0, 3}, {4, 3}}, 10}}) {
        std::vector<int> xs, ys;
        for (const auto& [x, y] : points) {
            xs.push_back(x);
            ys.push_back(y);
        }
        auto tree = Flute::flute(xs.size(), xs.data(), ys.data(), FLUTE_ACCURACY);
        assert(tree.length == optimum);
        int n = 2 * tree.deg - 2, length = 0, edges = 0;
        std::vector<std::vector<int>> adjacency(n);
        std::set<std::pair<int, int>> locations;
        for (int i = 0; i < n; ++i) {
            const auto& a = tree.branch[i];
            assert(a.n >= 0 && a.n < n);
            const auto& b = tree.branch[a.n];
            locations.emplace(a.x, a.y);
            length += std::abs(a.x - b.x) + std::abs(a.y - b.y);
            if (a.n != i) {
                ++edges;
                adjacency[i].push_back(a.n);
                adjacency[a.n].push_back(i);
            }
        }
        assert(edges == n - 1 && length == optimum);
        for (auto point : points) assert(locations.contains(point));
        std::set<int> visited{0};
        std::vector<int> stack{0};
        while (!stack.empty()) {
            int node = stack.back();
            stack.pop_back();
            for (int next : adjacency[node])
                if (visited.insert(next).second) stack.push_back(next);
        }
        assert(visited.size() == size_t(n));
        Flute::free_tree(tree);
    }
    std::cout << "FLUTE: LUT adapter, exact small lengths, terminal coverage and connected acyclic trees passed\n";
}
