"""One source-bound E2 numeric assertion, not a complete research pipeline."""
import argparse
import hashlib
import importlib.util
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

MODEL='Qwen/Qwen2.5-1.5B-Instruct'
REVISION='989aa7980e4cf806f80c7fef2b1adb7bc71aa306'
XML_HASH='65e7d34f440fd923b28556607abe0d82daba7e073e1129eadf91082c1c972411'
TEMPLATE=("On the GDB-10to13 benchmark, {method} has a mean absolute deviation of "
          "{value} kcal/mol for conformer energy differences relative to CCSD(T)*/CBS, "
          "considering conformations within 100 kcal/mol of each molecule's energy minimum.")
PATTERN=re.compile(re.escape(TEMPLATE).replace(r'\{method\}',r'(?P<method>[^\n,]+)').replace(r'\{value\}',r'(?P<value>\d+(?:\.\d+)?)'))

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(e):return ' '.join(''.join(e.itertext()).split())
def load_guard(project):
    p=Path(project)/'src/researchqa/scope_guard_v1.py'
    spec=importlib.util.spec_from_file_location('connected_scope_guard',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m,p

def prepare(case,xml):
    case=Path(case);xml=Path(xml)
    if digest(xml)!=XML_HASH:raise ValueError('Unexpected source XML')
    manifest=json.loads((case/'manifest.json').read_text())
    records={}
    for c in ('E1','E2'):
        p=case/f'{c}_evidence.jsonl'
        if digest(p)!=manifest['condition_file_sha256'][c]:raise ValueError('Evidence hash mismatch')
        records[c]=[json.loads(x) for x in p.read_text().splitlines()]
    if records['E2'][:len(records['E1'])]!=records['E1']:raise ValueError('Shared prose changed')
    prose=[x for x in records['E1'] if 'Table 1 provides mean absolute deviations' in x['text']]
    tables=[x for x in records['E2'] if x['evidence_id']=='train_14460_table_Tab1']
    if len(prose)!=1 or len(tables)!=1:raise ValueError('Ambiguous source records')
    table=ET.fromstring(tables[0]['text'])
    original=ET.parse(xml).getroot().find('.//table-wrap[@id="Tab1"]')
    if ET.tostring(table)!=ET.tostring(original):raise ValueError('Derived table differs from XML')
    headers=[text(x) for x in table.findall('./table/thead/tr/th')]
    if len(headers)!=len(set(headers)):raise ValueError('Duplicate headers')
    rows=[list(x) for x in table.findall('./table/tbody/tr') if (list(x)[0].text or '').strip()=='MAD']
    if len(rows)!=1 or len(rows[0])!=len(headers):raise ValueError('Ambiguous MAD row')
    for cell in table.findall('.//th')+table.findall('.//td'):
        if any(cell.get(a,'1')!='1' for a in ('rowspan','colspan')):raise ValueError('Merged cells unsupported')
    values={headers[i]:text(rows[0][i]) for i in range(1,len(headers))}
    return {'prose':prose[0],'table_id':tables[0]['evidence_id'], 'caption':text(table.find('caption')),
            'footnote':text(table.find('table-wrap-foot')),'values':values,'source_xml_sha256':digest(xml),
            'E2_sha256':digest(case/'E2_evidence.jsonl')}

def assess(raw,source,guard):
    base={'scientific_approval':False,'whole_summary_verified':False,
          'scope_alignment_method':'exact restricted sentence grammar; not general semantic extraction'}
    match=PATTERN.fullmatch(raw.strip())
    if not match:return {**base,'decision':'Insufficient Evidence','reason':'Unsupported claim grammar; no automatic repair'}
    method=match['method'];value=match['value']
    if method not in source['values']:return {**base,'decision':'Insufficient Evidence','reason':'No unique exact method header'}
    eid=source['table_id'];pid=source['prose']['evidence_id']
    source_text=(f"Caption: {source['caption']}\nMethod: {method}\nMetric: MAD\n"
                 f"Value: {source['values'][method]}\nFootnote: {source['footnote']}")
    evidence={eid:{'text':source_text},pid:source['prose']}
    def ref(i,q):
        s=evidence[i]['text']
        if s.count(q)!=1:raise ValueError('Ambiguous source quotation: '+q)
        a=s.index(q);return {'evidence_id':i,'start':a,'end':a+len(q),'quote':q}
    scope={'outcome':'conformer energy differences','population':'GDB-10to13 benchmark',
           'comparison':method+' versus CCSD(T)*/CBS reference',
           'condition':"conformations within 100 kcal/mol of each molecule's energy minimum",
           'measure':'mean absolute deviation (MAD)','unit':'kcal/mol'}
    quotes={'outcome':[(eid,'conformer energy differences')],'population':[(eid,'GDB-10to13 benchmark')],
            'comparison':[(eid,method),(pid,'Reference values are recomputed at the CCSD(T)*/CBS level of theory.')],
            'condition':[(pid,'within 100 kcal mol−1 of the energy minima for each molecule')],
            'measure':[(pid,'mean absolute deviations (MAD)')],'unit':[(eid,'Units are in kcal mol−1')]}
    # These canonical mappings were assistant-reviewed for this source and grammar only.
    # No independent reviewer or general semantic inference is claimed.
    contract={'contract_id':'train14460_Tab1_'+method+'_MAD','scope':scope,
              'scope_references':{k:[ref(i,q) for i,q in v] for k,v in quotes.items()},
              'value':source['values'][method],'value_reference':ref(eid,source['values'][method]),
              'scope_mapping_review_status':'reviewed','mapping_review_type':'assistant-reviewed source-specific grammar',
              'independent_human_review_completed':False}
    start=raw.index(value,raw.index('deviation of '))
    claim={'text':raw,'scope':scope,'value':value,'value_reference':{'start':start,'end':start+len(value),'quote':value},
           'scope_mapping_review_status':'reviewed','mapping_review_type':'literal grammar binding'}
    decision=guard.check_scope_value(claim,contract,evidence)
    return {**base,**decision,'extracted_claim':claim,'source_contract':contract,'source_evidence':evidence,
            'whole_summary_verified':False,'automatic_full_claim_approval':False}

def generate(source,event_path):
    import torch,transformers
    from transformers import AutoTokenizer,AutoModelForCausalLM
    instruction=("Write exactly ONE sentence by filling METHOD and VALUE in the following sentence. "
        "Choose one method from the table. Copy its MAD value. Preserve every other word. "
        "Return only the filled sentence, with no heading, quotes, or Markdown.\n"
        +TEMPLATE.format(method='METHOD',value='VALUE')+'\nTABLE:\n'
        +json.dumps({'caption':source['caption'],'MAD_values':source['values'],'units':source['footnote']},ensure_ascii=False))
    messages=[{'role':'system','content':'Use supplied evidence only.'},{'role':'user','content':instruction}]
    event={'messages':messages,'model_id':MODEL,'model_revision':REVISION,'model_calls':0}
    event_path.write_text(json.dumps(event,indent=2,ensure_ascii=False))
    print('Loading pinned CPU model...',flush=True)
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION)
    model=AutoModelForCausalLM.from_pretrained(MODEL,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True).to('cpu').eval()
    prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    inputs=tokenizer(prompt,return_tensors='pt',add_special_tokens=False)
    n=inputs['input_ids'].shape[-1]
    event.update(input_tokens=n,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),model_calls=1)
    event_path.write_text(json.dumps(event,indent=2,ensure_ascii=False))
    print('Generating one source-grounded assertion...',flush=True);started=time.perf_counter()
    with torch.inference_mode():out=model.generate(**inputs,max_new_tokens=180,do_sample=False,num_beams=1,pad_token_id=tokenizer.eos_token_id)
    tokens=out[0,n:];raw=tokenizer.decode(tokens,skip_special_tokens=True).strip()
    event.update(raw_response=raw,generated_tokens=len(tokens),hit_token_limit=len(tokens)==180,
                 generation_seconds=round(time.perf_counter()-started,2),torch_version=torch.__version__,transformers_version=transformers.__version__)
    event_path.write_text(json.dumps(event,indent=2,ensure_ascii=False))
    return raw,event

