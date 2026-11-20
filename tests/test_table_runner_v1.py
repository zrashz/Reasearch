import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from researchqa.table_runner_v1 import process, run


def packet(claim='Alpha reduces DP by 4.00 (from 15.28 to 9.95) compared to Beta.'):
    values=[['Methods','DP'],['Beta','15.28'],['Alpha','9.95']]
    return {'record_id':'dev:1','claim':claim,'caption':'Method evaluation',
            'table_cells':[[{'cell_id':f'r{r}_c{c}','text':v} for c,v in enumerate(row)]
                           for r,row in enumerate(values)]}

class RunnerTests(unittest.TestCase):
    def test_real_arithmetic_but_no_scientific_approval(self):
        r=process(packet()); c=r['numerical_checks'][0]
        self.assertEqual(c['expected_change'],'5.33')
        self.assertEqual(c['numerical_decision'],'Refuted')
        self.assertEqual(r['operational_decision'],'Insufficient Evidence')
        self.assertIsNone(r['scientific_prediction'])
    def test_correct_arithmetic_still_not_full_support(self):
        r=process(packet().copy() | {'claim':packet()['claim'].replace('4.00','5.33')})
        self.assertEqual(r['numerical_checks'][0]['numerical_decision'],'Supported')
        self.assertIsNone(r['scientific_prediction'])
    def test_duplicate_rows_abstain(self):
        p=packet(); p['table_cells'].append([{'cell_id':'r3_c0','text':'Beta'}, {'cell_id':'r3_c1','text':'20'}])
        self.assertEqual(process(p)['numerical_checks'],[])
    def test_blank_source_never_zero(self):
        p=packet();p['table_cells'][1][1]['text']=''
        self.assertEqual(process(p)['numerical_checks'],[])
    def test_bad_coordinates_technical_failure(self):
        p=packet();p['table_cells'][1][1]['cell_id']='r2_c1'
        self.assertEqual(process(p)['operational_decision'],'Technical Failure')
    def test_unhandled_wording_kept(self):
        self.assertEqual(process(packet('Alpha is better.'))['status'],'unresolved')
    def test_latency_source_matching(self):
        p=packet("Alpha's 3-hop latency is Beta's 2.45 seconds.")
        p['caption']='Average latency (s/QA)';p['table_cells'][0][1]['text']='3-hop'
        r=process(p)
        self.assertEqual(r['numerical_checks'][0]['source_cell_id'],'r1_c1')
    def test_missing_condition_no_binding(self):
        p=packet("Beta's 2.45 seconds.");p['caption']='Average latency'
        self.assertEqual(process(p)['numerical_checks'],[])
    def test_resume_preserves_bytes_and_changed_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'inputs.jsonl';out=Path(d)/'out'
            inp.write_text(json.dumps(packet())+'\n')
            run(inp,out)
            before={p.name:p.read_bytes() for p in out.iterdir()}
            run(inp,out)
            self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
            inp.write_text(json.dumps(packet('changed'))+'\n')
            with self.assertRaises(ValueError):run(inp,out)
    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/'in.jsonl';inp.write_text((json.dumps(packet())+'\n')*2)
            with self.assertRaises(ValueError):run(inp,Path(d)/'out')
    def test_gold_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=packet();p['gold_label']='Refuted'
            inp=Path(d)/'in.jsonl';inp.write_text(json.dumps(p)+'\n')
            with self.assertRaises(ValueError):run(inp,Path(d)/'out')

if __name__=='__main__':unittest.main()
