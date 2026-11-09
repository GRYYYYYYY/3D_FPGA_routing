// Standalone exact-oracle tests for the finite planning recurrence.
#include "h3d_partition_dp.h"

#include <cassert>
#include <functional>
#include <iostream>
#include <random>

// Enumerate every hierarchical cut and candidate choice, without using the
// production solver's common-set merging or minimum recurrence.
struct OracleChoice {
    double cost;
    std::vector<std::pair<int, size_t>> assignments;
};

std::vector<OracleChoice> enumerate_plans(std::vector<t_h3d_plan_leaf> leaves,
                                          const std::vector<double>& opening) {
    std::vector<OracleChoice> choices;
    for (size_t candidate = 0; candidate < opening.size(); ++candidate) {
        OracleChoice choice{opening[candidate], {}};
        bool feasible = true;
        for (const auto& leaf : leaves) {
            auto found = std::find_if(leaf.candidates.begin(), leaf.candidates.end(), [candidate](const auto& c) {
                return c.channel == candidate;
            });
            if (found == leaf.candidates.end()) {
                feasible = false;
                break;
            }
            choice.cost += found->branch_cost;
            choice.assignments.emplace_back(leaf.pin, candidate);
        }
        if (feasible)
            choices.push_back(choice);
    }
    if (leaves.size() > 1) {
        // Random fixtures use strictly increasing x and y=0, fixing the
        // hierarchy independently of the production sorting implementation.
        std::sort(leaves.begin(), leaves.end(), [](const auto& a, const auto& b) { return a.x < b.x; });
        auto mid = leaves.begin() + leaves.size() / 2;
        auto left = enumerate_plans({leaves.begin(), mid}, opening);
        auto right = enumerate_plans({mid, leaves.end()}, opening);
        for (const auto& a : left) {
            for (const auto& b : right) {
                OracleChoice choice{a.cost + b.cost, a.assignments};
                choice.assignments.insert(choice.assignments.end(), b.assignments.begin(), b.assignments.end());
                choices.push_back(choice);
            }
        }
    }
    return choices;
}

int main() {
    std::vector<t_h3d_plan_leaf> leaves = {
        {1, 0, 0, {{0, 0.}, {1, 10.}}},
        {2, 10, 0, {{0, 10.}, {1, 0.}}},
    };
    auto shared = h3d_plan_partition(leaves, {20., 20.});
    assert(shared.cost == 30. && shared.groups == 1);
    assert(shared.assignment[0].second == shared.assignment[1].second);
    auto split = h3d_plan_partition(leaves, {1., 1.});
    assert(split.cost == 2. && split.groups == 2);
    assert(split.assignment[0].second != split.assignment[1].second);

    // Nearby but unreachable candidate 0 is excluded from sink 2.
    leaves[1].candidates = {{1, 0.}};
    auto reachable = h3d_plan_partition(leaves, {20., 20.});
    assert(reachable.assignment[1].second == 1);
    leaves[1].candidates.clear();
    auto infeasible = h3d_plan_partition(leaves, {20., 20.});
    assert(!std::isfinite(infeasible.cost) && infeasible.assignment.empty());
    assert(h3d_plan_partition({}, {}).cost == 0.);

    std::mt19937 random(20261022);
    for (int trial = 0; trial < 250; ++trial) {
        int count = 1 + random() % 5;
        int channels = 1 + random() % 4;
        std::vector<double> opening;
        for (int c = 0; c < channels; ++c)
            opening.push_back(random() % 12);
        leaves.clear();
        for (int i = 0; i < count; ++i) {
            t_h3d_plan_leaf leaf{i + 1, i * 4, 0, {}};
            for (int c = 0; c < channels; ++c) {
                if (random() % 5 != 0)
                    leaf.candidates.push_back({size_t(c), double(random() % 15)});
            }
            leaves.push_back(leaf);
        }
        auto plans = enumerate_plans(leaves, opening);
        double optimum = std::numeric_limits<double>::infinity();
        for (const auto& plan : plans)
            optimum = std::min(optimum, plan.cost);
        auto actual = h3d_plan_partition(leaves, opening);
        assert(actual.cost == optimum);
        if (std::isfinite(optimum)) {
            assert(actual.assignment.size() == leaves.size());
            for (const auto& [pin, channel] : actual.assignment) {
                const auto& leaf = leaves.at(pin - 1);
                assert(std::any_of(leaf.candidates.begin(), leaf.candidates.end(), [channel](const auto& c) {
                    return c.channel == channel;
                }));
            }
        }
    }
    std::cout << "DP: hand-checked sharing/splitting/reachability and 250 exhaustive-oracle cases passed\n";
}
