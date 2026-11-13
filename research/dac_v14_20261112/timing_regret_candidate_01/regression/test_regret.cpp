#include "h3d_timing_regret.h"
#include <cassert>
#include <limits>
#include <random>
#include <iostream>
int main() {
    const double unit=1.e-10, weight=.25;
    assert(h3d_timing_regret_seconds(unit,0.,unit,weight)==0.);
    assert(h3d_timing_regret_seconds(unit,unit,unit,weight)==0.);
    assert(h3d_timing_regret_seconds(unit,unit*1.01,unit,weight)==0.);
    assert(h3d_timing_regret_seconds(unit,10.*unit,unit,weight)==weight*unit);
    assert(h3d_timing_regret_seconds(0.,unit,unit,0.)==0.);
    assert(h3d_timing_regret_seconds(std::numeric_limits<double>::infinity(),unit,unit,weight)==0.);
    std::mt19937 rng(193);std::uniform_real_distribution<double> sample(0.,20.);
    for(int i=0;i<100000;++i) {
        double chosen=sample(rng)*unit, alternative=sample(rng)*unit;
        double p=h3d_timing_regret_seconds(chosen,alternative,unit,weight);
        assert(p>=0. && p<=weight*unit);
        assert(alternative>chosen || p==0.);
        assert(h3d_timing_regret_seconds(chosen,alternative+unit,unit,weight)>=p);
        assert(h3d_timing_regret_seconds(chosen+unit,alternative,unit,weight)<=p);
        double scaled=h3d_timing_regret_seconds(chosen*1000.,alternative*1000.,unit*1000.,weight);
        assert(std::abs(scaled-p*1000.) < 1.e-20);
    }
    std::cout << "100000 dimensional/bound/monotonicity cases plus invalid and tie cases passed\n";
}
