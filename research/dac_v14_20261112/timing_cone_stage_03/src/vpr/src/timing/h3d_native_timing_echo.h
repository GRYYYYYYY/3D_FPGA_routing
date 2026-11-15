#pragma once

#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <limits>

#include "timing_info.h"
#include "tatum/echo_writer.hpp"
#include "vpr_error.h"
#include "vtr_log.h"

/** @brief Optional full-precision observation of the completed native STA. */
namespace h3d_native_timing_echo {

/**
 * @brief Export the existing timing graph, constraints, delays and analyzer tags.
 *
 * VPR_H3D_FINAL_TIMING_ECHO names a diagnostic file. An unset or empty variable
 * leaves the default flow untouched. The exporter changes neither timing state
 * nor routing; double max_digits10 preserves the native float values exactly.
 */
inline void write_if_requested(const SetupHoldTimingInfo& timing,
                               const tatum::DelayCalculator& delay_calculator) {
    const char* path = std::getenv("VPR_H3D_FINAL_TIMING_ECHO");
    if (!path || !*path) return;
    std::ofstream output(path);
    if (!output) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot open full-precision timing echo: %s", path);
    output << std::setprecision(std::numeric_limits<double>::max_digits10);
    tatum::write_echo(output, *timing.timing_graph(), *timing.timing_constraints(),
                      delay_calculator, timing.analyzer());
    output.close();
    if (!output) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Cannot finish full-precision timing echo: %s", path);
    VTR_LOG("H3D_FINAL_TIMING_ECHO path=%s\n", path);
}

} // namespace h3d_native_timing_echo
