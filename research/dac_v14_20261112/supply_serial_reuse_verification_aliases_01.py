"""Supply byte-identical config aliases expected by the existing verifier.
Algorithm commands continue reading their originally frozen configs directory.
"""
from pathlib import Path
import time,shutil
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'complete_serial_reusable_graph_dev_01';owner=read(root/'queue/registration.json');aliases={}
while len(aliases)<2:
    for mode in ['paired','unrestricted']:
        case=root/mode
        if not case.exists():continue
        source=root/'configs'/(mode+'.json');target=case/'config.json'
        assert sha(source)==owner['source_sha256'][str(source.resolve())]
        if target.exists():assert sha(target)==sha(source)
        else:shutil.copy2(source,target)
        aliases[mode]=dict(source=str(source),verification_alias=str(target),sha256=sha(source))
    write(root/'config_verification_aliases.json',dict(passed=len(aliases)==2,aliases=aliases,qualification='Byte-identical output-side aliases for the generic verifier. Driver invocation, frozen inputs, selection and actual measurement are unchanged.'))
    live=process_identity(owner['pid'])
    if not live or live['state']=='Z' or live['start_ticks']!=owner['start_ticks']:break
    if len(aliases)<2:time.sleep(2)
