"""Saved-claim numerical adapter diagnostic; no generation and no full pipeline replay."""
import argparse,json,sys,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--events',required=True);p.add_argument('--evidence',required=True);p.add_argument('--output',required=True);a=p.parse_args()
project=Path(a.project);sys.path.insert(0,str(project/'src'))
from researchqa.conformer_table_v1 import verify,correction
source=json.loads(Path(a.events).read_text());evidence=json.loads(Path(a.evidence).read_text());rows=[]
for i,item in enumerate(source['value']):
 before=verify(item,evidence);fixed=correction(item,evidence) if before is None or before['label']!='Supported' else None
 after=verify(fixed,evidence) if fixed else None
 rows.append({'index':i,'original':item,'numeric_check':before,'source_assisted_correction':fixed,'recheck':after})
 print('Claim',i,'->',before['label'] if before else 'Outside restricted numeric grammar','| corrected:',bool(fixed),'| recheck:',after['label'] if after else None)
 if fixed:print(fixed['text'])
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
report={'purpose':'Restricted numerical saved-claim development diagnostic','records':rows,'model_calls':0,'full_pipeline_run':False,'historical_results_modified':False,'independent_evaluation_performed':False,'source_event_sha256':sha(a.events),'source_evidence_sha256':sha(a.evidence),'adapter_sha256':sha(project/'src/researchqa/conformer_table_v1.py')}
out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x') as f:json.dump(report,f,indent=2,ensure_ascii=False)
print('Saved:',out)
