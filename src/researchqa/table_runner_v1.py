"""Conservative, model-free table development runner; not final verification."""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from .latency_binding_v1 import bind_latency_mentions

NUMBER = r'[+-]?\d+(?:\.\d+)?'
VERSION = 'table-development-runner-v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def validate(packet):
    if not isinstance(packet.get('record_id'), str) or not packet['record_id']:
        raise ValueError('Missing record ID')
    if not isinstance(packet.get('claim'), str):
        raise ValueError('Missing claim text')
    rows = packet.get('table_cells')
    if not isinstance(rows, list) or len(rows) < 2 or not rows[0]:
        raise ValueError('Missing table cells')
    ids = set()
    for r, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(rows[0]):
            raise ValueError('Irregular table width')
        for c, cell in enumerate(row):
            if (not isinstance(cell, dict) or cell.get('cell_id') != f'r{r}_c{c}'
                or not isinstance(cell.get('text'), str)):
                raise ValueError('Invalid cell coordinates or text')
            if cell['cell_id'] in ids:
                raise ValueError('Duplicate cell ID')
            ids.add(cell['cell_id'])
    return rows


def changes(claim, rows):
    """Explicit change grammar only; no entity aliases or header inference."""
    pattern = (rf'\b(?P<verb>reduces|decreases|boosts|increases)\s+'
               rf'(?P<metric>[A-Za-z][A-Za-z0-9_-]*)\s+by\s+'
               rf'(?P<change>{NUMBER})\s*\(\s*from\s+(?P<old>{NUMBER})'
               rf'\s+to\s+(?P<new>{NUMBER})\s*\)')
    mentions = list(re.finditer(pattern, claim, re.I))
    if not mentions:
        return [], ['Explicit change grammar not matched.']
    targets = [row for row in rows[1:] if row[0]['text'].strip() and
               re.match(re.escape(row[0]['text'].strip()) + r'(?=\s)', claim, re.I)]
    baseline = re.search(r'\bcompared\s+to\s+(.+?)\s*[.]?\s*$', claim, re.I)
    if len(targets) != 1 or baseline is None:
        return [], ['Target/baseline method binding unresolved.']
    name = baseline.group(1).rstrip('.').strip().casefold()
    bases = [row for row in rows[1:] if row[0]['text'].strip().casefold() == name]
    if len(bases) != 1:
        return [], ['Baseline method is missing or ambiguous.']
    found, issues = [], []
    for m in mentions:
        cols = [i for i, cell in enumerate(rows[0])
                if cell['text'].strip().casefold() == m['metric'].casefold()]
        if len(cols) != 1:
            issues.append('Missing or ambiguous metric: ' + m['metric'])
            continue
        c = cols[0]
        old_text, new_text = bases[0][c]['text'].strip(), targets[0][c]['text'].strip()
        if not all(re.fullmatch(NUMBER, x) for x in (old_text, new_text)):
            issues.append('Missing or non-scalar source values: ' + m['metric'])
            continue
        old, new = Decimal(old_text), Decimal(new_text)
        delta = old-new if m['verb'].lower() in ('reduces','decreases') else new-old
        mismatches = [key for key, expected in
                      [('old',old),('new',new),('change',delta)]
                      if Decimal(m[key]) != expected]
        found.append({'adapter':'explicit_change', 'metric':m['metric'],
                      'claim_quote':m.group(0), 'claim_offsets':[m.start(),m.end()],
                      'source_cell_ids':[bases[0][c]['cell_id'],targets[0][c]['cell_id']],
                      'context_cell_ids':[bases[0][0]['cell_id'],targets[0][0]['cell_id'],rows[0][c]['cell_id']],
                      'source_values':[old_text,new_text], 'expected_change':str(delta),
                      'claimed_change':m['change'], 'mismatches':mismatches,
                      'numerical_decision':'Refuted' if mismatches else 'Supported'})
    return found, issues


