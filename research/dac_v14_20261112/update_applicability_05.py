"""Correct mechanism trigger wording without changing historical evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil

D = Path(__file__).resolve().parent
old = D / 'mechanism_applicability_current_04'
new = D / 'mechanism_applicability_current_05'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = json.loads((old / 'completion.json').read_text())
assert receipt['passed']
for name, expected in receipt['artifact_sha256'].items():
    assert digest(old / name) == expected
paper = D / 'submission_narrative_15/main.tex'
assert 'All nine guided BNN resource groups have zero release events' in paper.read_text()
before = '筛选规则只能提出可执行机会：需要完整共享分支、有限可用时序余量、域阻塞的实际失败或容量owner见证，以及整组合法与预算接受；无上述见证不编造机制收益。'
after = '筛选规则只能提出可执行机会：完整共享分支与有限可用时序余量用于选择共享域尝试；实际域搜索失败时才考虑按网释放，有受支持的容量阻塞见证时才考虑扩大owner协调范围。两者是各自条件触发的机制，不是每次共享域搜索的前置条件；BNN九个已核验域组均无释放事件。最终候选须整组合法并满足预算；机制收益按实际执行和匹配对照分别归因。'
text = (old / 'APPLICABILITY.md').read_text()
assert text.count(before) == 1
new.mkdir(exist_ok=False)
shutil.copyfile(old / 'rows.json', new / 'rows.json')
(new / 'APPLICABILITY.md').write_text(text.replace(before, after).replace('投稿14主表', '投稿15主表'))
result = {'passed': True, 'updated_at': datetime.now(timezone.utc).isoformat(),
          'complete_pair_rows': receipt['complete_pair_rows'], 'pending_rows': receipt['pending_rows'],
          'new_native_or_STA_calls': 0, 'prior_snapshot_preserved': True,
          'qualification': 'Correct mechanism trigger attribution; no quality, timing, or historical receipt changes.',
          'source_sha256': {str(p): digest(p) for p in [Path(__file__).resolve(), old / 'completion.json', old / 'rows.json', old / 'APPLICABILITY.md', paper]},
          'artifact_sha256': {n: digest(new / n) for n in ['rows.json', 'APPLICABILITY.md']}}
(new / 'completion.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'passed': True, 'rows_unchanged': digest(old / 'rows.json') == digest(new / 'rows.json'), 'new_native_or_STA_calls': 0}))
