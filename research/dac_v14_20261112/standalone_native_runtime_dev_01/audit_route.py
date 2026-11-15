"""Audit an explicit route and graph without historical experiment dependencies."""
import argparse
from pathlib import Path
import runtime_audit as study
from runtime_common import write_json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph',type=Path,required=True);p.add_argument('--route',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    graph,route=a.graph.resolve(),a.route.resolve()
    study.cr.graph_records=study.records
    evidence=study.cr.batch_graph_evidence(graph,[route])
    audit=study.cr.audit(graph,route,graph_evidence=evidence)
    result=dict(audit=audit,physical_metrics=study.physical_route_metrics(route,evidence) if audit['passed'] else None,
        VPR_calls_new=0,qualification='Scoped physical audit only; native FULL and endpoint STA remain separately required.')
    write_json(a.output,result)
    return 0 if audit['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
