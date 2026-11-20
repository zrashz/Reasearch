import copy,json,unittest
from pathlib import Path
from researchqa.conformer_table_v1 import prepare,verify,correction,TEMPLATE
from researchqa.gpu_backend_v1 import GPUBackend
class NumericWriterChecks(unittest.TestCase):
    def setUp(self):
        self.e=json.loads((Path(__file__).parent/'conformer_source_fixture.json').read_text())
        self.s=prepare(self.e)
        self.item={'text':TEMPLATE.format(benchmark=self.s['benchmark'],limit=self.s['limit'],entity='ANI-1ccx-R',baseline='ANI-1ccx',new='2.54',base='2.07',percent='23'),'evidence_ids':list(self.e)}
    def test_unrelated_caution_ignored(self):
        from researchqa.sentence_nli_v1 import select_span
        self.assertFalse(select_span('Method improves torsion accuracy.','Computers are useful but costly. Method improves torsion accuracy.')['context_caution'])
    def test_related_caution_retained(self):
        from researchqa.sentence_nli_v1 import select_span
        self.assertTrue(select_span('Method improves torsion accuracy.','Method improves torsion accuracy only in small molecules.')['context_caution'])
    def test_referring_caution_retained(self):
        from researchqa.sentence_nli_v1 import select_span
        self.assertTrue(select_span('Method improves torsion accuracy.','Method improves torsion accuracy. However, this may not generalize.')['context_caution'])
    def test_real_cells_bound(self):
        self.assertEqual(self.s['values']['ANI-1ccx'],'2.07');self.assertEqual(self.s['values']['ANI-1ccx-R'],'2.54')
    def test_supported_full_scope(self):
        r=verify(self.item,self.e);self.assertEqual(r['label'],'Supported');self.assertFalse(r['scientific_approval'])
    def test_wrong_percent(self):
        self.item['text']=self.item['text'].replace('23%','36%');self.assertEqual(verify(self.item,self.e)['label'],'Refuted')
    def test_wrong_cell_value(self):
        self.item['text']=self.item['text'].replace('2.54','2.55');self.assertEqual(verify(self.item,self.e)['label'],'Refuted')
    def test_wrong_benchmark(self):
        self.item['text']=self.item['text'].replace('GDB-10to13','Other');self.assertEqual(verify(self.item,self.e)['label'],'Insufficient Evidence');self.assertIsNone(correction(self.item,self.e))
    def test_wrong_range(self):
        self.item['text']=self.item['text'].replace('within 100','within 50');self.assertEqual(verify(self.item,self.e)['label'],'Insufficient Evidence')
    def test_missing_table(self):
        e={k:v for k,v in self.e.items() if v['modality']=='prose'};self.assertEqual(verify(self.item,e)['label'],'Insufficient Evidence')
    def test_missing_scope_prose(self):
        e={k:v for k,v in self.e.items() if v['modality']=='table'};self.assertEqual(verify(self.item,e)['label'],'Insufficient Evidence')
    def test_ambiguous_source(self):
        self.e['duplicate']=copy.deepcopy(self.e[self.s['table_id']]);self.assertIsNone(prepare(self.e))
    def test_wrong_outcome_table(self):
        self.e[self.s['table_id']]['text']=self.e[self.s['table_id']]['text'].replace('conformer energy differences','atomic forces');self.assertIsNone(prepare(self.e))
    def test_scope_offsets(self):
        a,b=self.s['scope_offsets'];self.assertEqual(self.e[self.s['prose_id']]['text'][a:b],self.s['scope_quote'])
    def test_observed_requires_correction(self):
        self.item['text']='Training a model only to the smaller CCSD(T)*/CBS data set (ANI-1ccx-R) results in a 23% degradation in RMSD compared with the transfer learning model (ANI-1ccx).'
        self.assertEqual(verify(self.item,self.e)['label'],'Insufficient Evidence')
        self.item['evidence_ids']=[self.s['table_id']]
        fixed=correction(self.item,self.e);self.assertIsNotNone(fixed);self.assertEqual(verify(fixed,self.e)['label'],'Supported');self.assertIn(self.s['prose_id'],fixed['evidence_ids'])
    def test_wrong_percentage_corrected_and_rechecked(self):
        self.item['text']=self.item['text'].replace('23%','99%');fixed=correction(self.item,self.e);self.assertEqual(verify(fixed,self.e)['label'],'Supported')
    def test_ambiguous_as_well_not_approved(self):
        self.item['text']='ANI-1ccx performs as well as DFT within 100 kcal/mol.';self.assertIsNone(verify(self.item,self.e));self.assertIsNone(correction(self.item,self.e))
    def test_wrong_direction(self):
        self.item['text']=TEMPLATE.format(benchmark=self.s['benchmark'],limit='100',entity='ANI-1ccx',baseline='ANI-1ccx-R',new='2.07',base='2.54',percent='23')
        self.assertEqual(verify(self.item,self.e)['label'],'Refuted');self.assertIsNone(correction(self.item,self.e))
    def test_unknown_entity_not_repaired(self):
        self.item['text']=self.item['text'].replace('ANI-1ccx-R','Unknown');self.assertEqual(verify(self.item,self.e)['label'],'Insufficient Evidence');self.assertIsNone(correction(self.item,self.e))
    def test_metric_swap_not_handled(self):
        self.item['text']=self.item['text'].replace('RMSD','MAD');self.assertIsNone(verify(self.item,self.e))
    def test_merged_cells_block(self):
        self.e[self.s['table_id']]['text']=self.e[self.s['table_id']]['text'].replace('colspan="1"','colspan="2"',1);self.assertIsNone(prepare(self.e))
    def test_no_padding_or_automatic_retry(self):
        b=GPUBackend.__new__(GPUBackend);b.last_meta={};calls=[]
        def ask(*args):calls.append(args);return [{'text':'Short supported finding.','evidence_ids':[self.s['prose_id']]}]
        b.ask=ask;out=b.write([{'text':'Finding.','evidence_ids':[self.s['prose_id']]}],self.e)
        self.assertEqual(len(calls),1);self.assertFalse(b.last_meta['writer_length_pass']);self.assertEqual(b.last_meta['automatic_length_retries'],0)
    def test_backend_numeric_no_nli(self):
        b=GPUBackend.__new__(GPUBackend);r=b.verify(self.item,self.e);self.assertEqual(r['label'],'Supported');self.assertEqual(b.last_meta['model_calls'],0)
if __name__=='__main__':unittest.main()
