"""Eligibility-review queue and strict grouped split preparation. No inferred eligibility."""
import argparse
import csv
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import random

KNOWN_EXPOSED={'train:0','train:2','train:3','train:4','train:5'}
REVIEW_FIELDS=['record_id','source_split','source_row','provisional_group_hash',
 'known_development_exposure','study_id','selected_pair','eligible',
 'E1_readable','E2_readable','E3_readable','important_numerical_findings',
 'underlying_study_group_reviewed','near_duplicate_reviewed','previously_inspected',
 'reviewer','reviewed_at','source_reference','notes']
CHECKS=['E1_readable','E2_readable','E3_readable','important_numerical_findings',
        'underlying_study_group_reviewed','near_duplicate_reviewed']


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)


def new_output(path):
    path=Path(path)
    if path.exists():raise ValueError('Output directory exists; preserve it and use a new directory')
    path.mkdir(parents=True)
    return path


def queue(index_path,out,limit=300,exposure_path=None):
    if not isinstance(limit,int) or limit<=0:raise ValueError('Queue size must be positive')
    exposed=set(KNOWN_EXPOSED)
    if exposure_path:
        payload=json.loads(Path(exposure_path).read_text())
        if not isinstance(payload,list) or any(not isinstance(x,str) for x in payload):raise ValueError('Exposure file must be a JSON list of record IDs')
        exposed.update(payload)
    with Path(index_path).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    required={'record_id','source_split','source_row','provisional_group_hash','exact_duplicate'}
    if not rows or not required.issubset(rows[0]):raise ValueError('Unsupported audit-index schema')
    if len({r['record_id'] for r in rows})!=len(rows):raise ValueError('Duplicate audit record IDs')
    groups=defaultdict(list)
    for r in rows:
        if not r['provisional_group_hash']:raise ValueError('Missing provisional group')
        if r['exact_duplicate'].strip().lower() not in {'true','false'}:raise ValueError('Unknown exact-duplicate encoding')
        groups[r['provisional_group_hash']].append(r)
    exposed_groups={r['provisional_group_hash'] for r in rows if r['record_id'] in exposed}
    representatives=[]
    for group,members in groups.items():
        candidates=[r for r in members if r['exact_duplicate'].strip().lower()=='false']
        if not candidates:continue
        # Train-only engineering queue. No official validation/test texts inspected.
        candidates=[r for r in candidates if r['source_split']=='train']
        if not candidates:continue
        candidates.sort(key=lambda r:(r['record_id'] not in exposed,int(r['source_row'])))
        representatives.append(candidates[0])
    seed='scinews-eligibility-queue-v1'
    representatives.sort(key=lambda r:(r['provisional_group_hash'] not in exposed_groups,
        hashlib.sha256((seed+':'+r['provisional_group_hash']).encode()).hexdigest()))
    selected=representatives[:limit]
    output=new_output(out)
    with (output/'eligibility_review.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=REVIEW_FIELDS);w.writeheader()
        for r in selected:
            row={key:'' for key in REVIEW_FIELDS}
            row.update({key:r[key] for key in ('record_id','source_split','source_row','provisional_group_hash')})
            known=r['provisional_group_hash'] in exposed_groups
            row.update(known_development_exposure='yes' if known else 'not_recorded',
                       previously_inspected='yes' if known else 'unknown',
                       selected_pair='pending',eligible='pending')
            w.writerow(row)
    write(output/'queue_manifest.json',{'purpose':'Eligibility review queue only; not eligible sample',
        'source_index_sha256':digest(index_path),'queue_sha256':digest(output/'eligibility_review.csv'),
        'queue_seed':seed,'queued_pairs':len(selected),'confirmed_eligible_studies':0,
        'known_exposed_ids':sorted(exposed),'known_exposed_groups':sorted(exposed_groups),
        'additional_exposure_log_complete':False,'provisional_grouping_only':True,
        'original_source_splits_modified':False,'models_run':False})
    print(json.dumps({'queued_pairs':len(selected),'confirmed_eligible_studies':0,
                     'review_csv':str(output/'eligibility_review.csv'),'models_run':False},indent=2))


def select(rows,exposed_groups,targets=None,seed=62):
    targets=targets or {'development':20,'validation':20,'test':60}
    if set(targets)!={'development','validation','test'} or any(type(x) is not int or x<0 for x in targets.values()):
        raise ValueError('Invalid split targets')
    candidates=[]
    for row in rows:
        selected=row.get('selected_pair','').strip().lower()
        eligible=row.get('eligible','').strip().lower()
        if selected!='yes' or eligible!='yes':continue
        if any(row.get(k,'').strip().lower()!='yes' for k in CHECKS):raise ValueError('Selected eligible pair lacks completed evidence/group review')
        if any(not row.get(k,'').strip() for k in ['study_id','reviewer','reviewed_at','source_reference']):
            raise ValueError('Missing study identity or review provenance')
        exposure=row.get('previously_inspected','').strip().lower()
        if exposure not in {'yes','no'}:raise ValueError('Unknown exposure cannot enter a split')
        known=row['provisional_group_hash'] in exposed_groups or row.get('known_development_exposure')=='yes'
        if known and exposure!='yes':raise ValueError('Known inspected study cannot be marked untouched')
        candidates.append(row)
    for field in ('record_id','study_id','provisional_group_hash'):
        if len({r[field] for r in candidates})!=len(candidates):raise ValueError('Select one pair per reviewed study/group; duplicate '+field)
    dev=[r for r in candidates if r['previously_inspected'].strip().lower()=='yes']
    unseen=[r for r in candidates if r['previously_inspected'].strip().lower()=='no']
    rng=random.Random(seed);dev.sort(key=lambda r:r['study_id']);unseen.sort(key=lambda r:r['study_id'])
    rng.shuffle(dev);rng.shuffle(unseen)
    dev=dev[:targets['development']]
    need=targets['development']-len(dev)
    if len(unseen)<need+targets['validation']+targets['test']:
        raise ValueError('Not enough reviewed untouched studies for exact 20/20/60 targets; no split created')
    dev+=unseen[:need];unseen=unseen[need:]
    val=unseen[:targets['validation']];test=unseen[targets['validation']:targets['validation']+targets['test']]
    return [{**r,'split':name} for name,items in [('development',dev),('validation',val),('test',test)] for r in items]


def split(review_path,manifest_path,out):
    manifest=json.loads(Path(manifest_path).read_text())
    with Path(review_path).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    registered={r['provisional_group_hash'] for r in rows if r.get('known_development_exposure')=='yes'}
    exposed=set(manifest['known_exposed_groups'])|registered
    # Compare original queue identity fields; review may add decisions but not rewrite identity.
    original=Path(manifest_path).parent/'eligibility_review.csv'
    # The review path must be a separate edited copy; protect the original queue/hash.
    if Path(review_path).resolve()==original.resolve():raise ValueError('Use a reviewed COPY; preserve original queue CSV')
    if digest(original)!=manifest['queue_sha256']:raise ValueError('Original review queue changed')
    with original.open(encoding='utf-8',newline='') as f:old={r['record_id']:r for r in csv.DictReader(f)}
    if len({r['record_id'] for r in rows})!=len(rows) or set(old)!={r['record_id'] for r in rows}:raise ValueError('Review queue IDs changed')
    for r in rows:
        if any(r[k]!=old[r['record_id']][k] for k in ['source_split','source_row','provisional_group_hash','known_development_exposure']):raise ValueError('Queue identity/exposure fields changed')
    result=select(rows,exposed)
    output=new_output(out)
    write(output/'split_plan.json',{'status':'reviewed study split; independent scientific review still required',
        'review_sha256':digest(review_path),'queue_manifest_sha256':digest(manifest_path),'seed':62,
        'counts':dict(Counter(r['split'] for r in result)),'records':result,'final_test_executed':False})
    evaluation=output/'evaluation_only';evaluation.mkdir()
    with (evaluation/'finding_inventory_templates.jsonl').open('x',encoding='utf-8') as f:
        for r in result:
            f.write(json.dumps({'study_id':r['study_id'],'record_id':r['record_id'],'split':r['split'],
              'review_status':'pending','prepared_without_viewing_system_outputs':None,
              'first_annotator':None,'second_annotator':None,'findings':[],
              'finding_schema':{'finding_id':'','outcome':'','population':'','comparison':'','condition':'',
                'measure':'','value':None,'unit':'','source_evidence_id':'','source_quote':'','importance_rationale':''}},ensure_ascii=False)+'\n')
    rng=random.Random(62);second=[]
    for name,n in [('validation',5),('test',15)]:
        group=[r for r in result if r['split']==name]
        second.extend({'study_id':r['study_id'],'record_id':r['record_id'],'split':name,'review_completed':False} for r in rng.sample(group,n))
    write(evaluation/'second_annotator_targets.json',{'planned_fraction_per_split':0.25,
      'selection_seed':62,'reviewer_confirmed':False,'targets':second})
    print(json.dumps({'counts':dict(Counter(r['split'] for r in result)),
                      'inventories_completed':0,'second_reviews_completed':0,'output':str(output)},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('queue');q.add_argument('--index',required=True);q.add_argument('--output',required=True)
    q.add_argument('--limit',type=int,default=300);q.add_argument('--additional-exposure')
    s=sub.add_parser('split');s.add_argument('--review',required=True);s.add_argument('--queue-manifest',required=True);s.add_argument('--output',required=True)
    a=p.parse_args()
    if a.command=='queue':queue(a.index,a.output,a.limit,a.additional_exposure)
    else:split(a.review,a.queue_manifest,a.output)

if __name__=='__main__':main()
