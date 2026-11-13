from pathlib import Path
base=Path(__file__).resolve().parent/'src/vpr/src/route'
p=base/'h3d_fast_plan.cpp';s=p.read_text()
s=s.replace('#include "h3d_crossing.h"','#include "h3d_crossing.h"\n#include "h3d_calibrated_cost.h"')
s=s.replace('    channel_index_.resize(graph_.num_nodes(), -1);','''    const char* mixed = std::getenv("VPR_H3D_MIXED_DELAY");
    if (mixed && std::string(mixed) != "0" && std::string(mixed) != "1")
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "VPR_H3D_MIXED_DELAY must be 0 or 1");
    mixed_delay_ = mixed && std::string(mixed) == "1";
    VTR_LOG("H3D_EXPERIMENT mixed_delay=%d\\n", mixed_delay_);
    channel_index_.resize(graph_.num_nodes(), -1);''',1)
s=s.replace('    std::set<int> timed;','''    std::set<int> timed;
    // Normalize observed delay by the same physical unit before fitting a
    // robust endpoint-local scale. Unknown distance is not infeasibility.
    auto calibrate = [&](RRNodeId endpoint, const H3dDelayPlan::Distances& distances) {
        std::vector<double> ratios;
        for (const auto& [node, delay] : distances) {
            int c = channel_index_[node];
            if (c >= 0) ratios.push_back(delay / delay_plan_->delay_unit() / proxy_(endpoint, c));
        }
        return h3d_calibrated_scale(std::move(ratios));
    };
    const bool mixed = mixed_delay_ && forward;
    const double source_scale = mixed ? calibrate(source, *forward) : 1.;
    std::unordered_map<int, double> sink_scales;''')
s=s.replace('        return proxy_(source, c);','        return source_scale * proxy_(source, c);',1)
s=s.replace('    auto branch = [&](int pin, size_t c) {','''    auto branch = [&](int pin, size_t c) {
        if (mixed) {
            double sink_cost = proxy_(terminals[pin], c);
            auto back = reverse.find(pin);
            if (back != reverse.end()) {
                auto found = back->second->find(channels_[c]);
                sink_cost = found != back->second->end() ? found->second / delay_plan_->delay_unit()
                                                       : sink_cost * sink_scales.at(pin);
            }
            return sink_cost * (1. + 4. * criticality[pin]) + 4. * criticality[pin] * source_cost(c);
        }''')
s=s.replace('        if (forward && !forward->empty() && !ranked.empty()) {','''        if (mixed && !ranked.empty()) {
            // Unlike the legacy all-or-nothing rule, reverse-only measurements
            // are useful even when the bounded source query found no candidate.
            const auto& back = delay_plan_->distances(terminals[pin], true);
            reverse[pin] = &back;
            sink_scales[pin] = calibrate(terminals[pin], back);
            ++mixed_pins_;
            size_t measured = 0;
            for (auto& [cost, c] : ranked) {
                bool from = forward->contains(channels_[c]);
                bool to = back.contains(channels_[c]);
                measured += from || to;
                mixed_both_ += from && to;
                mixed_source_only_ += from && !to;
                mixed_sink_only_ += !from && to;
                mixed_estimated_ += !from && !to;
                cost = opening(c) + branch(pin, c);
            }
            mixed_informed_pins_ += measured > 0;
        } else if (forward && !forward->empty() && !ranked.empty()) {''')
s=s.replace('    if (delay_plan_) delay_plan_->log();','''    VTR_LOG("H3D_MIXED pins=%zu informed_pins=%zu both=%zu source_only=%zu sink_only=%zu estimated=%zu\\n",
            mixed_pins_, mixed_informed_pins_, mixed_both_, mixed_source_only_, mixed_sink_only_, mixed_estimated_);
    if (delay_plan_) delay_plan_->log();''')
p.write_text(s)
p=base/'h3d_fast_plan.h';s=p.read_text().replace('    bool edge_encoding_ = false;', '''    bool mixed_delay_ = false;                                         ///< Experimental calibrated candidate-level delay, off by default.
    size_t mixed_pins_ = 0, mixed_informed_pins_ = 0;                    ///< Eligible and measurement-informed connections.
    size_t mixed_both_ = 0, mixed_source_only_ = 0, mixed_sink_only_ = 0, mixed_estimated_ = 0; ///< Sampled candidate coverage.
    bool edge_encoding_ = false;''');p.write_text(s)
