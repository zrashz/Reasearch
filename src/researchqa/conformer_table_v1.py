"""Restricted conformer-table adapter; not a general scientific numerical extractor."""
import re,hashlib,xml.etree.ElementTree as ET
from decimal import Decimal,ROUND_HALF_UP

TEMPLATE=("On the {benchmark} benchmark, for conformer energy differences relative to CCSD(T)*/CBS "
          "within {limit} kcal/mol of each molecule's energy minimum, {entity} has an RMSD of {new} kcal/mol "
          "versus {base} kcal/mol for {baseline}, a {percent}% increase.")
PATTERN=re.compile(r"On the (?P<benchmark>[^,]+) benchmark, for conformer energy differences relative to CCSD\(T\)\*/CBS within (?P<limit>\d+(?:\.\d+)?) kcal/mol of each molecule's energy minimum, (?P<entity>[^,]+) has an RMSD of (?P<new>\d+(?:\.\d+)?) kcal/mol versus (?P<base>\d+(?:\.\d+)?) kcal/mol for (?P<baseline>[^,]+), a (?P<percent>\d+(?:\.\d+)?)% increase\.")
OBSERVED=re.compile(r"Training a model only to the smaller CCSD\(T\)\*/CBS data set \((?P<entity>[^)]+)\) results in a (?P<percent>\d+(?:\.\d+)?)% degradation in RMSD compared with the transfer learning model \((?P<baseline>[^)]+)\)\.")

def text(node):return ''.join(node.itertext()).strip()
def prepare(evidence):
    candidates=[]
    for eid,entry in evidence.items():
        if entry.get('modality')!='table':continue
        try:root=ET.fromstring(entry['text'])
        except (ET.ParseError,KeyError):continue
        caption=root.find('caption');table=root.find('table');foot=root.find('table-wrap-foot');label=root.find('label')
        if any(x is None for x in (caption,table,foot,label)):continue
        cap=text(caption)
        bench=re.fullmatch(r'Accuracy in predicting conformer energy differences on the (.+) benchmark',cap)
        if not bench or not re.search(r'kcal\s*mol.*−1',text(foot)):continue
        if any(c.get('colspan','1')!='1' or c.get('rowspan','1')!='1' for c in table.iter() if c.tag in {'th','td'}):continue
        headers=table.findall('./thead/tr')
        if len(headers)!=1:continue
        names=[text(c) for c in headers[0]]
        if len(names)<3 or names[0] or len(set(names))!=len(names):continue
        values={};cells={};invalid=False
        for ri,row in enumerate(table.findall('./tbody/tr')):
            cols=list(row)
            metric=''.join(cols[0].itertext()).strip() if cols else ''
            # Superscripts are footnote markers, not part of metric names.
            if cols:metric=(cols[0].text or '').strip()
            if metric!='RMSD':continue
            if values or len(cols)!=len(names):invalid=True;break
            for ci,(name,cell) in enumerate(zip(names[1:],cols[1:]),1):
                try:v=Decimal(text(cell))
                except Exception:invalid=True;break
                if not v.is_finite() or v<=0:invalid=True;break
                values[name]=str(v);cells[name]={'row':ri,'column':ci,'text':text(cell)}
        if invalid or not values:continue
        table_label=text(label)
        for pid,p in evidence.items():
            if p.get('modality')!='prose':continue
            source=p.get('text','')
            if bench[1] not in source or 'CCSD(T)*/CBS' not in source or 'RMSD' not in source:continue
            scope=re.search(re.escape(table_label)+r' only considers conformations within (\d+(?:\.\d+)?) kcal mol−1 of the energy minima for each molecule\.',source)
            if not scope:continue
            candidates.append({'table_id':eid,'prose_id':pid,'benchmark':bench[1],'limit':scope[1],
                'values':values,'cells':cells,'source_prose':source,'scope_quote':scope[0],'scope_offsets':[scope.start(),scope.end()],
                'table_sha256':hashlib.sha256(entry['text'].encode()).hexdigest(),
                'prose_sha256':hashlib.sha256(source.encode()).hexdigest()})
    return candidates[0] if len(candidates)==1 else None

