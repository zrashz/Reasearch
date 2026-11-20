"""Development sentence selection. Scores are uncalibrated, never scientific approval."""
import re

STOP = set("the a an of in on for and or to is are was were with by as that this it its at from we our has have been be after show shows conclude potential based".split())
CAUTION = re.compile(r"\b(however|although|except|limited|limitation|uncertain|not|cannot|may|might|could|suggest|preliminary|but|whereas|rather than)\b", re.I)

def background(text):
    return bool(re.search(r"\b(play|plays) an? (important|essential|key) role\b", text, re.I))

def terms(text):
    return set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", text.lower())) - STOP


def relevant_cautions(claim, spans, selected_index):
    """Narrow lexical context screen, not complete semantic scope checking."""
    query = terms(claim)
    found = []
    for index, span in enumerate(spans):
        text = span["text"]
        has_caution = bool(CAUTION.search(text)) or bool(
            re.search(r"\bonly\b", text, re.I)
        )
        if not has_caution:
            continue

        overlap = len(query & terms(text)) / max(1, len(query))
        refers_back = (
            index == selected_index + 1
            and bool(re.match(
                r"\s*(?:However[,]?\s+|But\s+|Nevertheless[,]?\s+)?"
                r"(?:this|these|it|such)\b",
                text, re.I
            ))
        )

        if index == selected_index or overlap >= .35 or refers_back:
            found.append(dict(span))
    return found


def select_span(claim, paragraph):
    # Source offsets are exact. No NLI score participates in selection.
    bounds=[0]+[m.end() for m in re.finditer(r"(?<=[.!?])\s+(?=[A-Z])", paragraph)]+[len(paragraph)]
    spans=[]
    for start,end in zip(bounds,bounds[1:]):
        raw=paragraph[start:end]; left=len(raw)-len(raw.lstrip()); right=len(raw.rstrip())
        if raw.strip():spans.append({'start':start+left,'end':start+right,'text':raw.strip()})
    if not spans:return None
    query=terms(claim)
    if not query:return None
    ranked=sorted(enumerate(spans),key=lambda p:(-len(query & terms(p[1]['text']))/len(query),p[0]))
    i,chosen=ranked[0]; coverage=len(query & terms(chosen['text']))/len(query)
    # Conservative lexical prerequisite, not semantic scope validation.
    if coverage < .60:return None
    neighbors=spans[max(0,i-1):min(len(spans),i+2)]
    return {**chosen,'lexical_coverage':coverage,'context_start':neighbors[0]['start'],
            'context_end':neighbors[-1]['end'],'context':paragraph[neighbors[0]['start']:neighbors[-1]['end']],
            'context_caution':bool(relevant_cautions(claim, spans, i)),
            'caution_spans':relevant_cautions(claim, spans, i),
            'selection_method':'maximum lexical claim coverage, source-order tie break; before NLI'}

def check_text(claim, cited, score):
    records=[]
    if background(claim):
        return {'label':'Insufficient Evidence','reason':'Background-only wording; finding selection unavailable',
                'scores':records,'scientific_approval':False,'scope_verified':False}
    for eid,entry in cited.items():
        paragraph=entry['text']; selected=select_span(claim,paragraph)
        if selected is None:
            return {'label':'Insufficient Evidence','reason':'No adequate lexical source sentence; scope unresolved',
                    'scores':records,'scientific_approval':False,'scope_verified':False}
        sentence_score=score(selected['text'],claim)
        context_score=score(selected['context'],claim)
        full_score=score(paragraph,claim)
        record={'evidence_id':eid,'source_span':selected,'uncalibrated_scores':sentence_score,
                'context_scores':context_score,'paragraph_scores':full_score}
        records.append(record)
        if any(x is None for x in (sentence_score,context_score,full_score)):
            record['supported']=False;record['withheld_reason']='Context exceeds 512 tokens; no silent truncation'
            continue
        contradicted=any(s.get('contradiction',0)>=.9 for s in (sentence_score,context_score,full_score))
        # When qualifiers occur anywhere in the source paragraph require full-context entailment too.
        caution_pass=not selected['context_caution'] or (context_score.get('entailment',0)>=.9 and full_score.get('entailment',0)>=.9)
        record['supported']=sentence_score.get('entailment',0)>=.9 and not contradicted and caution_pass
        record['withheld_reason']=None if record['supported'] else 'Support, contradiction, or contextual-qualifier checks unresolved'
    supported=bool(records) and all(r.get('supported',False) for r in records)
    return {'label':'Supported' if supported else 'Insufficient Evidence',
            'reason':'Development sentence entailment with context checks; uncalibrated, not scientific approval',
            'scores':records,'scientific_approval':False,'scope_verified':False,'independently_verified':False}