def main():
    a=argparse.ArgumentParser();a.add_argument('--project',required=True);a.add_argument('--case',required=True);a.add_argument('--xml',required=True);a.add_argument('--output',required=True)
    g=a.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--claim-file')
    args=a.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    report={'purpose':'Connected E2 assertion development run; not final evaluation','record_id':'train:14460',
            'model_calls':0,'full_V0_V3_pipeline_completed':False,'eligibility':'pending','runner_sha256':digest(__file__)}
    try:
        source=prepare(args.case,args.xml);guard,path=load_guard(args.project)
        report.update(source_xml_sha256=source['source_xml_sha256'],E2_sha256=source['E2_sha256'],guard_sha256=digest(path))
        if args.live:
            raw,event=generate(source,out/'generation_event.json');report['model_calls']=event['model_calls']
            report['generation_hit_token_limit']=event['hit_token_limit']
        else:raw=Path(args.claim_file).read_text().strip()
        report['raw_claim']=raw
        report['assertion_result']=assess(raw,source,guard)
        if report.get('generation_hit_token_limit'):
            report['assertion_result']={'decision':'Insufficient Evidence','reason':'Generation reached token limit','scientific_approval':False}
        report['status']='completed_assertion_check'
    except Exception as e:
        event_path=out/'generation_event.json'
        if event_path.exists():report['model_calls']=json.loads(event_path.read_text()).get('model_calls',0)
        report.update(status='technical_failure',error=type(e).__name__+': '+str(e))
    (out/'result.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)
    if report['status']=='technical_failure':raise SystemExit(1)

if __name__=='__main__':main()
