# BNN first-group crossing-cost contrast

The first ranked group of the matched BNN interleaved pair restores the same eight connections from eight nets. The common source has 2059567 wire units, 94 SB and 5062 CB. The CPD cap is 13.607436067 ns and the wire cap is 2061627. The three new unrestricted trials use the previously developed robot cost-only worker. The zero setting reproduces the historical unrestricted candidate, ordered query work, endpoints and policy decision.

| Search | Wire | SB | CB | Original decision |
|---|---:|---:|---:|---|
| Native / zero | 2059583 | 88 | 5062 | Accept |
| Weight 0.5 | 2059615 | 87 | 5062 | Accept |
| Weight 2 | 2059671 | 86 | 5062 | Accept |
| Reused retained-crossing domain | 2059667 | 86 | 5062 | Accept |

Weight 2 matches the domain candidate on CPD, SB, CB and every setup and hold component. It costs four more wire units. This fixed-group result identifies a simple explanation for the vertical saving on that scope. A complete crossing-cost controller comparison remains open. The complete native/domain BNN result and its 24.91% timing overhead retain their original comparison boundary. The shared imported experiment took 1259.24 seconds, with all pressure retries, source checks and candidate validations included.

The adjacent data files include all 26 complete pairs, endpoint distributions, site changes, fixed-group counts and work. The two full BNN routes have occupancies 5144 and 5103. The latter reaches the fixed-terminal bound and vacates exactly 39 SB pairs and two CB output sources. The largest setup loss is 3.694 ns on BNN and 2.988 ns on LSTM. The native worst-slack neighborhoods (1 ns) have identical paired setup on both circuits.

The evidence snapshot extends submission 19. Future weighted-controller runs would affect the full comparison and cost interpretation. Further TPU owner work concerns local attribution only.
