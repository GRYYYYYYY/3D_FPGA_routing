#include "h3d_equivalent_guides.h"
#include <cassert>
#include <random>
#include <limits>
#include <iostream>
int main() {
 assert(h3d_equivalent_guide(1.,1.,16.,16.));
 assert(h3d_equivalent_guide(1.,0.,16.,0.));
 assert(!h3d_equivalent_guide(1.,1.021,16.,16.));
 assert(!h3d_equivalent_guide(1.,1.,16.,16.01));
 assert(!h3d_equivalent_guide(1.,1.,16.,std::numeric_limits<double>::quiet_NaN()));
 assert(!h3d_equivalent_guide(-1.,0.,16.,16.));
 std::mt19937 gen(761);std::uniform_real_distribution<double> random(0.,100.);
 for(int i=0;i<100000;++i) {
  double a=random(gen),b=random(gen),x=random(gen),y=random(gen);
  bool allowed=h3d_equivalent_guide(a,b,x,y);
  if(allowed) {
   assert(b<=a+.02 && y<=x+1.e-10*std::max(1.,x));
   assert(h3d_equivalent_guide(a,std::max(0.,b-.1),x,std::max(0.,y-.1)));
   assert(h3d_equivalent_guide(a+.1,b,x+.1,y));
  }
 }
 std::cout<<"100000 no-slower/no-pricier monotonic cases and boundary/invalid cases passed\n";
}
