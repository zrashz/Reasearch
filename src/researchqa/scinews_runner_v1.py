"""SciNews development audit, stage plan and optional CPU engineering run."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import resource
import time
import xml.etree.ElementTree as ET
from .workflow import source_evidence, CASE
from .scinews_stages_v1 import run_condition

BASE=Path('private/scinews_development_candidates_v1')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)


def load_conditions(project):
    project=Path(project).resolve()
    source_evidence(project)  # Original DOI, correction DOI, hashes and corrected row.
    folder=project/CASE/'development_condition_inputs_v1'
    conditions={}
    for condition in ('E1','E2','E3'):
        path=folder/f'{condition}_evidence.jsonl'
        with path.open(encoding='utf-8') as f:rows=[json.loads(line) for line in f if line.strip()]
        ids=[r['evidence_id'] for r in rows]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate evidence ID')
        if any(not isinstance(r.get('text'),str) or not r['text'].strip() for r in rows):
            raise ValueError('Missing evidence text')
        conditions[condition]=rows
    e1,e2,e3=[conditions[k] for k in ('E1','E2','E3')]
    if not e1 or any(r.get('modality')!='prose' for r in e1):raise ValueError('E1 must contain only prose')
    # Modality labels alone cannot prove prose contains no extraction leaks.
    if any(any(key in r for key in ('image_path','table_html','ocr_text')) for r in e1):
        raise ValueError('Unexpected visual/table payload in E1')
    if e2[:len(e1)]!=e1 or not e2[len(e1):] or any(r.get('modality')!='table' for r in e2[len(e1):]):
        raise ValueError('E2 must preserve E1 exactly and add tables only')
    if e3[:len(e2)]!=e2 or not e3[len(e2):] or any(r.get('modality')!='chart' for r in e3[len(e2):]):
        raise ValueError('E3 must preserve E2 exactly and add charts only')
    corrected=(project/CASE/'table3_corrected_development_v1.xml').read_text()
    table3=[r for r in e2 if r['evidence_id']=='train_5_table_tbl3']
    if len(table3)!=1 or table3[0]['text']!=corrected:raise ValueError('E2 corrected Table 3 differs')
    for r in e2[len(e1):]:ET.fromstring(r['text'])
    for r in e3[len(e2):]:
        original=Path(r['image_path']);parts=original.parts
        if 'private' not in parts:raise ValueError('Unknown image path root')
        local=(project/Path(*parts[parts.index('private'):])).resolve()
        if not local.is_relative_to(project) or sha(local)!=r['image_sha256']:
            raise ValueError('Chart file or image hash differs')
    candidate=read(project/BASE/'train_5.json')
    if candidate.get('DOI','').strip().lower()!='10.1136/bmj.l6131':raise ValueError('Wrong news-paper DOI')
    title=candidate.get('News_Title')
    if not isinstance(title,str) or not title.strip():raise ValueError('Missing news title')
    return conditions,title


def audit(project):
    conditions,title=load_conditions(project)
    folder=Path(project)/CASE/'development_condition_inputs_v1'
    return {'purpose':'SciNews development evidence validation; not eligibility approval',
            'record_id':'train:5','counts':{k:len(v) for k,v in conditions.items()},
            'source_hashes':{k:sha(folder/f'{k}_evidence.jsonl') for k in conditions},
            'shared_prose_identical':True,'shared_E2_identical':True,
            'corrected_table3_identity_checked':True,'chart_hash_checked':True,
            'paragraph_semantics_and_visual_readability_independently_validated':False,
            'eligibility_confirmed':False,'model_calls':0,
            'configurations':[{'condition':e,'verification':v,'status':
                              'blocked_visual_backend_unvalidated' if e=='E3' else 'pending_live_development'}
                             for e in conditions for v in ('V0','V1','V2','V3')]}


def retrieve(rows,title):
    """Explicit lexical development retrieval, not final embedding procedure."""
    terms=set(re.findall(r'[a-z]{4,}',title.lower()))
    ranked=sorted(enumerate(rows),key=lambda x:(-sum(x[1]['text'].lower().count(t) for t in terms),x[0]))
    selected=[];excluded=[];total=0
    for _,r in ranked:
        if len(selected)>=6 or total+len(r['text'])>18000:
            excluded.append(r['evidence_id']);continue
        selected.append(r);total+=len(r['text'])
    if not selected:raise ValueError('No whole evidence record fits development budget')
    return {r['evidence_id']:r for r in selected},{'method':'lexical_development_only_not_final_embeddings',
           'whole_records_only':True,'selected_ids':[r['evidence_id'] for r in selected],
           'excluded_ids':excluded,'max_records':6,'max_characters':18000}


def execute(project,condition,out):
    conditions,title=load_conditions(project)
    if condition=='E3':raise ValueError('E3 blocked: no validated visual backend. Do not substitute prose or assistant OCR.')
    from .scinews_live_v1 import DevelopmentBackend
    selected,retrieval=retrieve(conditions[condition],title)
    # Dependencies are part of the resume identity, as are prompts/backend source.
    codehash={name:sha(Path(__file__).with_name(name)) for name in
              ['scinews_runner_v1.py','scinews_stages_v1.py','scinews_live_v1.py','workflow.py','numerical.py','extraction_guard.py']}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    identity={'condition':condition,'record_id':'train:5','evidence_sha256':canonical(conditions[condition]),
              'news_title_sha256':canonical(title),'retrieval':retrieval,'code_hashes':codehash}
    if (out/'identity.json').exists():
        if read(out/'identity.json')!=identity:raise ValueError('Resume identity changed; use a new output directory')
    else:
        if any(out.iterdir()):raise ValueError('Output directory nonempty without identity')
        write(out/'identity.json',identity)
    write_once=lambda name,obj: write(out/name,obj) if not (out/name).exists() else None
    write_once('audit.json',audit(project));write_once('retrieved_evidence.json',selected)
    print('Loading development CPU backend; no final model selection implied.',flush=True)
    backend=DevelopmentBackend()
    if (out/'backend.json').exists() and read(out/'backend.json')!=backend.config:
        raise ValueError('Backend environment/settings changed; use a new output directory')
    write_once('backend.json',backend.config)
    def save(name,call):
        path=out/'events'/f'{name}.json'
        if path.exists():
            old=read(path)
            if old['status']!='completed':raise ValueError('Saved failed event preserved: '+name)
            return old['value']
        print('Stage:',name,flush=True)
        backend.last_meta={'model_calls':0};start=time.perf_counter()
        try:
            value=call()
        except Exception as e:
            write(path,{'status':'failed','error':f'{type(e).__name__}: {e}',
                        'elapsed_seconds':time.perf_counter()-start,'metadata':backend.last_meta})
            raise
        write(path,{'status':'completed','value':value,'elapsed_seconds':time.perf_counter()-start,
                    'metadata':backend.last_meta})
        return value
    def outcome(name,value):
        value.update({'record_id':'train:5','condition':condition,'configuration':name,
                      'status':'development_output_not_final_evaluation','automatic_scientific_approval':False,
                      'atomic_completeness_verified':False,'finding_coverage_assessed':False,
                      'evidence_anchor_support_independently_validated':False})
        write_once(name+'.json',value)
    error=None
    try:run_condition(selected,title,backend,save,outcome)
    except Exception as e:error=f'{type(e).__name__}: {e}'
    events=[read(p) for p in (out/'events').glob('*.json')]
    summary={'purpose':'Live development integration, not final experiment','condition':condition,
             'completed_configurations':[v for v in ('V0','V1','V2','V3') if (out/(v+'.json')).exists()],
             'error':error,'model_calls_including_corrections_and_rechecks':sum(e['metadata'].get('model_calls',0) for e in events),
             'step_elapsed_seconds':sum(e['elapsed_seconds'] for e in events),
             'process_peak_RSS_KiB_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'independent_evaluation_performed':False,'full_research_completed':False}
    write_once('run_summary.json',summary)
    print(json.dumps(summary,indent=2))
    if error:raise RuntimeError(error)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--live',action='store_true',help='Explicitly enable CPU model inference')
    p.add_argument('--condition',choices=['E1','E2','E3'],default='E1')
    a=p.parse_args();project=Path(a.project).resolve();out=Path(a.output).resolve()
    if a.live:execute(project,a.condition,out)
    else:
        report=audit(project)
        out.mkdir(parents=True,exist_ok=True)
        path=out/'scinews_audit_plan.json'
        if path.exists():
            if read(path)!=report:raise ValueError('Different audit exists; use a new output directory')
        else:write(path,report)
        print(json.dumps(report,indent=2))

if __name__=='__main__':main()
