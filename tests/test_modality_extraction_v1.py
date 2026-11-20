import unittest,json
from pathlib import Path
from researchqa.gpu_backend_v1 import GPUBackend,parse_object
from researchqa.conformer_table_v1 import prepare,verify,correction,TEMPLATE
class ModalChecks(unittest.TestCase):
 def setUp(self):
  self.e=json.loads((Path(__file__).parent/'conformer_source_fixture.json').read_text())
 def test_rounded_source_disagreement_withheld(self):
  s=prepare(self.e)
  item={'text':TEMPLATE.format(benchmark=s['benchmark'],limit=s['limit'],entity='ANI-1x',baseline='ANI-1ccx',new='2.79',base='2.07',percent='35'),'evidence_ids':list(self.e)}
  r=verify(item,self.e);self.assertEqual(r['label'],'Insufficient Evidence');self.assertEqual(r['reported_percentage'],'36');self.assertEqual(r['rounded_cell_percentage'],'35');self.assertIsNone(correction(item,self.e))
 def test_mixed_candidates_preserve_prose_and_numeric(self):
  e={**self.e,'chart':{'modality':'chart','text':'caption'}}
  b=GPUBackend.__new__(GPUBackend);calls=[]
  def ask(ins,payload,evidence,key):
   calls.append(evidence);b.last_meta={'model_calls':1,'raw_response':'retained'}
   return [{'text':'Chart finding.','evidence_ids':['chart']}] if 'chart' in evidence else [{'text':'Prose result '+chr(65+i)+'.','evidence_ids':[next(k for k in self.e if 'prose' in k)]} for i in range(4)]
  b.ask=ask;r=b.extract('title',e)
  self.assertEqual(len(calls),2);self.assertTrue(all(x['modality']=='prose' for x in calls[0].values()));self.assertEqual(len(r),4)
  self.assertEqual(r[0]['text'],'Prose result A.');self.assertEqual(r[1]['text'],'Prose result B.')
  self.assertIn('23% increase',r[2]['text']);self.assertNotIn('35% increase',str(b.last_meta['source_derived_numeric_hints']))
  self.assertEqual(r[3]['text'],'Chart finding.');self.assertEqual(b.last_meta['model_calls'],2);self.assertEqual(len(b.last_meta['extraction_steps']),2)
 def test_E1_no_table_or_chart_leak(self):
  e={k:v for k,v in self.e.items() if v['modality']=='prose'}
  b=GPUBackend.__new__(GPUBackend)
  def ask(*args):b.last_meta={'model_calls':1};return [{'text':'Prose finding.','evidence_ids':list(e)}]
  b.ask=ask;b.extract('title',e);self.assertEqual(b.last_meta['source_derived_numeric_hints'],[]);self.assertEqual(b.last_meta['model_calls'],1)
 def test_echo_response_still_rejected(self):
  with self.assertRaises(ValueError):parse_object('{"findings":[],"supporting_paper_evidence":{}}','sentences')
 def test_extraction_failure_preserves_metadata(self):
  b=GPUBackend.__new__(GPUBackend)
  def fail(*a):b.last_meta={'model_calls':1,'raw_response':'invalid'};raise ValueError('Invalid schema')
  b.ask=fail
  with self.assertRaises(ValueError):b.extract('title',self.e)
  self.assertEqual(b.last_meta['model_calls'],1);self.assertEqual(b.last_meta['extraction_steps'][0]['metadata']['raw_response'],'invalid')
