#include "src/vpr/src/route/h3d_calibrated_cost.h"
#include <cassert>
#include <limits>
int main() {
 assert(h3d_calibrated_scale({}) == 1.);
 assert(h3d_calibrated_scale({1,1,1,1}) == 1.);
 assert(h3d_calibrated_scale({0,0,0,0,0,0,0,0}) == .5);
 assert(h3d_calibrated_scale({2,2,2,2,2,2,2,10000}) == 1.5);
 assert(h3d_calibrated_scale({-1, std::numeric_limits<double>::infinity()}) == 1.);
 assert(h3d_calibrated_scale({2,4}) == 1.4);
}
