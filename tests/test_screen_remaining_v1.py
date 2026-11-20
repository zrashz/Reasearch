import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from screen_remaining_v1 import doi,screen
class Response:
 def __init__(self,payload=None,content=b''):self.payload=payload;self.content=content;self.url='https://www.ebi.ac.uk/test'
 def raise_for_status(self):pass
 def json(self):return self.payload
class Session:
 def __init__(self,items):self.items=iter(items);self.calls=0
 def get(self,*a,**k):self.calls+=1;return next(self.items)
class ScreenChecks(unittest.TestCase):
 def test_prefix_normalization(self):self.assertEqual(doi('dx.doi.org/10.1038/NATURE1'),'10.1038/nature1')
 def test_truncated_link_not_repaired(self):self.assertIsNone(doi('www.nature.com/ … /article.html'))
 def test_unknown_doi_no_network(self):
  s=Session([]);r=screen({'record_id':'train:1','doi':'bad'},s,Path('/tmp'));self.assertEqual(s.calls,0);self.assertEqual(r['eligibility'],'pending')
 def test_wrong_xml_doi_not_saved(self):
  s=Session([Response({'resultList':{'result':[{'doi':'10.1/notvalid'}]}})])
  # DOI syntactic validity is intentionally checked before lookup.
  self.assertEqual(screen({'record_id':'train:1','doi':'10.1/notvalid'},s,Path('/tmp'))['status'],'doi_review_required')
 def test_identity_mismatch_blocks_xml(self):
  s=Session([Response({'resultList':{'result':[{'doi':'10.1038/example','pmcid':'PMC123'}]}}),Response(content=b'<article><front><article-meta><article-id pub-id-type="doi">10.1038/other</article-id></article-meta></front></article>')])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'xml').mkdir();r=screen({'record_id':'train:1','doi':'10.1038/example'},s,p)
   self.assertEqual(r['status'],'retrieval_or_identity_review_required');self.assertEqual(list((p/'xml').iterdir()),[])
 def test_success_is_not_eligibility(self):
  raw=b'<article><front><article-meta><article-id pub-id-type="doi">10.1038/example</article-id><title-group><article-title>Study</article-title></title-group></article-meta></front><body><p>Result</p><table-wrap/><fig/></body></article>'
  s=Session([Response({'resultList':{'result':[{'doi':'10.1038/example','pmcid':'PMC123'}]}}),Response(content=raw)])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'xml').mkdir();r=screen({'record_id':'train:1','doi':'10.1038/example'},s,p)
   self.assertEqual(r['status'],'xml_saved_review_pending');self.assertEqual(r['eligibility'],'pending');self.assertEqual(r['table_elements'],1)
if __name__=='__main__':unittest.main()
