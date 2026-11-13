#pragma once

#include "rr_graph_view.h"

/** @brief Identify a real directed inter-layer edge between single-layer RR nodes.
 * No graph edges, delay values or capacities are created by this adapter. */
inline bool h3d_crosses_layers(const RRGraphView& graph, RRNodeId from, RRNodeId to) {
    return graph.node_layer_low(from) == graph.node_layer_high(from)
           && graph.node_layer_low(to) == graph.node_layer_high(to)
           && graph.node_layer_low(from) != graph.node_layer_low(to);
}

/** @brief Test whether a node is the source of an existing crossing edge. CB outputs
 * share the real OPIN capacity; SB half-node pairs use their real capacity. */
inline bool h3d_crossing_entry(const RRGraphView& graph, RRNodeId node) {
    for (auto edge : graph.node_out_edges(node))
        if (h3d_crosses_layers(graph, node, graph.edge_sink_node(node, edge))) return true;
    return false;
}
