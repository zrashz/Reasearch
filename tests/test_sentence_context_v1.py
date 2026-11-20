import unittest,json
from researchqa.sentence_nli_v1 import select_span,check_text,background
from researchqa.gpu_backend_v1 import GPUBackend,parse_object,numerical
S={'entailment':.96,'neutral':.03,'contradiction':.01}
N={'entailment':.01,'neutral':.98,'contradiction':.01}
C={'entailment':.01,'neutral':.01,'contradiction':.98}
class Checks(unittest.TestCase):
    def test_exact_offsets(self):
        p='Background explains chemistry. ANI-1ccx outperforms DFT on torsion benchmarks. Other results follow.'
        a=select_span('ANI-1ccx outperforms DFT on torsion benchmarks.',p)
        self.assertEqual(p[a['start']:a['end']],a['text'])
        self.assertEqual(p[a['context_start']:a['context_end']],a['context'])
    def test_sentence_selected_before_scores(self):
        seen=[]
        def scorer(p,c):seen.append(p);return S
        check_text('ANI-1ccx outperforms DFT on torsion benchmarks.',{'p':{'text':'Background explains chemistry. ANI-1ccx outperforms DFT on torsion benchmarks. Other results follow.'}},scorer)
        self.assertEqual(seen[0],'ANI-1ccx outperforms DFT on torsion benchmarks.')
    def test_paragraph_neutral_sentence_supported_development_only(self):
        calls=iter([S,N,N])
        r=check_text('Method improves torsion accuracy.',{'p':{'text':'Background chemistry. Method improves torsion accuracy. Other results follow.'}},lambda *a:next(calls))
        self.assertEqual(r['label'],'Supported');self.assertFalse(r['scientific_approval']);self.assertFalse(r['scope_verified'])
    def test_context_contradiction_blocks(self):
        calls=iter([S,C,N])
        r=check_text('Method improves torsion accuracy.',{'p':{'text':'Method improves torsion accuracy.'}},lambda *a:next(calls))
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_qualifier_missing_blocks(self):
        calls=iter([S,N,N])
        r=check_text('Method improves torsion accuracy.',{'p':{'text':'Method improves torsion accuracy only in small molecules.'}},lambda *a:next(calls))
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_negation_context_blocks(self):
        r=check_text('Method improves torsion accuracy.',{'p':{'text':'Method improves torsion accuracy. However this does not generalize.'}},lambda *a:N)
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_wrong_comparator_not_approved(self):
        r=check_text('Method outperforms CCSD on torsion benchmarks.',{'p':{'text':'Method outperforms DFT on torsion benchmarks.'}},lambda *a:N)
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_no_lexical_match(self):
        self.assertIsNone(select_span('Neural method improves protein binding.','Rain affects river levels.'))
    def test_over_budget_context_blocks(self):
        calls=iter([S,None,None])
        r=check_text('Method improves torsion accuracy.',{'p':{'text':'Method improves torsion accuracy.'}},lambda *a:next(calls))
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_background_no_inference(self):
        def fail(*a):raise AssertionError('No call expected')
        r=check_text('Molecular torsions play an important role in chemistry.',{},fail)
        self.assertEqual(r['label'],'Insufficient Evidence')
    def test_alias_preserved(self):
        i={'text':'Finding.','evidence_ids':['p']}
        self.assertEqual(parse_object(json.dumps({'key_sentences':[i]}),'sentences'),[i])
    def test_ambiguous_alias_rejected(self):
        with self.assertRaises(ValueError):parse_object('{"key_sentences":[],"sentences":[]}','sentences')
    def test_invalid_correction_withheld(self):
        b=GPUBackend.__new__(GPUBackend);b.last_meta={'raw_response':'kept'}
        def fail(*a):raise ValueError('Unexpected keys')
        b.ask=fail
        self.assertIsNone(b.correct({'text':'Finding','evidence_ids':['p']},{'reason':'Unresolved'},{'p':{}}))
        self.assertTrue(b.last_meta['correction_withheld']);self.assertEqual(b.last_meta['raw_response'],'kept')
    def test_measurement_policy_preserved(self):
        b=GPUBackend.__new__(GPUBackend)
        r=b.verify({'text':'Method error is 1.46 kcal/mol.','evidence_ids':['p']},{'p':{'modality':'prose','text':'Method error is 1.46 kcal/mol.'}})
        self.assertEqual(r['label'],'Insufficient Evidence')
if __name__=='__main__':unittest.main()
