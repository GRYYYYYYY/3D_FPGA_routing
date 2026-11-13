#include "src/vpr/src/route/h3d_bounded_critical_guide.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
int main() {
    std::mt19937 rng(142913);size_t reduced=0,preserved=0,scope=0;
    for(size_t i=0;i<300000;++i) {
        bool enabled=rng()%2,config=rng()%2,cross=rng()%2,pref=rng()%2,rcv=rng()%2;
        float c=float(rng()%10001)/10000.f;
        if(i%8==0)c=.9f;if(i%8==1)c=std::nextafter(.9f,0.f);
        float native=std::ldexp(float(1+rng()%64),int(rng()%71)-80),old=native*float(1+rng()%8);
        float seconds=float((rng()%101)/100.*2.6042048676241537e-10*.25);
        auto k=h3d_bounded_critical_cost(enabled,config,cross,pref,rcv,c,native,old,0.f,seconds,true);
        const double original=(1.-double(c))*(double(old)-native);
        const double actual=k.applied ? double(c*k.timing_seconds) : (1.-double(c))*(double(k.congestion)-native);
        assert(actual<=original+std::max(1.e-35,std::abs(original)*1.e-12));
        assert(k.congestion>=native && k.congestion<=old);
        if(k.applied) {assert(k.congestion==native && k.timing_seconds==seconds);++reduced;}
        else {assert(k.congestion==old && k.timing_seconds==0.f);++preserved;}
        if(enabled && config && cross && !pref && !rcv && c>=.9f) {
            ++scope;if(original<=double(c*seconds))assert(!k.applied);
            auto zero=h3d_bounded_critical_cost(true,true,true,false,false,c,native,old,0.f,0.f,true);
            assert((1.-double(c))*(double(zero.congestion)-native)==0.);
        }
    }
    std::cout<<"cases=300000 reduced="<<reduced<<" preserved="<<preserved<<" applicable_scope="<<scope<<" no-amplification/exact-low-cost/zero/RCV/boundary passed\n";
}
