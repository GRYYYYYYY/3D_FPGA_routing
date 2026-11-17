"""Use the original pair gate's own lock; do not reacquire it in a wrapper."""
from pathlib import Path
import admit_cp1r5_frisc_base_01 as base
base.ROOT=Path(__file__).resolve().parent/'FRISC_sdc_readonly_02'
assert not (base.ROOT/'pair').exists()
base.pair()
