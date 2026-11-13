#pragma once

#include <algorithm>
#include <cmath>
#include <vector>

/** @brief Fit an endpoint-local robust delay/proxy scale in normalized delay units.
 * Eight prior observations at unit scale shrink small samples toward geometry.
 * Measurements themselves are never shrunk; only missing distances use this fit.
 * A zero measured distance is valid. Absent/nonfinite samples are not distances.
 */
inline double h3d_calibrated_scale(std::vector<double> ratios) {
    ratios.erase(std::remove_if(ratios.begin(), ratios.end(), [](double x) {
        return !std::isfinite(x) || x < 0.;
    }), ratios.end());
    if (ratios.empty()) return 1.;
    std::sort(ratios.begin(), ratios.end());
    size_t n = ratios.size();
    double median = n % 2 ? ratios[n / 2] : .5 * (ratios[n / 2 - 1] + ratios[n / 2]);
    return (n * median + 8.) / (n + 8.);
}
