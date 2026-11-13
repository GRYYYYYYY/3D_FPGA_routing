#pragma once

#include "h3d_resumable_delay_search.h"
#include <algorithm>
#include <memory>

/** @brief Bounded endpoint-frontier cache for one immutable graph/weight epoch.
 * Keys identify endpoint AND direction. Slot reservations bound container entry
 * counts, not allocator bytes; the caller must retain its process memory guard.
 * A bounded, non-evicting ledger preserves work charges after LRU eviction.
 * A full ledger refuses new keys rather than silently granting fresh budgets.
 * All calls are sequential. Returned values are copies, never dangling handles.
 */
class H3dDelayFrontierCache {
  public:
    struct Limits {
        size_t states, keys, nodes_per_state, heap_per_state;
        size_t endpoint_settlements, aggregate_settlements;
    };
    enum class Stop { SEARCH, KEY_LIMIT, WORK_LIMIT };
    struct Result {
        Stop stop = Stop::SEARCH;
        std::optional<H3dResumableDelaySearch::e_stop> search_stop;
        size_t newly_settled = 0;
        std::vector<std::optional<double>> distances;
    };
    struct Stats {
        size_t work = 0, evictions = 0, restarts = 0, peak_states = 0;
        size_t live_states = 0, ledger_keys = 0;
    };

    explicit H3dDelayFrontierCache(Limits limits) : limits_(limits) {
        if (!limits.states || !limits.keys || !limits.nodes_per_state || !limits.heap_per_state)
            throw std::invalid_argument("nonzero cache storage limits required");
    }

    Stats stats() const {
        auto result = stats_;
        result.live_states = states_.size(); result.ledger_keys = ledger_.size();
        return result;
    }

    template<typename Terminal, typename Expand>
    Result query(size_t key, size_t source, const std::vector<size_t>& targets,
                 size_t quota, Terminal terminal, Expand expand) {
        Result result; result.distances.resize(targets.size());
        for (auto target : targets)
            if (!terminal(target)) throw std::invalid_argument("requested goal is not terminal");
        auto known = ledger_.find(key);
        if (known == ledger_.end()) {
            if (ledger_.size() >= limits_.keys) {result.stop = Stop::KEY_LIMIT; return result;}
            known = ledger_.emplace(key, Ledger{source, 0, false}).first;
        }
        auto& ledger = known->second;
        if (ledger.source != source) throw std::invalid_argument("cache key changed endpoint");
        auto state = states_.find(key);
        size_t remaining = std::min(limits_.endpoint_settlements - ledger.work,
                                    limits_.aggregate_settlements - stats_.work);
        // Cached exact answers remain available after the global work cap.
        if (state == states_.end() && !remaining && !targets.empty()) {
            result.stop = Stop::WORK_LIMIT; return result;
        }
        if (state == states_.end()) {
            if (states_.size() >= limits_.states) {
                auto victim = std::min_element(states_.begin(), states_.end(),
                    [](const auto& a, const auto& b) {return a.second.used < b.second.used;});
                states_.erase(victim); ++stats_.evictions;
            }
            auto search = std::make_unique<H3dResumableDelaySearch>(source,
                limits_.endpoint_settlements - ledger.work, limits_.nodes_per_state, limits_.heap_per_state);
            state = states_.emplace(key, State{std::move(search), 0}).first;
            if (ledger.admitted) ++stats_.restarts;
            ledger.admitted = true;
            stats_.peak_states = std::max(stats_.peak_states, states_.size());
        }
        state->second.used = ++clock_;
        try {
            auto answer = state->second.search->query(targets, std::min(quota, remaining), terminal, expand);
            result.search_stop = answer.stop;
            result.newly_settled = answer.newly_settled;
            ledger.work += answer.newly_settled; stats_.work += answer.newly_settled;
            for (size_t i = 0; i < targets.size(); ++i)
                result.distances[i] = state->second.search->terminal_distance(targets[i]);
            if (!remaining && answer.stop != H3dResumableDelaySearch::e_stop::TARGETS_MET)
                result.stop = Stop::WORK_LIMIT;
        } catch (...) {
            // Invalid graphs/allocation failures cannot yield an uncharged retry.
            // Conservatively retire all remaining admitted work, then propagate.
            ledger.work += remaining; stats_.work += remaining;
            states_.erase(state);
            throw;
        }
        return result;
    }

  private:
    struct Ledger {size_t source, work; bool admitted;};
    struct State {std::unique_ptr<H3dResumableDelaySearch> search; size_t used;};
    Limits limits_;
    Stats stats_;
    size_t clock_ = 0;
    std::unordered_map<size_t, Ledger> ledger_;
    std::unordered_map<size_t, State> states_;
};
