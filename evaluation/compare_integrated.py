"""Re-run the combined search and original PR on both lexical fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from collections import defaultdict

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / 'aayatun-research'
REVISIONS = {'pr1': '928ff86', 'integrated': 'bc755b9'}


def main():
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    engines = {}
    for name, rev in REVISIONS.items():
        module = types.ModuleType(name)
        source = subprocess.check_output(['git', 'show', rev + ':searchtool.py'])
        exec(compile(source, rev, 'exec'), module.__dict__)
        module._load_vocab()
        module._load_bk_tree()
        engines[name] = module
    reports = {}
    for fixture in ['challenge_v2.jsonl', 'difficult_multiword.jsonl']:
        data = (HERE / fixture).read_bytes()
        cases = [json.loads(line) for line in data.splitlines()]
        runs = []
        groups = defaultdict(list)
        regressions = []
        for index, case in enumerate(cases):
            rankings = {}
            ranks = {}
            anchors = set(case.get('expected', [])) or {
                ref for ref, grade in case.get('judgments', {}).items() if grade == 2}
            for name, engine in engines.items():
                hits, _ = engine.index_search(case['query'], 10, field=case['field'])
                rankings[name] = [f"{h['surah']}:{h['verse']}" for h in hits]
                ranks[name] = next((i for i, ref in enumerate(rankings[name], 1)
                                    if ref in anchors), 0)
            runs.append({'id': case['id'], 'rankings': rankings})
            if anchors:
                for group in ['all', case.get('intent', case.get('kind', 'other'))]:
                    groups[group].append(ranks)
                if ranks['pr1'] and (not ranks['integrated'] or ranks['integrated'] > ranks['pr1']):
                    regressions.append({'id': case['id'], 'query': case['query'], 'ranks': ranks})
            if index % 100 == 0:
                print(fixture, index, '/', len(cases), flush=True)
        metrics = {}
        for group, rows in groups.items():
            metrics[group] = {}
            for name in engines:
                values = [r[name] for r in rows]
                metrics[group][name] = {
                    'n': len(rows), 'top1': sum(r == 1 for r in values),
                    'top5': sum(0 < r <= 5 for r in values),
                    'mrr10': sum(1/r if r else 0 for r in values) / len(rows)}
        reports[fixture] = {'sha256': hashlib.sha256(data).hexdigest(), 'metrics': metrics,
                            'regressions': regressions, 'runs': runs}
        print(fixture, metrics['all'], 'rank regressions', len(regressions), flush=True)
    (HERE / 'integrated_results.json').write_text(
        json.dumps({'revisions': REVISIONS, 'fixtures': reports}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf8')


if __name__ == '__main__':
    main()
