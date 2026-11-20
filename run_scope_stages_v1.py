"""Connect the scoped numeric adapter to V0–V3. Default is saved-claim replay."""
import argparse,hashlib,json,sys,time
from pathlib import Path

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--source-run',required=True);p.add_argument('--case',required=True);p.add_argument('--xml',required=True);p.add_argument('--output',required=True)
    p.add_argument('--mode',choices=['replay','live-summary'],default='replay');a=p.parse_args()
    project=Path(a.project).resolve();sys.path.insert(0,str(project/'src'));sys.path.insert(0,str(project))
    from researchqa.scope_stage_backend_v1 import ScopeStageBackend,SavedClaimReplay,connected_module
    from researchqa.scinews_stages_v1 import run_condition
    connected=connected_module(project);previous_path=Path(a.source_run)/'result.json';previous=json.loads(previous_path.read_text())
    if previous.get('record_id')!='train:14460' or previous.get('status')!='completed_assertion_check':raise ValueError('Unexpected saved source run')
    if previous['runner_sha256']!=digest(project/'connected_claim_runner_v1.py'):raise ValueError('Connected runner changed')
    source=connected.prepare(a.case,a.xml);guard,guard_path=connected.load_guard(project)
    if source['E2_sha256']!=previous['E2_sha256'] or digest(guard_path)!=previous['guard_sha256']:raise ValueError('Saved-run source dependencies changed')
    rows=[json.loads(s) for s in (Path(a.case)/'E2_evidence.jsonl').read_text().splitlines()]
    evidence={x['evidence_id']:x for x in rows}
    if len(evidence)!=len(rows):raise ValueError('Duplicate evidence ids')
    anchors=[source['prose']['evidence_id'],source['table_id']]
    original={'text':previous['raw_claim'],'evidence_ids':anchors}
    identity={'mode':a.mode,'source_result_sha256':digest(previous_path),'E2_sha256':source['E2_sha256'],
              'source_anchors_prepared_externally':True,'source_xml_sha256':source['source_xml_sha256'],
              'code_sha256':{str(n):digest(project/n) for n in ['connected_claim_runner_v1.py','run_scope_stages_v1.py','src/researchqa/scope_stage_backend_v1.py','src/researchqa/scinews_stages_v1.py','src/researchqa/scope_guard_v1.py']}}
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write(out/'identity.json',identity)
    outcomes={};events={};backend=None;error=None
    try:
        if a.mode=='replay':base=SavedClaimReplay(original)
        else:
            from researchqa.scinews_live_v2 import DevelopmentBackend
            print('Loading live development writer and NLI; unsupported outputs may be withheld.',flush=True)
            base=DevelopmentBackend()
            identity['live_backend_code_sha256']={n:digest(project/'src/researchqa'/n) for n in ['scinews_live_v1.py','scinews_live_v2.py']}
            write(out/'live_environment.json',{'config':base.config,'code_sha256':identity['live_backend_code_sha256']})
        backend=ScopeStageBackend(base,source,guard,connected)
        def save(name,call):
            backend.last_meta={'model_calls':0};start=time.perf_counter()
            try:value=call()
            except Exception as e:
                event={'status':'failed','error':type(e).__name__+': '+str(e),'metadata':backend.last_meta,'elapsed_seconds':time.perf_counter()-start};write(out/'events'/f'{name}.json',event);events[name]=event;raise
            event={'status':'completed','value':value,'metadata':backend.last_meta,'elapsed_seconds':time.perf_counter()-start};events[name]=event;write(out/'events'/f'{name}.json',event);return value
        def outcome(name,value):
            draft='draft_raw' if name in {'V0','V2'} else 'draft_pre'
            value.update(record_id='train:14460',condition='E2',configuration=name,execution_mode=a.mode,
                         summary_generation_performed=a.mode=='live-summary',paired_draft_sha256=canonical(events[draft]['value'] if draft in events else []),
                         automatic_scientific_approval=False,independent_evaluation_performed=False,
                         development_only=True)
            outcomes[name]=value;write(out/(name+'.json'),value)
        run_condition(evidence,'Approaching coupled cluster accuracy through transfer learning',backend,save,outcome)
    except Exception as e:error=type(e).__name__+': '+str(e)
    summary={'purpose':'Scope adapter and V0–V3 development connection; not final evaluation','mode':a.mode,
             'completed_configurations':list(outcomes),'new_model_calls':sum(e['metadata'].get('model_calls',0) for e in events.values()),
             'prior_model_calls_not_recounted':previous.get('model_calls'),
             'outputs':{k:{'word_count':v['word_count_excluding_anchors'],'within_80_120_words':v['within_80_120_words'],'statements':len(v['statements'])} for k,v in outcomes.items()},
             'paired_raw_draft_preserved':len(outcomes)==4 and outcomes['V0']['paired_draft_sha256']==outcomes['V2']['paired_draft_sha256'],
             'paired_prechecked_draft_preserved':len(outcomes)==4 and outcomes['V1']['paired_draft_sha256']==outcomes['V3']['paired_draft_sha256'],
             'summary_quality_established':False,'full_research_completed':False,'error':error}
    write(out/'run_summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
    if error:raise SystemExit(1)
if __name__=='__main__':main()