def result(label,reason,**extra):return {'label':label,'reason':reason,'scope_verified':False,'scientific_approval':False,**extra}

def verify(item,evidence):
    match=PATTERN.fullmatch(item['text'].strip())
    observed=OBSERVED.fullmatch(item['text'].strip())
    if not match and not observed:return None
    source=prepare({k:evidence[k] for k in item['evidence_ids'] if k in evidence})
    if source is None:return result('Insufficient Evidence','Required unambiguous conformer table and scoped prose anchors unavailable')
    if observed:return result('Insufficient Evidence','Original comparison omits explicit benchmark, range and reference scope; source-assisted completion required')
    d=match.groupdict()
    if d['benchmark']!=source['benchmark'] or Decimal(d['limit'])!=Decimal(source['limit']):
        return result('Insufficient Evidence','Comparison scope differs from evidence')
    if d['entity'] not in source['values'] or d['baseline'] not in source['values'] or d['entity']==d['baseline']:
        return result('Insufficient Evidence','Comparison entities unresolved')
    base=Decimal(source['values'][d['baseline']]);new=Decimal(source['values'][d['entity']])
    if new<base:return result('Refuted','Increase direction contradicts matched source values',source_binding=source)
    places=len(d['percent'].partition('.')[2]);expected=((new-base)/base*100).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP)
    # A reported percentage can derive from unrounded measurements; do not overwrite it.
    reported=re.search(re.escape(d['entity'])+r"(?![-\w])[^.]{0,180}?(\d+(?:\.\d+)?)% (?:degradation|increase) in RMSD[^.]{0,120}?"+re.escape(d['baseline'])+r"(?![-\w])",source['source_prose'])
    if reported:
        places_reported=len(reported[1].partition('.')[2])
        from_cells=((new-base)/base*100).quantize(Decimal(1).scaleb(-places_reported),rounding=ROUND_HALF_UP)
        if from_cells!=Decimal(reported[1]):
            return result('Insufficient Evidence','Reported prose percentage differs from calculation using rounded table cells; unresolved rounding/source precision',
                reported_percentage=reported[1],rounded_cell_percentage=str(from_cells),source_binding=source)
    mismatch=[key for key,v in [('base',base),('new',new),('percent',expected)] if Decimal(d[key])!=v]
    return result('Refuted' if mismatch else 'Supported','Restricted scoped RMSD comparison against reported rounded table cells',
        numeric_scope_checked=True,source_binding=source,mismatched_fields=mismatch,
        computed_percent=str(expected),rounding='ROUND_HALF_UP to claim decimal precision; derived from reported cells, not raw measurements')

def correction(item,evidence):
    match=OBSERVED.fullmatch(item['text'].strip()) or PATTERN.fullmatch(item['text'].strip())
    if not match:return None
    source=prepare(evidence)
    if source is None:return None
    d=match.groupdict();entity=d['entity'];baseline=d['baseline']
    if entity not in source['values'] or baseline not in source['values'] or entity==baseline:return None
    # Never rewrite an explicitly different benchmark/range into this study's scope.
    if 'benchmark' in d and (d['benchmark']!=source['benchmark'] or Decimal(d['limit'])!=Decimal(source['limit'])):return None
    base=Decimal(source['values'][baseline]);new=Decimal(source['values'][entity])
    if new<base:return None
    percent=((new-base)/base*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)
    replacement={'text':TEMPLATE.format(**{k:source[k] for k in ('benchmark','limit')},entity=entity,baseline=baseline,
                    new=source['values'][entity],base=source['values'][baseline],percent=percent),
                 'evidence_ids':[source['table_id'],source['prose_id']]}
    if replacement['text']==item['text']:return None
    return replacement if verify(replacement,evidence)['label']=='Supported' else None
