"""Re-run the two recorded OpenSearch configurations on both fixtures."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
FIELDS = {'all': ['ar', 'en', 'bn_tafsir', 'en_tafsir', 'ai', 'surah_name'],
          'ayah': ['ar'], 'translation': ['en'], 'bn_tafsir': ['bn_tafsir'],
          'en_tafsir': ['en_tafsir'], 'ai': ['ai']}


def call(path, data=None):
    req = urllib.request.Request('http://127.0.0.1:19200' + path,
                                 data=data.encode() if data else None,
                                 headers={'Content-Type': 'application/x-ndjson'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def main():
    version = call('/')['version']['number']
    assert call('/aayatun-eval-normalized/_count')['count'] == 6236
    output = {'version': version, 'index': 'aayatun-eval-normalized', 'fixtures': {}}
    for fixture in ['challenge_v2.jsonl', 'difficult_multiword.jsonl']:
        raw = (HERE / fixture).read_bytes()
        cases = [json.loads(line) for line in raw.splitlines()]
        runs = {c['id']: {} for c in cases}
        for mode in ['lexical', 'phrase']:
            for start in range(0, len(cases), 100):
                batch = cases[start:start + 100]
                lines = []
                for c in batch:
                    text = c['query'].strip('"')
                    base = {'multi_match': {'query': text, 'fields': FIELDS[c['field']]}}
                    query = base
                    if mode == 'phrase':
                        query = {'bool': {'must': [base], 'should': [
                            {'multi_match': {'query': text, 'fields': FIELDS[c['field']],
                                             'type': 'phrase', 'boost': 3}}]}}
                    lines.extend([json.dumps({'index': 'aayatun-eval-normalized'}),
                                  json.dumps({'size': 10, '_source': False, 'query': query})])
                response = call('/_msearch', '\n'.join(lines) + '\n')
                for c, result in zip(batch, response['responses']):
                    if 'error' in result:
                        raise RuntimeError(result['error'])
                    runs[c['id']][mode] = [h['_id'] for h in result['hits']['hits']]
            print(fixture, mode, 'complete', flush=True)
        output['fixtures'][fixture] = {
            'sha256': hashlib.sha256(raw).hexdigest(), 'runs': runs}
    (HERE / 'integrated_opensearch_results.json').write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
