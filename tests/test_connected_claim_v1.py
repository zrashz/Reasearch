import importlib.util,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connected_claim_runner_v1 import TEMPLATE,assess
P=Path(__file__).resolve().parents[1]/'src/researchqa/scope_guard_v1.py'
if not P.exists():P=Path(__file__).resolve().parents[1]/'scope_guard_dependency.py'
spec=importlib.util.spec_from_file_location('guard_for_tests',P);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class ConnectedChecks(unittest.TestCase):
 def setUp(self):
  self.s={'prose':{'evidence_id':'p','text':'Table 1 provides mean absolute deviations (MAD). Reference values are recomputed at the CCSD(T)*/CBS level of theory. Table 1 only considers conformations within 100 kcal mol−1 of the energy minima for each molecule.'},'table_id':'t','caption':'Accuracy in predicting conformer energy differences on the GDB-10to13 benchmark','footnote':'aUnits are in kcal mol−1','values':{'ANI-1ccx':'1.46','ANI-1x':'1.97'}}
 def claim(self,**kw):return TEMPLATE.format(method=kw.get('method','ANI-1ccx'),value=kw.get('value','1.46'))
 def test_actual_value_bound(self):
  r=assess(self.claim(),self.s,guard);self.assertEqual(r['decision'],'Supported');self.assertFalse(r['scientific_approval'])
 def test_wrong_number_refuted(self):self.assertEqual(assess(self.claim(value='1.96'),self.s,guard)['decision'],'Refuted')
 def test_method_specific_value(self):self.assertEqual(assess(self.claim(method='ANI-1x'),self.s,guard)['decision'],'Refuted')
 def test_unknown_method_abstains(self):self.assertEqual(assess(self.claim(method='UNKNOWN'),self.s,guard)['decision'],'Insufficient Evidence')
 def test_outcome_swap_abstains(self):self.assertEqual(assess(self.claim().replace('conformer energy differences','atomization energy'),self.s,guard)['decision'],'Insufficient Evidence')
 def test_missing_condition_abstains(self):self.assertEqual(assess(self.claim().split(', considering')[0]+'.',self.s,guard)['decision'],'Insufficient Evidence')
 def test_extra_statement_abstains(self):self.assertEqual(assess(self.claim()+' It prevents disease.',self.s,guard)['decision'],'Insufficient Evidence')
 def test_missing_units_abstains(self):self.assertEqual(assess(self.claim().replace('1.46 kcal/mol','1.46'),self.s,guard)['decision'],'Insufficient Evidence')
 def test_ambiguous_source_fails(self):
  self.s['prose']['text']+=' mean absolute deviations (MAD)'
  with self.assertRaises(ValueError):assess(self.claim(),self.s,guard)
 def test_nan_abstains(self):self.assertEqual(assess(self.claim(value='NaN'),self.s,guard)['decision'],'Insufficient Evidence')
 def test_wrong_benchmark_abstains(self):self.assertEqual(assess(self.claim().replace('GDB-10to13','HC7'),self.s,guard)['decision'],'Insufficient Evidence')
if __name__=='__main__':unittest.main()
