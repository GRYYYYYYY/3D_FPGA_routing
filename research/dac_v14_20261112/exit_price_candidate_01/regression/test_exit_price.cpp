#include "h3d_exit_price.h"
#include <cassert>
#include <limits>
#include <random>
#include <iostream>
int main() {
 assert(h3d_exit_price_premium(1.,16.,.25)==0.);
 assert(h3d_exit_price_premium(2.,16.,.25)==4.);
 assert(h3d_exit_price_premium(100.,16.,.25)==4.);
 assert(h3d_exit_price_premium(1.5,16.,.25)==2.);
 assert(h3d_exit_price_premium(4.,16.,0.)==0.);
 assert(h3d_exit_price_premium(std::numeric_limits<double>::infinity(),16.,.25)==0.);
 std::mt19937 gen(114);std::uniform_real_distribution<double> value(0.,100.);
 for(int i=0;i<100000;++i) {
  double price=value(gen),opening=value(gen),weight=value(gen)/100.;
  double result=h3d_exit_price_premium(price,opening,weight);
  assert(result>=0. && result<=opening*weight);
  assert(h3d_exit_price_premium(price+1.,opening,weight)>=result);
  assert(h3d_exit_price_premium(price,opening+1.,weight)>=result);
  if(price<=1.)assert(result==0.);
 }
 std::cout<<"100000 cap/nonnegative/monotonic cases and inactive/invalid boundaries passed\n";
}
