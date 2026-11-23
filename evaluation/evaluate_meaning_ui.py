"""Evaluate the configured meaning-search UI on English translation questions."""
import json
import hashlib
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / 'aayatun-research'


def main():
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    from app import app
    client = app.test_client()
    fixture = (HERE / 'challenge_v2.jsonl').read_bytes()
    cases = [json.loads(line) for line in fixture.splitlines()]
    cases = [c for c in cases if c['field'] == 'translation' and c['language'] == 'en'
             and c['intent'] == 'semantic' and 2 in c['judgments'].values()]
    runs = []
    for case in cases:
        response = client.post('/search/', data={
            'query_str': case['query'], 'search_mode': 'meaning',
            'target_field': 'translation:', 'limit': '10'})
        text = response.get_data(as_text=True)
        assert response.status_code == 200 and 'temporarily unavailable' not in text
        refs = re.findall(r'class="surahlink"[^>]*>\s*(\d+:\d+)', text)
        rank = next((i for i, ref in enumerate(refs, 1)
                     if case['judgments'].get(ref) == 2), 0)
        runs.append({'id': case['id'], 'refs': refs, 'rank': rank})
        print(case['id'], flush=True)
    report = {'dataset_sha256': hashlib.sha256(fixture).hexdigest(),
              'n': len(runs), 'top5': sum(0 < r['rank'] <= 5 for r in runs), 'runs': runs}
    (HERE / 'meaning_e2e_results.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('Result', report['top5'], '/', report['n'], flush=True)


if __name__ == '__main__':
    main()
