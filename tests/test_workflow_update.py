"""Software fixtures only; not scientific benchmark results."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from researchqa import workflow as w
from researchqa.extraction_guard import guard_attributes
from researchqa.numerical import check_percentage_claim


def fixture(project):
    case=project/w.CASE;case.mkdir(parents=True)
    original=project/w.SCREEN/'train_5_article.xml'
    original.write_text('<article><front><article-meta><article-id pub-id-type="doi">10.1136/bmj.l6131</article-id></article-meta></front></article>')
    correction=case/'correction_original.xml'
    correction.write_text('<article><front><article-meta><article-id pub-id-type="doi">10.1136/bmj.n3072</article-id></article-meta></front></article>')
    table=ET.Element('table-wrap',id='tbl3');row=ET.SubElement(ET.SubElement(table,'table'),'tr')
    for value in ['Admittance to NICU ≥4 days','21/55 (38.2)','36/81 (44.4)','0.86 (0.57 to 1.30)','0.58']:
        ET.SubElement(row,'td').text=value
    corrected=case/'table3_corrected_development_v1.xml';corrected.write_bytes(ET.tostring(table))
    values={'duration_operator':'>=','duration_days':4,
        'induction':{'numerator':21,'denominator':55,'reported_percentage':38.2},
        'expectant_management':{'numerator':36,'denominator':81,'reported_percentage':44.4}}
    w.write(case/'table3_correction_overlay_v1.json',{'source_xml_sha256':w.digest(original),'correction_xml_sha256':w.digest(correction),'corrected_record':values})
    w.write(case/'table3_corrected_development_manifest_v1.json',{'source_article_sha256':w.digest(original),'derived_table_sha256':w.digest(corrected)})
    extraction={'claim_text_without_citation':'The induction group had a 38.2% rate of infants admitted to NICU for at least four days.',
        'extracted_attributes':{'outcome':'NICU_duration','population':'all_trial_participants','duration_operator':'>=','duration_days':4,'duration_unit':'days','value_unit':'percent','group':'induction','numerator':38.2,'denominator':100,'value':38.2}}
    w.write(case/'claim_extraction_checker_v1.json',extraction)
    w.write(case/'evidence_candidates_v1.json',{'source_xml_sha256':w.digest(original),
        'E1_prose_candidates':[{'evidence_id':'test_p1','source_kind':'Body','section_path':['Example'],'text':'Software fixture paragraph.'}],
        'E2_table_candidates':[{'evidence_id':'test_table3','source_id':'tbl3','table_wrap_xml':ET.tostring(table,encoding='unicode')}]})
    return case


class WorkflowChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.project=Path(self.temp.name);self.case=fixture(self.project)
    def tearDown(self):self.temp.cleanup()
    def test_observed_extraction_replay_is_withheld(self):
        path=self.case/'claim_extraction_checker_v1.json';before=path.read_bytes()
        result=w.check_saved(self.project,path)
        self.assertEqual(result['checker_result']['decision'],'Insufficient Evidence')
        self.assertEqual(set(result['checker_result']['fields']),{'population','numerator','denominator'})
        self.assertEqual(path.read_bytes(),before)
        self.assertFalse(result['automatic_approval'])
    def test_original_source_mismatch_fails(self):
        (self.project/w.SCREEN/'train_5_article.xml').write_text('changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):w.source_evidence(self.project)
    def test_changed_corrected_row_even_with_updated_hash_fails(self):
        path=self.case/'table3_corrected_development_v1.xml';path.write_text(path.read_text().replace('21/55','22/55'))
        manifest=self.case/'table3_corrected_development_manifest_v1.json';value=w.read(manifest);value['derived_table_sha256']=w.digest(path);manifest.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'row'):w.source_evidence(self.project)
    def test_E2_preserves_E1_and_adds_corrected_table(self):
        out=self.project/'out';out.mkdir();result=w.prepare_conditions(self.project,out)
        e1=[json.loads(x) for x in (out/'E1_evidence.jsonl').read_text().splitlines()]
        e2=[json.loads(x) for x in (out/'E2_evidence.jsonl').read_text().splitlines()]
        self.assertEqual(e2[:len(e1)],e1);self.assertIn('21/55',e2[-1]['text']);self.assertFalse(result['E3_ready'])
    def test_wrapper_only_JSON_parsing_and_schema(self):
        attrs=w.read(self.case/'claim_extraction_checker_v1.json')['extracted_attributes']
        parsed,fence=w.parse_object('```json\n'+json.dumps(attrs)+'\n```');self.assertTrue(fence);self.assertEqual(parsed,attrs)
        with self.assertRaises(ValueError):w.parse_object('Explanation '+json.dumps(attrs))
        attrs['population']=['bad'];
        with self.assertRaises(ValueError):w.parse_object(json.dumps(attrs))
    def test_guard_preserves_raw_and_recognizes_explicit_form(self):
        attrs=w.read(self.case/'claim_extraction_checker_v1.json')['extracted_attributes'];before=dict(attrs)
        guarded,flags=guard_attributes('An induction rate of 38.2%.',attrs)
        self.assertEqual(attrs,before);self.assertIsNone(guarded['numerator']);self.assertEqual(len(flags),3)
        attrs.update(population='Table3_NICU_duration_subgroup',numerator=21,denominator=55)
        result,flags=guard_attributes('In the Table 3 NICU-duration subgroup, induction had 21/55 (38.2%).',attrs)
        self.assertEqual(result,attrs);self.assertEqual(flags,[])
    def test_numerical_mismatch_and_scope_mismatch_are_distinct(self):
        evidence=w.source_evidence(self.project)
        claim={k:evidence[k] for k in ['outcome','population','duration_operator','duration_days','duration_unit','value_unit']}
        claim.update(group='induction',numerator=21,denominator=55,value=38.2)
        self.assertEqual(check_percentage_claim(claim,evidence)['decision'],'Supported')
        claim['value']=61.8;self.assertEqual(check_percentage_claim(claim,evidence)['decision'],'Refuted')
        claim['duration_operator']='>';self.assertEqual(check_percentage_claim(claim,evidence)['decision'],'Insufficient Evidence')
    def test_exclusive_write_preserves_results(self):
        path=self.project/'x.json';w.write(path,{'one':1})
        with self.assertRaises(FileExistsError):w.write(path,{'two':2})
        self.assertEqual(w.read(path),{'one':1})
    def test_CLI_replay_creates_distinct_runs_without_models(self):
        script=Path(__file__).resolve().parents[1]/'research_workflow.py'
        for _ in range(2):
            result=subprocess.run([sys.executable,str(script),'replay-saved','--project',str(self.project)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        runs=list((self.project/'private/workflow_runs').iterdir());self.assertEqual(len(runs),2)
        for run in runs:self.assertEqual(w.read(run/'result.json')['additional_model_calls'],0)

if __name__=='__main__':unittest.main()
