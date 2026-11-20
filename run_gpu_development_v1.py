"""GPU scientific-summary development runner. Never labels research complete."""
import argparse,csv,hashlib,json,sys,time
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)

def load_case(case,conditions,source_xml=None):
    case=Path(case).resolve();manifest=json.loads((case/'manifest.json').read_text());rows={};rid=manifest['record_id']
    for c in ('E1','E2','E3'):
        p=case/f'{c}_evidence.jsonl'
        if not p.is_file():
            if c in conditions:raise ValueError('Condition unavailable: '+c)
            continue
        if sha(p)!=manifest['condition_file_sha256'][c]:raise ValueError('Evidence checksum changed: '+c)
        rows[c]=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        if len({r['evidence_id'] for r in rows[c]})!=len(rows[c]):raise ValueError('Duplicate evidence IDs')
    if any(x.get('modality')!='prose' for x in rows['E1']):raise ValueError('E1 modality leak')
    if any(any(k in x for k in ['image_path','ocr_text','table_html']) for x in rows['E1']):raise ValueError('E1 payload leak')
    if rows.get('E2',[])[:len(rows['E1'])]!=rows['E1']:raise ValueError('E2 changed shared prose')
    if any(x.get('modality')!='table' for x in rows['E2'][len(rows['E1']):]):raise ValueError('Unexpected E2 addition')
    if 'E3' in rows:
        if rows['E3'][:len(rows['E2'])]!=rows['E2']:raise ValueError('E3 changed E2')
        for r in rows['E3'][len(rows['E2']):]:
            if r.get('modality')!='chart' or sha(r['image_path'])!=r['image_sha256']:raise ValueError('E3 image identity mismatch')
    xml=Path(source_xml) if source_xml else None
    if xml is None and manifest.get('source_xml'):xml=Path(manifest['source_xml'])
    if xml is None:
        origin=case.parent.parent/case.name/'manifest.json'
        if origin.exists():
            m=json.loads(origin.read_text());xml=Path(m['source_xml'])
            if m['source_xml_sha256']!=manifest['source_xml_sha256']:raise ValueError('Origin XML chain mismatch')
    if xml is None or sha(xml)!=manifest['source_xml_sha256']:raise ValueError('Source XML unavailable/changed')
    return rid,rows,manifest,xml

