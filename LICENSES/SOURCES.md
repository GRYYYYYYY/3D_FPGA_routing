# Third-party source notices

- VTR: https://github.com/verilog-to-routing/vtr-verilog-to-routing, commit `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`. See `VTR-LICENSE.md`; it covers the modified VPR source and native Hecate architecture source subject to the stated component exceptions.
- Beyond-Flatland: https://github.com/IY2002/Beyond-Flatland, branch `vtr-3d`, commit `84ba44acf1bad597bc5a9d1f615415870e178a86`. Its retrieved root notice is retained in `Beyond-Flatland-LICENSE.md`. The hybrid architecture provenance identifies the sections adapted from its architecture.
- FLUTE: Iowa State BSD-3 code from the PathSteiner artifact, with the original notice retained in the code and `FLUTE-BSD3.txt`. LUT provenance is pinned in `configs/flute_sources.lock.json`.
- OpenROAD: https://github.com/The-OpenROAD-Project/OpenROAD, commit `a008522d88b669ac4c985609533cf5a3d2649222`. The partition-tool source patch in `patches/snapshot_20261109/` retains upstream notices; see `OpenROAD-LICENSE.txt`.
- Modern LaZagna VTR fork: https://github.com/IY2002/vtr-verilog-to-routing, commit `5abd3acaa603e037ec390fa545b04301f13d57e0`. This snapshot preserves build-portability changes separately from the native routing algorithm.

Original benchmark BLIFs, external source trees and paper PDFs remain external dependencies and are not embedded in the compact delivery ZIP. Their source URLs, commits and hashes are retained in the project manifests.
