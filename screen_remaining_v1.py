"""Resumeable public XML availability screen. No eligibility approval or model use."""
import argparse,csv,hashlib,json,re,time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

BASE='https://www.ebi.ac.uk/europepmc/webservices/rest'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def doi(s):
    s=re.sub(r'^(?:https?://)?(?:dx\.)?doi\.org/','',s.strip(),flags=re.I)
    s=re.sub(r'^doi:\s*','',s,flags=re.I)
    return s.lower() if re.fullmatch(r'10\.\d{4,9}/\S+',s,re.I) else None

def screen(row,session,out):
    result={'record_id':row['record_id'],'original_doi':row['doi'],'doi':doi(row['doi']),
            'eligibility':'pending','model_calls':0,'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
    if not result['doi']:return {**result,'status':'doi_review_required'}
    def get(url,**kw):
        r=session.get(url,timeout=(10,30),**kw);r.raise_for_status();return r
    try:
        d=result['doi'];r=get(BASE+'/search',params={'query':f'DOI:"{d}"','format':'json','pageSize':100})
        result['search_url']=r.url
        hits=[x for x in r.json().get('resultList',{}).get('result',[]) if doi(x.get('doi',''))==d]
        pmcs=sorted({x['pmcid'] for x in hits if re.fullmatch('PMC[0-9]+',x.get('pmcid',''))})
        if len(pmcs)!=1:return {**result,'status':'no_unique_pmc_candidate','candidate_pmcids':pmcs}
        result['pmcid']=pmcs[0];r=get(BASE+'/'+pmcs[0]+'/fullTextXML')
        raw=r.content;root=ET.fromstring(raw)
        ids=[x for x in root.findall('./front/article-meta/article-id') if x.get('pub-id-type')=='doi']
        if d not in {doi(''.join(x.itertext())) for x in ids}:raise ValueError('XML DOI identity mismatch')
        filename=row['record_id'].replace(':','_')+'.xml';path=out/'xml'/filename
        if path.exists():
            if path.read_bytes()!=raw:raise ValueError('Different XML already exists; review before replacing')
        else:
            with path.open('xb') as f:f.write(raw)
        body=root.find('./body'); title=root.find('./front/article-meta/title-group')
        result.update(status='xml_saved_review_pending',source_url=r.url,xml_file='xml/'+filename,
                      xml_sha256=hashlib.sha256(raw).hexdigest(),paper_title=' '.join(''.join(title.itertext()).split()) if title is not None else '',
                      body_prose_elements=len(body.findall('.//p')) if body is not None else 0,
                      table_elements=len(root.findall('.//table-wrap')),figure_elements=len(root.findall('.//fig')),
                      related_articles=[dict(x.attrib) for x in root.findall('.//related-article')],
                      image_readability_reviewed=False,structural_counts_only=True)
    except Exception as e:result.update(status='retrieval_or_identity_review_required',error=type(e).__name__+': '+str(e))
    return result

def main():
    import requests
    p=argparse.ArgumentParser();p.add_argument('--metadata',required=True);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    p.add_argument('--start',type=int,default=30);p.add_argument('--limit',type=int,default=270);a=p.parse_args()
    if a.start<0 or a.limit<1:raise ValueError('Invalid range')
    meta=Path(a.metadata);original=json.loads(Path(a.manifest).read_text())
    if digest(meta)!=original['metadata_sha256']:raise ValueError('Metadata changed')
    with meta.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    selected=rows[a.start:a.start+a.limit]
    if not selected:raise ValueError('Empty range')
    ids=[r['record_id'] for r in selected]
    if len(ids)!=len(set(ids)) or any(not re.fullmatch(r'train:\d+',i) for i in ids):raise ValueError('Unexpected record identities')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);(out/'xml').mkdir(exist_ok=True)
    identity={'metadata_sha256':digest(meta),'runner_sha256':digest(__file__),'start':a.start,'limit':a.limit,'record_ids':ids}
    config=out/'run_identity.json'
    if config.exists():
        if json.loads(config.read_text())!=identity:raise ValueError('Resume identity changed')
    else:
        if any(x.name not in {'xml'} for x in out.iterdir()):raise ValueError('Nonempty unknown run directory')
        config.write_text(json.dumps(identity,indent=2))
    session=requests.Session();session.headers['User-Agent']='ScientificNewsResearch/1.0'
    results=[]
    for i,row in enumerate(selected,1):
        path=out/(row['record_id'].replace(':','_')+'_screen.json')
        if path.exists():
            result=json.loads(path.read_text())
            if result['record_id']!=row['record_id'] or result['original_doi']!=row['doi']:raise ValueError('Cached record identity mismatch')
            if result.get('xml_file') and digest(out/result['xml_file'])!=result['xml_sha256']:raise ValueError('Cached XML changed')
            mode='cached'
        else:
            result=screen(row,session,out)
            with path.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
            mode='new';time.sleep(.4)
        results.append(result);print(f"{i}/{len(selected)} {row['record_id']} {mode}: {result['status']}",flush=True)
        summary={'records':len(results),'target_records':len(selected),'status_counts':dict(Counter(x['status'] for x in results)),
                 'confirmed_eligible_studies':0,'model_calls':0,'image_downloads':0,'original_queue_modified':False}
        temporary=out/'summary.pending';temporary.write_text(json.dumps(summary,indent=2));temporary.replace(out/'summary.json')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