def process(packet):
    start = time.perf_counter()
    base = {'record_id':packet.get('record_id'), 'model_calls':0,
            'scientific_prediction':None, 'complete_decomposition_verified':False,
            'full_scope_alignment_verified':False,
            'image_html_equivalence_verified':False}
    try:
        rows = validate(packet)
        latency = bind_latency_mentions(packet['claim'], rows, packet.get('caption'))
        checks = []
        for binding in latency['bindings']:
            equal = Decimal(binding['claim_value']) == Decimal(binding['source_value'])
            checks.append({'adapter':'latency', **binding,
                           'numerical_decision':'Supported' if equal else 'Refuted'})
        more, issues = changes(packet['claim'], rows)
        checks.extend(more)
        base.update(status='partial_numeric_checks' if checks else 'unresolved',
                    numerical_checks=checks,
                    unresolved=latency['unresolved'] + issues + [
                        'Scientific scope, unhandled claim components and image/HTML mapping remain unverified.'],
                    operational_decision='Insufficient Evidence')
    except (KeyError, ValueError, TypeError, ArithmeticError) as e:
        base.update(status='technical_failure', operational_decision='Technical Failure',
                    numerical_checks=[], error=f'{type(e).__name__}: {e}')
    base['elapsed_seconds'] = round(time.perf_counter()-start, 6)
    return base


def run(input_path, output_dir):
    input_path, output_dir = Path(input_path).resolve(), Path(output_dir).resolve()
    with input_path.open(encoding='utf-8') as f:
        packets = [json.loads(line) for line in f if line.strip()]
    ids = [p.get('record_id') for p in packets]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('Input record IDs must be unique nonempty strings')
    # Evaluation/review artifacts must not become input packets.
    forbidden = {'gold_label','label','reviewed_decision','prediction','review'}
    if any(forbidden & p.keys() or p.get('prediction') is not None for p in packets):
        # Prepared evidence packets contain prediction:null by design.
        bad = [p for p in packets if (forbidden-{'prediction'}) & p.keys()
               or p.get('prediction') is not None]
        if bad:
            raise ValueError('Evaluation/prediction fields are not allowed in inputs')
    settings = {'version':VERSION, 'input_sha256':sha(input_path),
                'runner_sha256':sha(__file__),
                'latency_adapter_sha256':sha(Path(__file__).with_name('latency_binding_v1.py')),
                'approval_policy':'Withhold full scientific decisions; scope and evidence correspondence unverified',
                'models_enabled':False}
    output_dir.mkdir(parents=True, exist_ok=True)
    settings_path = output_dir/'settings.json'
    if settings_path.exists():
        if json.loads(settings_path.read_text()) != settings:
            raise ValueError('Resume rejected: source inputs or code changed. Use a new output directory.')
    else:
        if any(output_dir.iterdir()):
            raise ValueError('Output directory is nonempty without settings')
        write(settings_path,settings)
    results=[]
    for packet in packets:
        key=hashlib.sha256(packet['record_id'].encode()).hexdigest()
        path=output_dir/(key+'.json')
        packet_hash=hashlib.sha256(json.dumps(packet,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if path.exists():
            result=json.loads(path.read_text())
            if result.get('record_id') != packet['record_id'] or result.get('packet_sha256') != packet_hash:
                raise ValueError('Saved record does not match input')
        else:
            result=process(packet)
            result['packet_sha256']=packet_hash
            write(path,result)
        results.append(result)
        print(packet['record_id'], result['status'], '| checks:',len(result['numerical_checks']),flush=True)
    summary={'purpose':'Partial table integration engineering run; not SciVer benchmark',
             'records':len(results),'status_counts':dict(Counter(r['status'] for r in results)),
             'operational_decisions':dict(Counter(r['operational_decision'] for r in results)),
             'numerical_checks':sum(len(r['numerical_checks']) for r in results),
             'model_calls':0,'scientific_predictions_generated':False,
             'assistant_reviews_consumed':False,'gold_labels_read':False,
             'runtime':{'python':sys.version.split()[0]},'settings':settings}
    summary_path=output_dir/'summary.json'
    if not summary_path.exists():
        write(summary_path,summary)
    print(json.dumps(summary,indent=2))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    run(args.inputs,args.output)

if __name__=='__main__':
    main()
