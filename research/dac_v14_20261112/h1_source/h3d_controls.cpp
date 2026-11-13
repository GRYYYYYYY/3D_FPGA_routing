#include "h3d_controls.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <map>
#include <queue>
#include <string>
#include <unordered_map>

#include "globals.h"
#include "h3d_flute.h"
#include "vpr_error.h"
#include "vtr_log.h"

namespace {
/** @brief Opt-in static topology controls, separate from cross-layer planning. */
enum class e_h3d_control { OFF,
                           FLUTE_SOFT,
                           STEINER_FIELD };

/** @brief Read the exact immutable control setting; typos are fatal. */
e_h3d_control mode() {
    static const e_h3d_control value = [] {
        const char* env = std::getenv("VPR_H3D_CONTROL");
        std::string name = env ? env : "off";
        if (name == "off") return e_h3d_control::OFF;
        if (name == "flute_soft") return e_h3d_control::FLUTE_SOFT;
        if (name == "steiner_field") return e_h3d_control::STEINER_FIELD;
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Unknown VPR_H3D_CONTROL '%s'", name.c_str());
        return e_h3d_control::OFF;
    }();
    return value;
}

/** @brief Parse a finite bounded control parameter. */
double setting(const char* name, double fallback, double lower, double upper) {
    const char* text = std::getenv(name);
    if (!text) return fallback;
    char* end = nullptr;
    double value = std::strtod(text, &end);
    if (end == text || *end || !std::isfinite(value) || value < lower || value > upper)
        VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "%s must be finite and in [%g,%g]", name, lower, upper);
    return value;
}

std::unordered_map<ParentNetId, t_h3d_planar_guide> guides;
bool initialized = false;
bool lut_loaded = false;
size_t skipped = 0, cells = 0;
double seconds = 0.;

/** @brief Build a reproducible XY guide; VPR retains layer assignment. */
t_h3d_planar_guide build(ParentNetId net) {
    const auto& graph = g_vpr_ctx.device().rr_graph;
    const auto& terminals = g_vpr_ctx.routing().net_rr_terminals[net];
    t_h3d_planar_guide result;
    result.beta = setting("VPR_H3D_CONTROL_BETA", .6, 0., .99);
    result.benefit.resize(terminals.size(), 0.);
    std::map<std::pair<int, int>, int> unique;
    for (RRNodeId node : terminals)
        unique.emplace(std::pair{graph.node_xlow(node), graph.node_ylow(node)}, 0);
    // Explicit bounded-work fallback, not a claim about FLUTE's own limits.
    if (unique.size() < 2 || unique.size() > 512) {
        ++skipped;
        return result;
    }
    std::vector<int> xs, ys;
    for (auto& [xy, id] : unique) {
        id = xs.size();
        xs.push_back(xy.first);
        ys.push_back(xy.second);
    }
    auto tree = Flute::flute(xs.size(), xs.data(), ys.data(), FLUTE_ACCURACY);
    int count = 2 * tree.deg - 2;
    std::vector<std::vector<int>> adjacent(count);
    int root = -1;
    std::map<std::pair<int, int>, int> node_at;
    for (int i = 0; i < count; ++i) {
        const auto& a = tree.branch[i];
        node_at.emplace(std::pair{a.x, a.y}, i);
        if (a.n != i) {
            adjacent[i].push_back(a.n);
            adjacent[a.n].push_back(i);
        }
    }
    root = node_at.at({graph.node_xlow(terminals[0]), graph.node_ylow(terminals[0])});
    std::vector<int> parent(count, -1), order{root}, load(count, 0);
    parent[root] = root;
    for (size_t i = 0; i < order.size(); ++i)
        for (int next : adjacent[order[i]])
            if (parent[next] < 0) {
                parent[next] = order[i];
                order.push_back(next);
            }
    VTR_ASSERT(order.size() == size_t(count));
    for (size_t pin = 1; pin < terminals.size(); ++pin)
        ++load[node_at.at({graph.node_xlow(terminals[pin]), graph.node_ylow(terminals[pin])})];
    for (auto it = order.rbegin(); it != order.rend(); ++it)
        if (*it != root) load[parent[*it]] += load[*it];

    int xmax = *std::max_element(xs.begin(), xs.end());
    int ymax = *std::max_element(ys.begin(), ys.end());
    result.xmin = *std::min_element(xs.begin(), xs.end());
    result.ymin = *std::min_element(ys.begin(), ys.end());
    result.width = xmax - result.xmin + 1;
    result.height = ymax - result.ymin + 1;
    result.potential.assign(size_t(result.width) * result.height, 0.f);
    auto seed = [&](int x, int y, float value) {
        auto& cell = result.potential[size_t(y - result.ymin) * result.width + x - result.xmin];
        cell = std::max(cell, value);
    };
    // A deterministic x-then-y L embedding. This does not reproduce
    // PathSteiner's optimized diagonal decomposition or hard corridors.
    for (int child : order) {
        if (child == root) continue;
        const auto& a = tree.branch[parent[child]];
        const auto& b = tree.branch[child];
        float value = mode() == e_h3d_control::FLUTE_SOFT ? 1.f : 1.f + std::log1p(load[child]);
        for (int x = std::min(a.x, b.x); x <= std::max(a.x, b.x); ++x)
            seed(x, a.y, value);
        for (int y = std::min(a.y, b.y); y <= std::max(a.y, b.y); ++y)
            seed(b.x, y, value);
    }
    for (size_t pin = 1; pin < terminals.size(); ++pin) {
        int node = node_at.at({graph.node_xlow(terminals[pin]), graph.node_ylow(terminals[pin])});
        while (node != root) {
            const auto& a = tree.branch[node];
            const auto& b = tree.branch[parent[node]];
            result.benefit[pin] += std::max(0, load[node] - 1) * (std::abs(a.x - b.x) + std::abs(a.y - b.y));
            node = parent[node];
        }
    }
    Flute::free_tree(tree);
    if (mode() == e_h3d_control::STEINER_FIELD) {
        // Phi(x)=max_e [(1+log(1+load_e))*exp(-L1(x,e)/sigma)],
        // normalized to [0,1]. This is our stated control formula; the
        // inaccessible potential-field paper's detailed formula is not claimed.
        float decay = std::exp(-1. / setting("VPR_H3D_CONTROL_SIGMA", 3., .1, 100.));
        using Entry = std::pair<float, size_t>;
        std::priority_queue<Entry> frontier;
        for (size_t i = 0; i < result.potential.size(); ++i)
            if (result.potential[i] > 0.f) frontier.emplace(result.potential[i], i);
        while (!frontier.empty()) {
            auto [value, i] = frontier.top();
            frontier.pop();
            if (value < result.potential[i]) continue;
            int x = i % result.width, y = i / result.width;
            for (auto [dx, dy] : {std::pair{-1, 0}, {1, 0}, {0, -1}, {0, 1}}) {
                int nx = x + dx, ny = y + dy;
                if (nx < 0 || ny < 0 || nx >= result.width || ny >= result.height) continue;
                size_t next = size_t(ny) * result.width + nx;
                float candidate = value * decay;
                if (candidate > result.potential[next]) {
                    result.potential[next] = candidate;
                    frontier.emplace(candidate, next);
                }
            }
        }
        float maximum = *std::max_element(result.potential.begin(), result.potential.end());
        for (auto& value : result.potential)
            value /= maximum;
    }
    cells += result.potential.size();
    return result;
}
} // namespace

