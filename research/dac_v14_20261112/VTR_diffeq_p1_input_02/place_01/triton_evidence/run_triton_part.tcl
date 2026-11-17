if {[catch {
  triton_part_hypergraph -hypergraph_file {triton_hypergraph.hgr} -num_parts 2 -balance_constraint 0.03 -seed 1
} message]} { puts stderr $message; exit 1 }
exit 0
