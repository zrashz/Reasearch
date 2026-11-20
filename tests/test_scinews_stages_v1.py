import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from researchqa.scinews_stages_v1 import claims,run_condition,structure
from researchqa.scinews_live_v1 import DevelopmentBackend

E={'p1':{'text':'A source sentence.','modality':'prose'}}
C={'text':'A source sentence.','evidence_ids':['p1']}

class Fake:
    """Synthetic routing fixture, never an empirical verifier."""
    def __init__(self,label='Supported',fix=None):self.label=label;self.fix=fix;self.writes=[];self.verifies=[];self.corrections=0
    def extract(self,title,evidence):return [copy.deepcopy(C)]
    def write(self,candidates,evidence):self.writes.append(copy.deepcopy(candidates));return copy.deepcopy(candidates)
    def verify(self,item,evidence):self.verifies.append(copy.deepcopy(item));return {'label':self.label}
    def correct(self,item,decision,evidence):self.corrections+=1;return copy.deepcopy(self.fix)


def execute(backend):
    events={};outcomes={}
    def save(name,call):
        if name not in events:events[name]=call()
        return copy.deepcopy(events[name])
    run_condition(E,'relevance title',backend,save,lambda k,v:outcomes.update({k:v}))
    return events,outcomes

class StageTests(unittest.TestCase):
    def test_supported_paths_and_paired_drafts(self):
        b=Fake();events,out=execute(b)
        self.assertEqual(set(out),{'V0','V1','V2','V3'})
        self.assertEqual(out['V0']['statements'],out['V2']['statements'])
        self.assertEqual(out['V1']['statements'],out['V3']['statements'])
        self.assertEqual(b.corrections,0)
        self.assertEqual(len(b.writes),2)
        self.assertEqual([k for k in events if 'check' in k],['post_raw_0_check0','pre_0_check0','post_pre_0_check0'])
    def test_withhold_no_padding_and_no_pre_draft_when_all_rejected(self):
        b=Fake('Insufficient Evidence');_,out=execute(b)
        self.assertFalse(out['V0']['empty_output'])
        for v in ('V1','V2','V3'):self.assertTrue(out[v]['empty_output'])
        self.assertEqual(b.corrections,2)
        self.assertEqual(len(b.writes),1)
        self.assertEqual(out['V2']['word_count_excluding_anchors'],0)
    def test_correction_bounded_then_rechecked(self):
        b=Fake('Refuted',C);events,out=execute(b)
        self.assertEqual(b.corrections,2)
        self.assertIn('post_raw_0_check1',events)
        self.assertIn('pre_0_check1',events)
        self.assertNotIn('post_raw_0_check2',events)
        self.assertTrue(out['V2']['empty_output'])
    def test_correction_unknown_anchor_rejected(self):
        b=Fake('Refuted',{'text':'replacement','evidence_ids':['chart_leak']})
        with self.assertRaises(ValueError):execute(b)
    def test_unknown_candidate_anchor_rejected(self):
        with self.assertRaises(ValueError):claims([{'text':'x','evidence_ids':['missing']}],set(E))
    def test_duplicate_candidate_rejected(self):
        with self.assertRaises(ValueError):claims([C,C],set(E))
    def test_invalid_verifier_output_is_not_neutral(self):
        with self.assertRaises(ValueError):execute(Fake('Technical Failure'))
    def test_empty_draft_not_length_pass(self):
        self.assertFalse(structure([])['within_80_120_words'])
        self.assertEqual(structure([])['anchor_count'],0)
    def test_numerical_backend_does_not_call_nli_or_approve(self):
        b=object.__new__(DevelopmentBackend)
        r=b.verify({'text':'A rate of 38.2 percent.','evidence_ids':['p1']},E)
        self.assertEqual(r['label'],'Insufficient Evidence')
        self.assertEqual(b.last_meta['model_calls'],0)
    def test_unavailable_numerical_correction_no_model_call(self):
        b=object.__new__(DevelopmentBackend)
        self.assertIsNone(b.correct(C,{'reason':'Numerical verification unavailable for this assertion.'},E))
        self.assertEqual(b.last_meta['model_calls'],0)

if __name__=='__main__':unittest.main()
