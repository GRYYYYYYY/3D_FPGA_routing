# Literature controls and reproduction boundaries

The subsequent [LaZagna paper-era comparison](../results/lazagna_reproduction/report.html)
is a separate toolchain/architecture study. It is not a third soft-guide variant
on the original A0 graph. Its exact DSP exit correspondence, non-equivalent planar
and vertical connections, published clock-configuration conflict, and observed
crossing-switch delays must be considered before interpreting differences in CPD
or routing success. The original conditional A3 −1.39% result is unchanged and
does not compare against LaZagna.

Both controls run in the same pinned native-3D VPR and reuse the exact packed
netlist, placement and directed RRG as A0–A4. They retain VPR's native timing,
present/history congestion, capacity negotiation and final FULL checks. Their
projection is only a preference; no geometric segment becomes a legal graph edge.

## Retrieved evidence

PathSteiner's [paper](https://www.shashwatshrivastava.com/documents/FCCM26_PathSteiner.pdf)
and [published artifact](https://zenodo.org/records/19204522) were inspected.
Its actual launcher disables timing analysis and sets maximum criticality to
zero. Its FLUTE topology, optimized L decomposition, hard coarse confinement,
coarse-path lookahead, progress-triggered release, retained legal branches and
history-cost schedule form a larger method than simply changing sink order.
The artifact's VTR base is `33c518fc6187d5f0a3e5022f26ce7e3c26599904`.
The concatenated patch was reconstructed for selected files with `patch -p1`;
all 31 relevant sections applied without rejection.

The [Steiner potential-field paper's publisher abstract](https://ieeexplore.ieee.org/abstract/document/11552685)
supports topology-aware sink ordering and A* modulation, but its full formula
and source were not obtained. This implementation must not be attributed to the
author or presented as a faithful reproduction of that paper's results.

## Implemented controls

The FLUTE implementation is the BSD-3-licensed Iowa State code included in the
PathSteiner artifact. Its copyright notice is retained in `h3d_flute.cpp/.h`.
Only its local filenames and explicit LUT-directory argument were adapted.
LUTs are pinned to the official OpenROAD-attic flute3 repository commit
`8c2387eb0fc6d66e1d8a283031d37444fc29a003`; paths and SHA256 hashes are recorded in
`configs/flute_sources.lock.json`. The run manifest also hashes both LUT files.
Accuracy is 10, matching the retrieved source's constant. Duplicate XY terminal
coordinates are collapsed for FLUTE, while real sink multiplicity is retained
when computing shared-trunk benefits.

- `VPR_H3D_CONTROL=flute_soft`: compute a static XY FLUTE tree, orient it from
  the actual source, embed each edge using deterministic x-then-y L segments,
  and multiply configurable wire congestion cost by `1-beta` when the resource
  midpoint lies on the union of those segments. Otherwise its multiplier is 1.
  The preference is projected onto every layer and persists across iterations.
  This is a static FLUTE soft-guide control, not PathSteiner's full algorithm.
- `VPR_H3D_CONTROL=steiner_field`: start from that same tree. An edge with `m`
  downstream sinks has strength `1+log(1+m)`. Define
  `Phi(x)=max_e strength(e)*exp(-L1(x,e)/sigma)`, normalize the maximum to 1,
  and apply multiplier `1-beta*Phi` to configurable wire congestion. The field
  is stored inside the net's XY bounding box and is zero outside. A resource
  samples it at its integer midpoint. Sink `i` is ordered by descending
  `(1+4*criticality_i)*(1+log(1+sum_path (m_e-1)*length_e))` with stable ties.
  These are our explicit control formulas, not formulas claimed from the
  inaccessible paper. They alter the cost/order heuristic, not actual RC.

Defaults are `beta=0.6`, `sigma=3` grid units, tunable through
`VPR_H3D_CONTROL_BETA` and `VPR_H3D_CONTROL_SIGMA`. Beta is restricted to
`[0,0.99]` so costs stay nonnegative. Nets with fewer than 2 or more than 512
unique XY sites skip guidance and are counted. All LUT loading, tree/field
construction and retained-cell counts are reported; lookup and sorting overhead
are included in total routing time. A failed guided search retries without
experimental preferences before the ordinary bounding-box fallback.

## Interpretation

These controls test whether inexpensive static planar topology information or
a generic field/order heuristic explains improvements attributed to cross-layer
planning. They cannot establish superiority over either original published
method. A faithful original-method comparison would require a separately
validated port of all algorithm stages, compatible evaluation conditions and,
for the potential-field work, access to its full specification or code.
