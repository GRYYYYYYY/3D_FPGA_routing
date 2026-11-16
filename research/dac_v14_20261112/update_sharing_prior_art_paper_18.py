"""Acknowledge negotiated same-net sharing; no experimental or superiority claim."""
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

parent_path=D/'input_seed_paper_binding_17.json';parent=read(parent_path)
previous=Path(parent['snapshot']);p=D/'paper';e=D/'sharing_prior_art_paper_evidence_18'
assert not e.exists() and sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
e.mkdir()
prior_sources=D/'routing_related_work_01/sources.json'
assert read(prior_sources)['primary_sources_only']
sources=dict(reviewed_at=datetime.now(timezone.utc).isoformat(),primary_sources_only=True,
    newly_read_source=dict(key='croute',title='CRoute: A Fast High-quality Timing-driven Connection-based FPGA Router',
        authors=['Dries Vercruyce','Elias Vansteenkiste','Dirk Stroobandt'],year=2019,doi='10.1109/FCCM.2019.00017',
        primary_url='https://backoffice.biblio.ugent.be/download/8640095/8640096',
        locators=['SectionII-B:Negotiated Sharing Mechanism,pp.2-3','SectionIV-E:Reroute Critical Connections,p.5','SectionV:Experiments,p.6'],
        paraphrase='Same-source connections share costs through a sharing factor. Uncongested critical connections are rerouted. The reported routing-time boundary excludes RRG generation.',
        supports_main='Same-net sharing and critical-connection rerouting are prior ingredients, not new mechanisms by themselves.',
        comparison_limit='No reproduced CRoute baseline; different input suite, buffered device model and time boundary prohibit cross-paper numeric ranking.'),
    retained_prior_primary_review=str(prior_sources),retained_prior_primary_review_sha256=sha(prior_sources),
    new_experimental_observations=0,new_independent_inputs=0,third_party_paper_republished=False,
    qualification='Fresh full CRoute manuscript reading strengthens existing limited citation. AIR/Liu context is retained from the previously sealed primary-source review; no claim that unexamined prior work lacks a mechanism.')
write(e/'sources.json',sources)
(e/'contribution_comparison.md').write_text('''# Contribution and attribution map

This comparison concerns mechanisms and evidence scopes, not a reproduced ranking
against external routers. Primary references are bound in sources.json and the
previous sealed routing-related-work review. Existing timing, sharing and repair
primitives are explicitly acknowledged.

| Reference or control | Established ingredient or observed effect | Scope of this manuscript's comparison |
|---|---|---|
| Liu et al., 2014, publisher abstract | Critical-path-related incremental rerouting after PathFinder | Current timing repair by itself is prior art. The present tests concern fixed-envelope joint decisions and resource tradeoffs. |
| AIR, 2020, Sections II/IV | Retained legal routing and incremental improvement; congestion history persists across convergences | Imported price reset is shared by our matched arms. In-router continuation with preserved prices is unvalidated; no external speed claim. |
| CRoute, 2019, Sections II-B/IV-E | Negotiated same-net sharing and rerouting of uncongested critical connections | Our local comparison changes permitted cross-layer sources after pruning; ordinary sharing and timing rerouting are not themselves new. |
| Same-source native/domain controls | Crossing-domain restrictions can change feasible timing/resource tradeoffs | Matched scopes and full-candidate decisions support only their measured contexts. Eligibility is not a general gain predictor. |
| Failure-release controls | Robot fixed-scope release can restore feasibility while retaining a resource tradeoff | Whole-flow benefit remains unconfirmed. All nine audited BNN guided resource roles have zero release events, so their gains are not attributed to executed release. |
| Blocking-owner controls | Identical native/domain R1 owner outputs support expanded coordination scope | Attribute those results to coordination. Partial robot-p1 owner reentries do not establish a complete-controller benefit. |

The CRoute manuscript's Section V excludes RRG generation from routing time.
Our cold complete flows include their registered graph/index construction and
all repair checks. Different boundaries and inputs cannot yield a valid numeric
cross-paper time comparison. No external performance numbers are transferred.

The fully integrated frozen controller still needs the registered CP1r3 three-input,
six-role confirmation. This editorial update creates no independent input, actual
native/STA execution, treatment effect, whole-flow result or new main-table row.
''')
old=(previous/'current_repair_main.tex').read_text()
before=r'CRoute uses timing-driven connection-based routing~\cite{croute}. Current timing, retained trees and incremental rerouting are therefore established ingredients.'
after=r'CRoute combines connection-based routing with negotiated same-net sharing and reroutes uncongested critical connections~\cite{croute}. Current STA, tree sharing and incremental repair are therefore established ingredients.'
assert old.count(before)==1
source=p/'current_repair_sharing_prior_art_18.tex';source.write_text(old.replace(before,after))
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),changes=[[before,after]],
    main_table_rows=43,new_native_calls=0,new_STA_calls=0,new_independent_inputs=0,new_full_method_results=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,prior_sources,e/'sources.json',e/'contribution_comparison.md']}))
print(dict(source=str(source),changed_passages=1,new_native_calls=0,new_benefit_claims=0))
