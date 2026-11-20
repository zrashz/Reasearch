"""Prepare one source-linked operational contract draft; not evaluation gold."""
import argparse
import hashlib
import json
from pathlib import Path
from .workflow import source_evidence,CASE


def reference(eid,text,quote):
    if text.count(quote)!=1:raise ValueError('Source quotation is missing or ambiguous: '+quote)
    start=text.index(quote)
    return {'evidence_id':eid,'quote':quote,'start':start,'end':start+len(quote)}


def prepare(project,out):
    project=Path(project);source_evidence(project)
    path=project/CASE/'development_condition_inputs_v1/E1_evidence.jsonl'
    with path.open(encoding='utf-8') as f:e={r['evidence_id']:r for line in f if line.strip() for r in [json.loads(line)]}
    def ref(eid,quote):return reference(eid,e[eid]['text'],quote)
    p4,p5,p7=['train_5_prose_'+x for x in ('004','005','007')]
    contract={'contract_id':'train5_primary_composite_RR_draft_v1',
      'purpose':'Operational source annotation draft; not independent evaluation inventory',
      'scope_mapping_review_status':'pending',
      'scope':{'outcome':'composite primary perinatal outcome',
               'population':'low risk uncomplicated singleton pregnancy',
               'comparison':'induction group versus expectant management group',
               'condition':'induction at 41 weeks versus expectant management/induction at 42 weeks',
               'measure':'relative risk','unit':'dimensionless relative-risk ratio'},
      'scope_references':{
        'outcome':[ref(p7,'composite primary perinatal outcome')],
        'population':[ref(p4,'low risk uncomplicated singleton pregnancy')],
        'comparison':[ref(p7,'2.4% (33/1381) in the induction group'),ref(p7,'2.2% (31/1379) in the expectant management group')],
        'condition':[ref(p5,'41 weeks'),ref(p5,'42 weeks')],
        'measure':[ref(p7,'relative risk')],
        'unit':[ref(p7,'relative risk')]},
      'value':1.06,'value_reference':ref(p7,'1.06'),
      'notes':['Unit is a canonical interpretation of relative risk; it is not literally written as dimensionless in this source.',
               'Canonical grouping and condition interpretation require source review.',
               'This is the composite PRIMARY outcome, not the secondary mortality outcome.'],
      'independent_human_review_completed':False,'approved_for_automatic_inference':False,
      'source_E1_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    out=Path(out)
    if out.exists():raise ValueError('Output already exists; preserve it')
    out.mkdir(parents=True)
    (out/'source_contract_draft.json').write_text(json.dumps(contract,indent=2))
    (out/'source_excerpts.json').write_text(json.dumps({key:e[key] for key in (p4,p5,p7)},indent=2))
    print(json.dumps({'source_contracts_prepared':1,'review_status':'pending','automatic_inference_approved':False,
                      'gold_labels_read':False,'model_calls':0,'output':str(out)},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();prepare(a.project,a.output)
if __name__=='__main__':main()
