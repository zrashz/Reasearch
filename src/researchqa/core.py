import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def records(path, prefix="item"):
    path = Path(path)
    with path.open("rb") as f:
        if path.suffix.lower() == ".jsonl":
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if not isinstance(r, dict):
                        raise ValueError("Every record must be an object")
                    yield r
        else:
            try:
                import ijson
            except ImportError as exc:
                raise RuntimeError("Install requirements.txt for streaming large JSON arrays") from exc
            count = 0
            for r in ijson.items(f, prefix, use_float=True):
                if not isinstance(r, dict):
                    raise ValueError("Wrong prefix: expected record objects")
                count += 1
                yield r
            if not count:
                raise ValueError("No records found; confirm JSON prefix")


def get(record, pointer):
    """JSON pointer with * to collect arrays; absent paths return None."""
    if not pointer:
        return None
    parts = pointer.strip("/").split("/")
    def walk(obj, tokens):
        if not tokens:
            return obj
        key, *rest = tokens
        key = key.replace("~1", "/").replace("~0", "~")
        if key == "*" and isinstance(obj, list):
            return [walk(v, rest) for v in obj]
        if isinstance(obj, dict):
            return walk(obj[key], rest) if key in obj else None
        if isinstance(obj, list) and key.isdigit():
            return walk(obj[int(key)], rest) if int(key) < len(obj) else None
        return None
    return walk(record, parts)


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(as_text(v) for v in value)
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValueError("Select a leaf field or section text path, not an entire object")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf8")


def schema(value, prefix=""):
    rows = []
    if isinstance(value, dict):
        for k, v in value.items():
            escaped = str(k).replace("~", "~0").replace("/", "~1")
            rows.extend(schema(v, prefix + "/" + escaped))
    elif isinstance(value, list):
        rows.append({"path":prefix,"type":"list","length":len(value)})
        if value:
            rows.extend(schema(value[0], prefix + "/*"))
    else:
        rows.append({"path":prefix,"type":type(value).__name__,
                     "characters":len(str(value)) if value is not None else 0})
    return rows


def normalize_label(value, mapping):
    # Explicit mapping avoids silently assuming True/False semantics.
    key = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if key not in mapping:
        raise ValueError("Unmapped raw label encoding: " + key)
    label = mapping[key]
    if label not in ("Supported", "Refuted"):
        raise ValueError("Gold mappings must use Supported or Refuted")
    return label


def sciver_metrics(gold, predictions):
    if not gold or len(gold) != len(predictions):
        raise ValueError("Require nonempty aligned gold and predictions")
    classes = ("Supported", "Refuted")
    allowed = (*classes, "Insufficient Evidence", "Technical Failure")
    if any(g not in classes for g in gold) or any(p not in allowed for p in predictions):
        raise ValueError("Unexpected label")
    rows = {}
    for c in classes:
        tp = sum(g == c and p == c for g,p in zip(gold,predictions))
        fp = sum(g != c and p == c for g,p in zip(gold,predictions))
        fn = sum(g == c and p != c for g,p in zip(gold,predictions))
        rows[c] = {"precision":tp/(tp+fp) if tp+fp else 0.0,
                   "recall":tp/(tp+fn) if tp+fn else 0.0,
                   "f1":2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0}
    n = len(gold)
    decisive = sum(p in classes for p in predictions)
    correct = sum(g == p for g,p in zip(gold,predictions))
    return {"n":n,"accuracy":correct/n,
            "macro_f1":sum(v["f1"] for v in rows.values())/2,
            "response_rate":decisive/n,
            "decisive_accuracy":correct/decisive if decisive else None,
            "abstentions":predictions.count("Insufficient Evidence"),
            "technical_failures":predictions.count("Technical Failure"),
            "technical_failure_policy":"Included in attempted-population denominator; report separately",
            "per_class":rows}


def make_split(rows, targets, seed=62):
    if len({r["study_id"] for r in rows}) != len(rows):
        raise ValueError("One selected pair per reviewed underlying study is required")
    eligible = [r for r in rows if r["eligible"].lower() == "yes"
                and r["previously_inspected"].lower() in ("yes","no")]
    inspected = [r for r in eligible if r["previously_inspected"].lower() == "yes"]
    untouched = [r for r in eligible if r["previously_inspected"].lower() == "no"]
    rng = random.Random(seed)
    rng.shuffle(inspected);rng.shuffle(untouched)
    devn, valn, testn = (targets[k] for k in ("development","validation","test"))
    # All known inspected/pilot studies are development-only; excess are excluded.
    dev = inspected[:devn]
    need = devn-len(dev)
    if len(untouched) < need+valn+testn:
        raise ValueError("Not enough reviewed untouched studies; do not silently reduce targets")
    dev += untouched[:need]; untouched = untouched[need:]
    val = untouched[:valn]; test = untouched[valn:valn+testn]
    return [{**r,"split":split} for split, group in
            (("development",dev),("validation",val),("test",test)) for r in group]
