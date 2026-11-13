#include "src/vpr/src/route/h3d_bounded_critical_guide.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <limits>
int main() {
    std::mt19937 rng(14272);size_t applied=0,unchanged=0;
    for(size_t i=0;i<200000;++i) {
        bool enable=rng()%2,config=rng()%2,cross=rng()%2,preferred=rng()%2,rcv=rng()%2;
        float c=float(rng()%10001)/10000.f;
        if(i%8==0)c=.9f;
        if(i%8==1)c=std::nextafter(.9f,0.f);
        float native=float(rng()%100000)*1.e-12f,old=native*3.f;
        double r=double(rng()%101)/100.,unit=2.6042048676241537e-10,beta=.25;
        float seconds=float(beta*r*unit);
        auto out=h3d_bounded_critical_cost(enable,config,cross,preferred,rcv,c,native,old,0.f,seconds);
        assert(out.congestion>=native && out.congestion<=old);
        assert(out.timing_seconds>=0.f && double(out.timing_seconds)<=beta*unit*(1+1.e-6));
        if(out.applied) {
            assert(out.congestion==native && out.timing_seconds==seconds);
            assert(enable && config && cross && !preferred && !rcv && c>=.9f);++applied;
        } else {assert(out.congestion==old && out.timing_seconds==0.f);++unchanged;}
        auto disabled=h3d_bounded_critical_cost(false,config,cross,preferred,rcv,c,native,old,1.e-10f,seconds);
        assert(!disabled.applied && disabled.congestion==old && disabled.timing_seconds==1.e-10f);
    }
    auto zero=h3d_bounded_critical_cost(true,true,true,false,false,.99f,3.f,9.f,0.f,0.f);
    assert(zero.applied && zero.congestion==3.f && zero.timing_seconds==0.f);
    std::cout<<"cases=200000 applied="<<applied<<" unchanged="<<unchanged<<" nativebase/cap/disabled/RCV/boundary passed\n";
}
