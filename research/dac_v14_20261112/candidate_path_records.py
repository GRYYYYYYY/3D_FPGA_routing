"""Strip only diagnostic elapsed time, retaining all physical/priced seconds."""
import re
from retained_prefix_workflow import original_records


def records(lines,allowed_prefixes=None):
    result=[]
    for line in original_records(lines,allowed_prefixes):
        if line.startswith('H3D_CANDIDATE_PATH_SUMMARY '):
            line=re.sub(r'\bseconds=\S+','seconds=<elapsed>',line)
        result.append(line)
    return result
