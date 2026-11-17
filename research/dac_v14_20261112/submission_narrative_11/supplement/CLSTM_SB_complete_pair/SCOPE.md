# CLSTM-small SB-only full pair

Both original complete flows and the registered raw/native, raw/domain and actual-pair gates passed. The source circuit is already known from historical Hybrid-O runs; the graph configuration and actual placement both differ. This is not a new circuit family or an isolated architecture comparison.

The complete N/D costs are single-sequence observations, not interleaved timing. Memory peaks are sampled; native/domain retain 7/5 missing memory observations. Original verifier costs and all three additional read-only stage costs are separate. No native or STA query was repeated for admission.

Seven native resource attempts include four accepts and three legal policy rejections; domain accepts two guided groups with no release events and skips the optional native diagnostic. Both timing phases retain two failed search transactions, a legal faster candidate rejected by the fixed SB cap, and a legal non-improving candidate. Final quality never borrows the rejected faster candidate. Mechanism attribution and the actual first-group match are in mechanism_summary.json. Full-state/byte/request/STA/physical gates and endpoint vectors are retained in the role and pair receipts.