void h3d_control_iteration(int iteration, bool is_flat) {
    if (mode() == e_h3d_control::OFF || iteration != 1) return;
    if (is_flat) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D controls currently require serial clustered routing");
    auto start = std::chrono::steady_clock::now();
    guides.clear();
    skipped = cells = 0;
    seconds = 0.;
    if (!lut_loaded) {
        const char* directory = std::getenv("VPR_H3D_FLUTE_LUT");
        if (!directory) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D controls require explicit VPR_H3D_FLUTE_LUT directory");
        Flute::readLUT(directory);
        lut_loaded = true;
    }
    initialized = true;
    seconds += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    VTR_LOG("H3D_CONTROL_INIT mode=%s xy_projected=1 original_paper_reproduction=0\n", mode() == e_h3d_control::FLUTE_SOFT ? "flute_soft" : "steiner_field");
}

void h3d_control_prepare(ParentNetId net) {
    if (mode() == e_h3d_control::OFF) return;
    if (!initialized) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "H3D controls require serial routing");
    if (guides.contains(net)) return;
    auto start = std::chrono::steady_clock::now();
    guides.emplace(net, build(net));
    seconds += std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

const t_h3d_planar_guide* h3d_control_guide(ParentNetId net) {
    if (mode() == e_h3d_control::OFF) return nullptr;
    const auto& result = guides.at(net);
    return result.potential.empty() ? nullptr : &result;
}

void h3d_control_sort(ParentNetId net, std::vector<size_t>& pins, const std::vector<float>& criticality) {
    if (mode() != e_h3d_control::STEINER_FIELD) return;
    const auto& guide = guides.at(net);
    std::stable_sort(pins.begin(), pins.end(), [&](int a, int b) {
        return (1. + 4. * criticality[a]) * (1. + std::log1p(guide.benefit[a]))
               > (1. + 4. * criticality[b]) * (1. + std::log1p(guide.benefit[b]));
    });
}

float h3d_control_multiplier(const t_h3d_planar_guide& guide, RRNodeId node) {
    const auto& graph = g_vpr_ctx.device().rr_graph;
    auto type = graph.node_type(node);
    if (type != e_rr_type::CHANX && type != e_rr_type::CHANY && type != e_rr_type::CHANZ) return 1.f;
    int x = (graph.node_xlow(node) + graph.node_xhigh(node)) / 2 - guide.xmin;
    int y = (graph.node_ylow(node) + graph.node_yhigh(node)) / 2 - guide.ymin;
    if (x < 0 || y < 0 || x >= guide.width || y >= guide.height) return 1.f;
    return 1.f - guide.beta * guide.potential[size_t(y) * guide.width + x];
}

void h3d_control_log() {
    if (mode() != e_h3d_control::OFF)
        VTR_LOG("H3D_CONTROL nets=%zu skipped_degree=%zu cells=%zu preprocessing_seconds=%.6f\n", guides.size(), skipped, cells, seconds);
}
