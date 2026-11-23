"""Compare the root-search branch with its parent on the difficult fixture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / 'aayatun-research'
REVISIONS = {
    'parent': '7271fdb6107950701f7c91119d63923f7a7f4f83',
    'root': 'bc755b9',
}


def main():
    fixture = (HERE / 'difficult_multiword.jsonl').read_bytes()
    cases = [json.loads(line) for line in fixture.splitlines()]
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    engines = {}
    for name, revision in REVISIONS.items():
        engine = types.ModuleType(name)
        source = subprocess.check_output(['git', 'show', revision + ':searchtool.py'])
        exec(compile(source, revision + ':searchtool.py', 'exec'), engine.__dict__)
        engine._load_vocab()
        engine._load_bk_tree()
        engines[name] = engine
    output = []
    for case in cases:
        rankings = {}
        for name, engine in engines.items():
            hits, _ = engine.index_search(case['query'], 10, field=case['field'])
            rankings[name] = [f"{hit['surah']}:{hit['verse']}" for hit in hits]
        output.append({'id': case['id'], 'rankings': rankings})
        print(case['id'], flush=True)
    report = {'fixture_sha256': hashlib.sha256(fixture).hexdigest(),
              'revisions': REVISIONS, 'runs': output}
    (HERE / 'root_comparison.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
