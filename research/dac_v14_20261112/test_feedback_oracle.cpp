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


#include <map>
int main() {
 std::mt19937 rng(20261112);
 size_t compared=0;
 for(int trial=0;trial<200;++trial) {
  int n=1+rng()%5,k=1+rng()%4;
  std::vector<double> openings(k); for(auto& x:openings)x=rng()%12;
  std::vector<t_h3d_plan_leaf> leaves;
  for(int i=0;i<n;++i) {t_h3d_plan_leaf leaf{i,i*4,0,{}};for(int c=0;c<k;++c)if(rng()%4)leaf.candidates.push_back({size_t(c),double(rng()%10)});leaves.push_back(leaf);}
  auto all=enumerate_plans(leaves,openings);
  std::map<std::vector<std::pair<int,size_t>>,double> costs;
  for(auto p:all) {std::sort(p.assignments.begin(),p.assignments.end());auto it=costs.find(p.assignments);if(it==costs.end())costs[p.assignments]=p.cost;else it->second=std::min(it->second,p.cost);}
  for(const auto& entry:costs){assert(h3d_assignment_cost(leaves,openings,entry.first)==entry.second);++compared;}
 }
 std::cout << "fixed_assignment_oracle_checks=" << compared << "\n";
}
