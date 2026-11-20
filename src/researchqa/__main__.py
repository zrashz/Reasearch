import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from .core import records, get, as_text, sha, schema, write_json, normalize_label, sciver_metrics, make_split


def main():
    p = argparse.ArgumentParser(description="Research preparation tools; no model inference")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("schema")
    s.add_argument("--input",required=True);s.add_argument("--prefix",default="item")
    s.add_argument("--output",required=True);s.add_argument("--sample",type=int,default=3)
    s = sub.add_parser("audit")
    s.add_argument("--mapping",required=True);s.add_argument("--output",required=True)
    s = sub.add_parser("split")
    s.add_argument("--review",required=True);s.add_argument("--output",required=True)
    s.add_argument("--config",default="configs/study.json")
    s = sub.add_parser("matrix")
    s.add_argument("--output",required=True)
    s = sub.add_parser("evaluate-sciver")
    s.add_argument("--gold",required=True);s.add_argument("--predictions",required=True)
    s.add_argument("--output",required=True)
    a = p.parse_args()
    if a.command == "schema":
        if not 1 <= a.sample <= 20:
            p.error("sample must be 1..20")
        result=[]
        for i,r in enumerate(records(a.input,a.prefix)):
            result.append({"row_zero_based":i,"fields":schema(r)})
            if len(result)>=a.sample:break
        write_json(a.output,{"input_sha256":sha(a.input),"prefix":a.prefix,
                              "sampled_schema_only":True,"records":result})
        print("Saved schema metadata only. No raw claim/news text printed.")
    elif a.command == "audit":
        cfg=json.loads(Path(a.mapping).read_text(encoding="utf8"))
        if cfg.get("confirmed") is not True:
            raise ValueError("Confirm actual field paths after schema inspection first")
        kind=cfg["dataset"]; fields=cfg["fields"]
        required=("news_text","paper_text") if kind=="scinews" else ("claim","label","paperid")
        if kind not in ("scinews","sciver"):raise ValueError("Unsupported dataset")
        if any(not fields.get(k) for k in required):raise ValueError("Missing field mapping")
        if kind=="scinews" and fields["news_text"]==fields["paper_text"]:
            raise ValueError("News and paper fields cannot be the same")
        out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
        counts=Counter();labels=Counter();groups=defaultdict(set);hashes=set();duplicates=0;missing=Counter()
        modalities=Counter();reasoning=Counter();manifest=[]
        with (out/"record_index.csv").open("w",newline="",encoding="utf8") as f:
            w=csv.DictWriter(f,fieldnames=["record_id","source_split","source_row","provisional_group_hash","exact_duplicate"])
            w.writeheader()
            for split,entry in cfg["files"].items():
                path=entry["path"];manifest.append({"split":split,"sha256":sha(path)})
                for i,r in enumerate(records(path,entry.get("prefix","item"))):
                    values={k:get(r,v) for k,v in fields.items()}
                    for k in required:
                        if values[k] is None or (isinstance(values[k],str) and not values[k].strip()):missing[k]+=1
                    counts[split]+=1
                    if counts[split] % 1000 == 0:
                        print(f"Progress: {split}: {counts[split]:,} records", flush=True)
                    import hashlib
                    raw=json.dumps(r,sort_keys=True,ensure_ascii=False).encode()
                    digest=hashlib.sha256(raw).hexdigest()
                    if kind=="scinews":
                        news=as_text(values["news_text"]);paper=as_text(values["paper_text"])
                        digest=hashlib.sha256(json.dumps([news,paper],ensure_ascii=False).encode()).hexdigest()
                        # Triage only: a year or ID also contains digits.
                        import re
                        counts["screen_candidates"]+=int(len(news)>=200 and len(paper)>=1000 and bool(re.search(r"\d",news)))
                        doi=as_text(values.get("doi")).strip().lower()
                        doi=re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)","",doi)
                        identity=("doi:"+doi if doi else "url:"+as_text(values.get("paper_url")).strip()
                                  if as_text(values.get("paper_url")).strip() else "paper:"+paper if paper else "unknown:"+split+":"+str(i))
                    else:
                        identity="paper:"+as_text(values["paperid"])
                        if not values["paperid"]:identity="unknown:"+split+":"+str(i)
                        if values["label"] is not None:
                            labels[normalize_label(values["label"],cfg["label_map"])]+=1
                        modalities[as_text(values.get("type")) or "UNKNOWN"]+=1
                        reasoning[as_text(values.get("claim_type")) or "UNKNOWN"]+=1
                    group=hashlib.sha256(identity.encode()).hexdigest()
                    groups[group].add(split)
                    duplicate=digest in hashes;duplicates+=duplicate;hashes.add(digest)
                    w.writerow({"record_id":f"{split}:{i}","source_split":split,"source_row":i,
                                "provisional_group_hash":group,"exact_duplicate":duplicate})
        result={"dataset":kind,"by_split":{k:counts[k] for k in cfg["files"]},
                "records":sum(counts[k] for k in cfg["files"]),"missing_required":dict(missing),
                "duplicate_records":duplicates,"duplicate_definition":"Exact news+paper text for SciNews; whole-record hash for SciVer",
                "provisional_groups":len(groups),"groups_crossing_source_splits":sum(len(s)>1 for s in groups.values()),
                "labels":dict(labels),"modalities":dict(modalities),"reasoning":dict(reasoning),
                "screen_candidates":counts["screen_candidates"] if kind=="scinews" else None,
                "source_hashes":manifest,"mapping":fields,
                "limitations":["Provisional grouping, not near-duplicate resolution","No confirmed eligibility","No evidence readability/content validation","No model inference","Counts may differ from previous audits using different duplicate definitions"]}
        write_json(out/"audit_summary.json",result)
        print(json.dumps(result,indent=2))
    elif a.command == "split":
        cfg=json.loads(Path(a.config).read_text())
        with open(a.review,encoding="utf8",newline="") as f:rows=list(csv.DictReader(f))
        result=make_split(rows,cfg["planned_pairs"],cfg["seed"])
        write_json(a.output,{"status":"provisional split plan; not proof of eligibility or test readiness",
                            "review_sha256":sha(a.review),"seed":cfg["seed"],"records":result})
        print("Saved provisional study-level split plan")
    elif a.command == "matrix":
        write_json(a.output,{"status":"design only; no outcomes generated","configurations":[
            {"id":f"V{v}-E{e}","pre_verify":v in (1,3),"post_verify":v in (2,3),
             "evidence":e,"shared_draft_group":"unverified" if v in (0,2) else "preverified"}
            for v in range(4) for e in range(1,4)]})
        print("Saved 12 configurations, not experimental results")
    elif a.command == "evaluate-sciver":
        def load(path):
            out={}
            for r in records(path):
                key=r["record_id"]
                if key in out:raise ValueError("Duplicate record_id")
                out[key]=r
            return out
        gold=load(a.gold);pred=load(a.predictions)
        if set(gold)!=set(pred):raise ValueError("Gold/prediction IDs differ; do not silently drop cases")
        keys=sorted(gold)
        result=sciver_metrics([gold[k]["gold_label"] for k in keys],[pred[k]["prediction"] for k in keys])
        result["gold_sha256"]=sha(a.gold);result["predictions_sha256"]=sha(a.predictions)
        write_json(a.output,result);print(json.dumps(result,indent=2))

if __name__=="__main__":main()