def select(rows,title):
    terms=set(__import__('re').findall(r'[a-z]{4,}',title.lower()))
    def score(row):
        labels=' '.join(map(str,row.get('section_path',[]))).lower()
        priority=0 if any(t in labels for t in ['results','findings','conclusions','discussion']) else 1 if row.get('source_kind')=='Abstract' else 2
        return priority,-sum(row['text'].lower().count(t) for t in terms),row['evidence_id']
    prose=sorted([r for r in rows if r.get('modality')=='prose'],key=score)
    chosen=[];size=0
    for r in prose:
        if len(chosen)<6 and size+len(r['text'])<=12000:chosen.append(r);size+=len(r['text'])
    for modality,limit in [('table',3),('chart',2)]:
        count=0
        for r in rows:
            if r.get('modality')==modality and count<limit and size+len(r['text'])<=18000:
                chosen.append(r);size+=len(r['text']);count+=1
    if not chosen:raise ValueError('No whole evidence record fits budget')
    return {r['evidence_id']:r for r in chosen},{'method':'results-first lexical development retrieval; not final embedding configuration',
          'selected_ids':[r['evidence_id'] for r in chosen],'excluded_ids':[r['evidence_id'] for r in rows if r not in chosen],
          'whole_records_only':True,'max_prose':6,'max_tables':3,'max_charts':2,'max_text_characters':18000}

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--metadata',required=True);p.add_argument('--output',required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case');g.add_argument('--cases-root')
    p.add_argument('--source-xml');p.add_argument('--conditions',default='E2');p.add_argument('--limit',type=int,default=1);p.add_argument('--audit-only',action='store_true');a=p.parse_args()
    project=Path(a.project).resolve();sys.path.insert(0,str(project/'src'));sys.path.insert(0,str(project))
    from researchqa.scinews_stages_v1 import run_condition
    conditions=a.conditions.split(',')
    if not conditions or len(conditions)!=len(set(conditions)) or any(c not in ['E1','E2','E3'] for c in conditions):raise ValueError('Invalid conditions')
    if a.limit<1:raise ValueError('Invalid case limit')
    if a.source_xml and not a.case:raise ValueError('Explicit XML is for one case only')
    paths=[Path(a.case)] if a.case else sorted(p for p in Path(a.cases_root).iterdir() if p.is_dir() and (p/'manifest.json').exists())[:a.limit]
    if not paths:raise ValueError('No cases found')
    with Path(a.metadata).open(encoding='utf-8',newline='') as f:metadata={r['record_id']:r for r in csv.DictReader(f)}
    cases=[]
    for path in paths:
        rid,rows,m,xml=load_case(path,conditions,a.source_xml)
        if rid not in metadata:raise ValueError('No news relevance metadata for '+rid)
        cases.append((path,rid,rows,m,xml,metadata[rid]['news_title']))
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    code_names=['run_gpu_development_v1.py','src/researchqa/gpu_backend_v1.py','src/researchqa/scinews_stages_v1.py','src/researchqa/scope_stage_backend_v1.py','connected_claim_runner_v1.py','src/researchqa/scope_guard_v1.py','src/researchqa/sentence_nli_v1.py','src/researchqa/conformer_table_v1.py']
    identity={'purpose':'GPU candidate development; not final experiments','record_ids':[c[1] for c in cases],
              'conditions':conditions,'metadata_sha256':sha(a.metadata),'code_sha256':{n:sha(project/n) for n in code_names},'audit_only':a.audit_only}
    write(out/'identity.json',identity)
    if a.audit_only:
        write(out/'audit.json',{'cases':len(cases),'conditions':conditions,'evidence_and_images_checked':True,'model_calls':0,'eligibility_confirmed':False});print('Audit passed; no models loaded.');return
    import torch
    if not torch.cuda.is_available():
        write(out/'run_summary.json',{'error':'CUDA GPU unavailable','models_loaded':False,'new_model_calls':0});raise RuntimeError('Select a Colab GPU runtime. Do not reinstall CPU torch or rerun old setup cells.')
    from huggingface_hub import model_info
    from researchqa.gpu_backend_v1 import GPUBackend,MODEL
    pin=project/'private/model_pins/gpu_vlm_candidate_v1.json'
    if pin.exists():
        saved=json.loads(pin.read_text())
        if saved['model_id']!=MODEL:raise ValueError('Different model pin exists')
        revision=saved['revision']
    else:
        revision=model_info(MODEL).sha;write(pin,{'model_id':MODEL,'revision':revision,'purpose':'Development candidate, not final model selection'})
    # Selected studies become development exposures, never silently move to held-out test.
    write(out/'development_exposed_record_ids.json',[c[1] for c in cases])
    try:backend=GPUBackend(revision)
    except Exception as e:
        write(out/'run_summary.json',{'status':'backend_load_failed','error':type(e).__name__+': '+str(e),'new_model_calls':0,'full_research_completed':False});raise
    write(out/'backend.json',backend.config)
    results=[]
    for path,rid,rows,m,xml,title in cases:
        for condition in conditions:
            target=out/rid.replace(':','_')/condition;target.mkdir(parents=True)
            selected,retrieval=select(rows[condition],title);write(target/'retrieved_evidence.json',selected);write(target/'retrieval.json',retrieval)
            active=backend
            # Reuse the validated, narrowly scoped numeric adapter when its sources are present.
            if rid=='train:14460' and condition in {'E2','E3'}:
                from researchqa.scope_stage_backend_v1 import ScopeStageBackend,connected_module
                connected=connected_module(project);source=connected.prepare(path,xml);guard,_=connected.load_guard(project)
                active=ScopeStageBackend(backend,source,guard,connected)
            events={};outcomes={};error=None
            def save(name,call):
                print(rid,condition,'stage:',name,flush=True);active.last_meta={'model_calls':0};started=time.perf_counter()
                try:value=call()
                except Exception as e:
                    event={'status':'failed','error':type(e).__name__+': '+str(e),'metadata':active.last_meta,'elapsed_seconds':time.perf_counter()-started};events[name]=event;write(target/'events'/f'{name}.json',event);raise
                event={'status':'completed','value':value,'metadata':active.last_meta,'elapsed_seconds':time.perf_counter()-started};events[name]=event;write(target/'events'/f'{name}.json',event);return value
            def outcome(name,value):
                draft='draft_raw' if name in {'V0','V2'} else 'draft_pre'
                value.update(record_id=rid,condition=condition,configuration=name,paired_draft_sha256=canonical(events[draft]['value'] if draft in events else []),
                             automatic_scientific_approval=False,independent_evaluation_performed=False,eligibility='pending',finding_coverage_assessed=False)
                outcomes[name]=value;write(target/(name+'.json'),value)
            try:run_condition(selected,title,active,save,outcome)
            except Exception as e:error=type(e).__name__+': '+str(e)
            summary={'record_id':rid,'condition':condition,'completed_configurations':list(outcomes),'error':error,
                     'new_model_calls':sum(e['metadata'].get('model_calls',0) for e in events.values()),
                     'outputs':{k:{'words':v['word_count_excluding_anchors'],'length_pass':v['within_80_120_words'],'summary':v['summary']} for k,v in outcomes.items()},
                     'full_research_completed':False,'independent_evaluation_performed':False}
            write(target/'run_summary.json',summary);results.append(summary);print(json.dumps(summary,indent=2,ensure_ascii=False),flush=True)
            if error:
                write(out/'run_summary.json',{'status':'stopped_preserving_failure','results':results,'full_research_completed':False});raise SystemExit(1)
    write(out/'run_summary.json',{'status':'completed_development_runs','results':results,'full_research_completed':False})
    print('Saved:',out,flush=True)
if __name__=='__main__':main()
