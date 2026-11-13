#include "h3d_partition_sensitivity.h"
#include <cassert>
#include <iostream>
#include <random>

static bool equal_cost(double a, double b) {
    return (a == b) || (std::isfinite(a) && std::isfinite(b)
        && std::abs(a-b) <= 1e-10 * std::max({1., std::abs(a), std::abs(b)}));
}

int main() {
    assert(h3d_partition_exclusion_costs({}, {}, {}).base_cost == 0.);
    std::mt19937 rng(14723);
    size_t exclusions = 0, impossible = 0, ties = 0, tables = 0;
    for (size_t trial = 0; trial < 1000; ++trial) {
        size_t n = 1 + rng()%9, k = 1 + rng()%7;
        std::vector<double> opening(k);
        for (auto& x : opening) x = (rng()%19) * (trial%2 ? .25 : .137);
        std::vector<t_h3d_plan_leaf> leaves;
        std::vector<std::pair<int,size_t>> requests;
        for (size_t i = 0; i < n; ++i) {
            t_h3d_plan_leaf leaf{int(i+1), int(rng()%4), int(rng()%4), {}};
            for (size_t c = 0; c < k; ++c) {
                if (rng()%4) leaf.candidates.push_back({c, (rng()%23) * (trial%2 ? .5 : .173)});
                requests.emplace_back(leaf.pin, c); // Include exclusions already absent from the table.
            }
            leaves.push_back(std::move(leaf));
        }
        std::shuffle(leaves.begin(), leaves.end(), rng);
        auto original = h3d_plan_partition(leaves, opening);
        auto result = h3d_partition_exclusion_costs(leaves, opening, requests);
        assert(equal_cost(result.base_cost, original.cost));
        assert(result.exclusion_costs.size() == requests.size());
        for (size_t j = 0; j < requests.size(); ++j) {
            auto modified = leaves;
            auto [pin, channel] = requests[j];
            for (auto& leaf : modified) if (leaf.pin == pin)
                leaf.candidates.erase(std::remove_if(leaf.candidates.begin(), leaf.candidates.end(),
                    [channel](const auto& c) { return c.channel == channel; }), leaf.candidates.end());
            double oracle = h3d_plan_partition(modified, opening).cost;
            assert(equal_cost(result.exclusion_costs[j], oracle));
            ++exclusions; impossible += !std::isfinite(oracle);
            ties += std::isfinite(oracle) && equal_cost(oracle, original.cost);
        }
        ++tables;
    }
    // Sharing can select a locally worse candidate with a strictly positive
    // net-level exclusion margin: a local-gap confidence would discard it.
    std::vector<t_h3d_plan_leaf> shared = {{1,0,0,{{0,0.},{1,1.}}}, {2,1,0,{{1,1.}}}};
    auto plan = h3d_plan_partition(shared, {2.,3.});
    assert(plan.groups == 1 && plan.cost == 5.);
    auto result = h3d_partition_exclusion_costs(shared, {2.,3.}, {{1,1},{2,1}});
    assert(result.exclusion_costs[0] == 6. && std::isinf(result.exclusion_costs[1]));
    assert(h3d_exact_tie_pressure(2.f, result.base_cost, result.exclusion_costs[0]) == 2.f);
    assert(h3d_exact_tie_pressure(2.f, result.base_cost, result.exclusion_costs[1]) == 2.f);
    auto tied = h3d_partition_exclusion_costs({{1,0,0,{{0,1.},{1,1.}}}}, {2.,2.}, {{1,0}});
    assert(h3d_exact_tie_pressure(2.f, tied.base_cost, tied.exclusion_costs[0]) == 0.f);
    assert(h3d_exact_tie_pressure(2.f, tied.base_cost, std::nextafter(tied.base_cost, INFINITY)) == 2.f);
    assert(std::abs(h3d_relative_margin_pressure(2.f, result.base_cost, result.exclusion_costs[0], 4.) - .4f) < 1e-7f);
    assert(h3d_relative_margin_pressure(2.f, result.base_cost, result.exclusion_costs[1], 4.) == 2.f);
    assert(h3d_relative_margin_pressure(2.f, tied.base_cost, tied.exclusion_costs[0], 3.) == 0.f);
    assert(h3d_relative_margin_pressure(2.f, 5., 6., 4.) == h3d_relative_margin_pressure(2.f, 50., 60., 40.));
    assert(h3d_relative_margin_pressure(2.f, 500., 501., 4.) == h3d_relative_margin_pressure(2.f, 5., 6., 4.));
    std::cout << "{\"passed\":true,\"random_tables\":" << tables
              << ",\"oracle_exclusions\":" << exclusions << ",\"infeasible_exclusions\":"
              << impossible << ",\"tied_exclusions\":" << ties << "}\n";
}
