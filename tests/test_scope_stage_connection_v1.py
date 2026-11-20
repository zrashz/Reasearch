import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
import connected_claim_runner_v1 as connected
from researchqa import scope_guard_v1 as guard
from researchqa.scinews_stages_v1 import run_condition
from researchqa.scope_stage_backend_v1 import ScopeStageBackend,SavedClaimReplay,OBSERVED
class StageScopeChecks(unittest.TestCase):
 def setUp(self):
  self.source={'prose':{'evidence_id':'p','text':'Table 1 provides mean absolute deviations (MAD). Reference values are recomputed at the CCSD(T)*/CBS level of theory. Table 1 only considers conformations within 100 kcal mol−1 of the energy minima for each molecule.'},'table_id':'t','caption':'Accuracy in predicting conformer energy differences on the GDB-10to13 benchmark','footnote':'aUnits are in kcal mol−1','values':{'ANI-1ccx':'1.46','ANI-1x':'1.97'}}
  self.evidence={'p':self.source['prose'],'t':{'text':'table','modality':'table'}}
  self.item={'text':OBSERVED.format(method='ANI-1ccx',value='1.46'),'evidence_ids':['p','t']}
 def backend(self,item=None):return ScopeStageBackend(SavedClaimReplay(item or self.item),self.source,guard,connected)
 def route(self,item=None):
  backend=self.backend(item);events={};out={}
  def save(name,call):events[name]=call();return events[name]
  run_condition(self.evidence,'title',backend,save,lambda n,v:out.update({n:v}));return events,out
 def test_observed_missing_benchmark_not_supported(self):
  d=self.backend().verify(self.item,self.evidence);self.assertEqual(d['label'],'Insufficient Evidence');self.assertIsNone(d['scientific_verdict_on_original_claim'])
 def test_source_assisted_correct_then_recheck(self):
  b=self.backend();before=copy.deepcopy(self.item);d=b.verify(self.item,self.evidence);new=b.correct(self.item,d,self.evidence)
  self.assertEqual(self.item,before);self.assertEqual(b.verify(new,self.evidence)['label'],'Supported');self.assertFalse(b.verify(new,self.evidence)['scientific_approval'])
 def test_all_routes_and_paired_drafts(self):
  events,out=self.route();self.assertEqual(set(out),{'V0','V1','V2','V3'});self.assertEqual(out['V0']['statements'],events['draft_raw']);self.assertEqual(out['V1']['statements'],events['draft_pre']);self.assertIn('METHOD is',out['V0']['summary']);self.assertIn('On the GDB',out['V2']['summary']);self.assertFalse(out['V3']['within_80_120_words'])
 def test_one_correction_per_enabled_stage(self):
  events,out=self.route();self.assertEqual(out['V2']['trace'][0]['correction_attempts'],1);self.assertEqual(out['V1']['trace'][0]['correction_attempts'],1);self.assertEqual(out['V3']['trace']['post'][0]['correction_attempts'],0);self.assertNotIn('post_raw_0_check2',events)
 def test_wrong_value_replaced_from_source(self):
  item={'text':connected.TEMPLATE.format(method='ANI-1ccx',value='9.99'),'evidence_ids':['p','t']};b=self.backend(item);d=b.verify(item,self.evidence);self.assertEqual(d['label'],'Refuted');new=b.correct(item,d,self.evidence);self.assertIn('1.46',new['text']);self.assertEqual(b.verify(new,self.evidence)['label'],'Supported')
 def test_missing_table_anchor_withheld(self):
  item=copy.deepcopy(self.item);item['evidence_ids']=['p'];b=self.backend(item);d=b.verify(item,self.evidence);self.assertEqual(d['label'],'Insufficient Evidence');self.assertIsNone(b.correct(item,d,self.evidence))
 def test_unknown_sentence_withheld_without_filler(self):
  item={'text':'This unsupported claim prevents all illnesses.','evidence_ids':['p','t']};_,out=self.route(item);self.assertEqual(out['V3']['statements'],[]);self.assertFalse(out['V3']['within_80_120_words'])
 def test_unrecognized_method_not_invented(self):
  item={'text':OBSERVED.format(method='Unknown',value='1.46'),'evidence_ids':['p','t']};b=self.backend(item);d=b.verify(item,self.evidence);self.assertEqual(d['label'],'Insufficient Evidence');self.assertIsNone(b.correct(item,d,self.evidence))
if __name__=='__main__':unittest.main()
