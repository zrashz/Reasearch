from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from researchqa.scinews_live_v2 import source_findings,validate_exact_findings,parse_anchored_text

class SourceFixTests(unittest.TestCase):
    def setUp(self):
        self.e={'p1':{'modality':'prose','section_path':['Results'],'source_kind':'Abstract',
                     'text':'The trial found no significant difference in the primary outcome.'},
                'p2':{'modality':'prose','section_path':['Introduction'],'text':'An earlier study found benefit in a different study population.'}}
    def test_results_not_background_retrieval(self):
        from researchqa.scinews_runner_v2 import retrieve
        result=dict(self.e['p1'],evidence_id='p1')
        background=dict(self.e['p2'],evidence_id='p2',text='keyword '*100)
        selected,meta=retrieve([background,result],'keyword')
        self.assertEqual(meta['selected_ids'][0],'p1')

    def test_prompt_echo_rejected(self):
        with self.assertRaises(ValueError):validate_exact_findings([{'text':'One atomic paper-supported finding','evidence_ids':['p1']}],self.e)
    def test_selected_quotes_source_exact_and_no_background(self):
        found=source_findings(self.e)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['text'],self.e['p1']['text'])
        self.assertEqual(found[0]['evidence_ids'],['p1'])
    def test_only_background_fails_closed(self):
        with self.assertRaises(ValueError):source_findings({'p2':self.e['p2']})
    def test_markdown_draft_is_not_silently_repaired(self):
        with self.assertRaises(ValueError):parse_anchored_text('### News Summary\nUnanchored claims.',self.e)
    def test_unknown_and_trailing_content_rejected(self):
        for raw in ['Claim. [wrong]','Claim. [p1] Extra uncited fact.']:
            with self.assertRaises(ValueError):parse_anchored_text(raw,self.e)
    def test_plain_anchored_output_accepted_as_syntax_only(self):
        self.assertEqual(parse_anchored_text('A statement. [p1]',self.e),[{'text':'A statement.','evidence_ids':['p1']}])

if __name__=='__main__':unittest.main()
