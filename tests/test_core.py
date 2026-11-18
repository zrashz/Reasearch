import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import unittest
from researchqa.core import get,normalize_label,sciver_metrics,make_split

class ResearchChecks(unittest.TestCase):
    def test_nested_mapping(self):
        self.assertEqual(get({"sections":[{"text":"a"},{"text":"b"}]},"/sections/*/text"),["a","b"])
        self.assertIsNone(get({},"/absent"))
    def test_explicit_label_mapping(self):
        with self.assertRaises(ValueError):normalize_label(True,{})
        self.assertEqual(normalize_label(True,{"true":"Supported"}),"Supported")
    def test_abstention_counts_against_accuracy(self):
        m=sciver_metrics(["Supported","Refuted"],["Supported","Insufficient Evidence"])
        self.assertEqual(m["accuracy"],0.5)
        self.assertEqual(m["response_rate"],0.5)
        self.assertAlmostEqual(m["macro_f1"],0.5)
    def test_no_response_has_no_decisive_accuracy(self):
        m=sciver_metrics(["Supported"],["Technical Failure"])
        self.assertEqual(m["accuracy"],0)
        self.assertIsNone(m["decisive_accuracy"])
    def test_pilot_does_not_enter_test(self):
        rows=[{"study_id":str(i),"eligible":"yes","previously_inspected":"yes" if i==0 else "no"} for i in range(5)]
        a=make_split(rows,{"development":1,"validation":1,"test":2})
        self.assertEqual(a[0]["study_id"],"0")
        self.assertEqual(a[0]["split"],"development")
        self.assertEqual(len({r["study_id"] for r in a}),4)
    def test_duplicate_studies_rejected(self):
        rows=[{"study_id":"x","eligible":"yes","previously_inspected":"no"}]*2
        with self.assertRaises(ValueError):make_split(rows,{"development":1,"validation":0,"test":1})

if __name__=="__main__":unittest.main()
