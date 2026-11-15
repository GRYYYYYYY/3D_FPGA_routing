#pragma once

struct H3dBoundedCriticalCost {
    bool applied;
    float congestion, timing_seconds;
};

/** Replace only the method's extra critical crossing charge; the native
 * congestion before that charge is retained exactly. Physical delay is not an
 * input or output. RCV and every other edge retain their original policy. */
inline H3dBoundedCriticalCost h3d_bounded_critical_cost(bool enabled,bool configurable,
        bool crossing,bool preferred,bool rcv,float criticality,float native_congestion,
        float old_congestion,float old_timing_seconds,float bounded_seconds,bool cap_only=false) {
    if(enabled && configurable && crossing && !preferred && !rcv && criticality>=.9f) {
        const double old_extra=(1.-double(criticality))*(double(old_congestion)-double(native_congestion));
        const double bound=double(criticality*bounded_seconds);
        if(cap_only && old_extra<=bound)return {false,old_congestion,old_timing_seconds};
        return {true,native_congestion,bounded_seconds};
    }
    return {false,old_congestion,old_timing_seconds};
}
