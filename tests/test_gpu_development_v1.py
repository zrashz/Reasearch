import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from researchqa.gpu_backend_v1 import parse_object,numerical,exact_source_sentence
from run_gpu_development_v1 import select
class GPUOfflineChecks(unittest.TestCase):
 def sample(self):return {'sentences':[{'text':'A finding.','evidence_ids':['p']}]}
 def test_valid_json(self):self.assertEqual(parse_object(json.dumps(self.sample()),'sentences'),self.sample()['sentences'])
 def test_outer_fence_only(self):self.assertEqual(parse_object('```json\n'+json.dumps(self.sample())+'\n```','sentences'),self.sample()['sentences'])
 def test_trailing_text_rejected(self):
  with self.assertRaises(ValueError):parse_object(json.dumps(self.sample())+' Commentary','sentences')
 def test_five_statements_rejected(self):
  obj=self.sample();obj['sentences']*=5
  with self.assertRaises(ValueError):parse_object(json.dumps(obj),'sentences')
 def test_missing_ids_rejected(self):
  obj=self.sample();obj['sentences'][0]['evidence_ids']=[]
  with self.assertRaises(ValueError):parse_object(json.dumps(obj),'sentences')
 def test_wrong_key_rejected(self):
  with self.assertRaises(ValueError):parse_object('{"summary":"text"}','sentences')
 def test_source_negation_not_substring_approval(self):self.assertFalse(exact_source_sentence('Treatment prevents infection.','We cannot conclude that Treatment prevents infection.'))
 def test_whole_source_sentence(self):self.assertTrue(exact_source_sentence('Treatment effect was uncertain.','We report results. Treatment effect was uncertain.'))
 def test_measurement_numbers_detected(self):self.assertTrue(numerical('MAD was 1.46 kcal/mol.'));self.assertTrue(numerical('A 23% increase.'));self.assertTrue(numerical('The value was 1.46.'))
 def test_model_identifier_not_measurement(self):self.assertFalse(numerical('ANI-1ccx performs differently.'));self.assertFalse(numerical('GDB-10to13 benchmark.'))
 def test_shared_retrieved_prose_across_conditions(self):
  prose=[{'evidence_id':'p','modality':'prose','text':'Results on cells.','section_path':['Results']}];table={'evidence_id':'t','modality':'table','text':'table'};chart={'evidence_id':'c','modality':'chart','text':'caption'}
  a,_=select(prose,'cells');b,_=select(prose+[table],'cells');c,_=select(prose+[table,chart],'cells');self.assertEqual(a['p'],b['p']);self.assertEqual(b['p'],c['p']);self.assertNotIn('c',b);self.assertIn('c',c)
 def test_no_record_truncation(self):
  records=[{'evidence_id':'long','modality':'prose','text':'x'*13000},{'evidence_id':'short','modality':'prose','text':'short result'}];selected,log=select(records,'result');self.assertNotIn('long',selected);self.assertIn('long',log['excluded_ids']);self.assertEqual(selected['short']['text'],'short result')
if __name__=='__main__':unittest.main()
