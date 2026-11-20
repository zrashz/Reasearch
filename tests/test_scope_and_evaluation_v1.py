import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from researchqa.scope_guard_v1 import check_scope_value,FIELDS
from researchqa.evaluation_prep_v1 import select,queue,CHECKS


def fixture():
    text='Outcome A in group B was 1.06.'
    e={'p1':{'text':text}}
    r={'evidence_id':'p1','start':0,'end':9,'quote':'Outcome A'}
    scope={k:'synthetic_'+k for k in FIELDS}
    contract={'contract_id':'synthetic','scope':scope,'scope_references':{k:[r] for k in FIELDS},
              'value':1.06,'value_reference':{'evidence_id':'p1','start':24,'end':28,'quote':'1.06'},
              'scope_mapping_review_status':'reviewed'}
    source_start=text.index('1.06')
    contract['value_reference'].update(start=source_start,end=source_start+4)
    claim={'text':'The value is 1.06.','scope':dict(scope),'value':1.06,
           'value_reference':{'start':13,'end':17,'quote':'1.06'},'scope_mapping_review_status':'reviewed'}
    # Correct offsets derived from the synthetic claim, never fuzzy matching.
    start=claim['text'].index('1.06');claim['value_reference'].update(start=start,end=start+4)
    return claim,contract,e


def reviewed(i,inspected='no'):
    return {'record_id':f'train:{i}','provisional_group_hash':f'g{i}','study_id':f's{i}',
            'selected_pair':'yes','eligible':'yes','previously_inspected':inspected,
            'reviewer':'fixture reviewer','reviewed_at':'fixture','source_reference':'fixture',
            **{key:'yes' for key in CHECKS}}

class ScopeTests(unittest.TestCase):
    def test_matching_assertion_only(self):
        a,b,e=fixture();r=check_scope_value(a,b,e)
        self.assertEqual(r['decision'],'Supported');self.assertFalse(r['scientific_approval'])
    def test_wrong_outcome_not_approved(self):
        a,b,e=fixture();a['scope']['outcome']='mortality'
        r=check_scope_value(a,b,e);self.assertEqual(r['decision'],'Insufficient Evidence')
        self.assertIn('outcome',r['mismatched_scope_fields'])
    def test_missing_scope_abstains(self):
        a,b,e=fixture();a['scope']['population']=None
        self.assertEqual(check_scope_value(a,b,e)['decision'],'Insufficient Evidence')
    def test_pending_mapping_abstains(self):
        a,b,e=fixture();b['scope_mapping_review_status']='pending'
        self.assertEqual(check_scope_value(a,b,e)['decision'],'Insufficient Evidence')
    def test_claim_scope_review_required(self):
        a,b,e=fixture();a['scope_mapping_review_status']='pending'
        self.assertEqual(check_scope_value(a,b,e)['decision'],'Insufficient Evidence')
    def test_fabricated_extracted_number_abstains(self):
        a,b,e=fixture();a['value']=2
        self.assertEqual(check_scope_value(a,b,e)['decision'],'Insufficient Evidence')
    def test_source_quote_tamper_preparation_error(self):
        a,b,e=fixture();b['value_reference']['quote']='9.99'
        with self.assertRaises(ValueError):check_scope_value(a,b,e)
    def test_wrong_number_same_scope_refuted(self):
        a,b,e=fixture();a['text']='The value is 2.00.';a['value']=2
        a['value_reference']={'quote':'2.00','start':13,'end':17}
        self.assertEqual(check_scope_value(a,b,e)['decision'],'Refuted')

class PreparationTests(unittest.TestCase):
    def test_exact_targets_and_inspected_dev_only(self):
        rows=[reviewed(i,'yes' if i<3 else 'no') for i in range(100)]
        result=select(rows,set());self.assertEqual(len(result),100)
        self.assertTrue(all(r['split']=='development' for r in result if r['previously_inspected']=='yes'))
        self.assertEqual(sum(r['split']=='test' for r in result),60)
    def test_not_enough_never_silently_shrinks(self):
        with self.assertRaises(ValueError):select([reviewed(i) for i in range(99)],set())
    def test_unknown_exposure_blocks(self):
        rows=[reviewed(i) for i in range(100)];rows[0]['previously_inspected']='unknown'
        with self.assertRaises(ValueError):select(rows,set())
    def test_known_exposed_cannot_be_hidden(self):
        with self.assertRaises(ValueError):select([reviewed(i) for i in range(100)],{'g0'})
    def test_duplicate_underlying_studies_block(self):
        rows=[reviewed(i) for i in range(100)];rows[1]['study_id']=rows[0]['study_id']
        with self.assertRaises(ValueError):select(rows,set())
    def test_missing_visual_review_blocks(self):
        rows=[reviewed(i) for i in range(100)];rows[0]['E3_readable']='pending'
        with self.assertRaises(ValueError):select(rows,set())
    def test_queue_keeps_group_exposure_and_no_eligibility(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);index=root/'index.csv'
            rows=[{'record_id':'train:5','source_split':'train','source_row':'5','provisional_group_hash':'same','exact_duplicate':'False'},
                  {'record_id':'val:8','source_split':'val','source_row':'8','provisional_group_hash':'same','exact_duplicate':'False'},
                  {'record_id':'train:9','source_split':'train','source_row':'9','provisional_group_hash':'other','exact_duplicate':'False'}]
            with index.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            queue(index,root/'out',2)
            with (root/'out/eligibility_review.csv').open() as f:result=list(csv.DictReader(f))
            self.assertEqual(len(result),2);self.assertEqual(result[0]['previously_inspected'],'yes')
            self.assertTrue(all(r['eligible']=='pending' for r in result))
            self.assertEqual(result[1]['previously_inspected'],'unknown')

if __name__=='__main__':unittest.main()
