"""Development stage controller. Backend quality is not established by routing tests."""
import copy
import re

LABELS={'Supported','Refuted','Insufficient Evidence'}


def claims(value, allowed):
    if not isinstance(value,list) or len(value)>8:
        raise ValueError('Expected at most eight statements')
    seen=set();result=[]
    for item in value:
        if not isinstance(item,dict) or set(item)!={'text','evidence_ids'}:
            raise ValueError('Invalid statement schema')
        text=item['text'];ids=item['evidence_ids']
        if not isinstance(text,str) or not text.strip() or text in seen:
            raise ValueError('Missing or duplicate statement')
        if not isinstance(ids,list) or not ids or any(not isinstance(x,str) or x not in allowed for x in ids):
            raise ValueError('Unknown/missing evidence anchor')
        seen.add(text);result.append(copy.deepcopy(item))
    return result


def checks(items, evidence, backend, stage, save):
    kept=[];log=[]
    for i,item in enumerate(items):
        decision=save(f'{stage}_{i}_check0',lambda:backend.verify(item,evidence))
        if decision.get('label') not in LABELS:raise ValueError('Invalid verifier label')
        entry={'original':copy.deepcopy(item),'first_check':decision,'correction_attempts':0}
        if decision['label']!='Supported':
            entry['correction_attempts']=1
            replacement=save(f'{stage}_{i}_correction',lambda:backend.correct(item,decision,evidence))
            if replacement is not None:
                replacement=claims([replacement],set(evidence))[0]
                final=save(f'{stage}_{i}_check1',lambda:backend.verify(replacement,evidence))
                if final.get('label') not in LABELS:raise ValueError('Invalid verifier label')
                entry['corrected']=replacement;entry['recheck']=final
                if final['label']=='Supported':kept.append(replacement)
            entry['withheld']=not ('recheck' in entry and entry['recheck']['label']=='Supported')
        else:
            kept.append(copy.deepcopy(item));entry['withheld']=False
        log.append(entry)
    return kept,log


def structure(items):
    summary=' '.join(x['text']+' ['+', '.join(x['evidence_ids'])+']' for x in items)
    words=len(' '.join(x['text'] for x in items).split())
    return {'summary':summary,'word_count_excluding_anchors':words,
            'within_80_120_words':80<=words<=120,'empty_output':not items,
            'sentence_count_not_guaranteed':True,'anchor_count':sum(len(x['evidence_ids']) for x in items)}


def run_condition(evidence, news_title, backend, save, outcome_save):
    """V0/V2 share raw draft; V1/V3 share prechecked draft.

    save must journal each external step and resume with validated inputs.
    """
    allowed=set(evidence)
    candidates=claims(save('extract',lambda:backend.extract(news_title,evidence)),allowed)
    raw=claims(save('draft_raw',lambda:backend.write(candidates,evidence)),allowed)
    outcome_save('V0', {'statements':raw,**structure(raw),'verification_enabled':False,'trace':[]})
    post_raw,log_raw=checks(raw,evidence,backend,'post_raw',save)
    outcome_save('V2',{'statements':post_raw,**structure(post_raw),'verification_enabled':True,'trace':log_raw})
    pre,log_pre=checks(candidates,evidence,backend,'pre',save)
    pre_draft=claims(save('draft_pre',lambda:backend.write(pre,evidence)) if pre else [],allowed)
    outcome_save('V1',{'statements':pre_draft,**structure(pre_draft),'verification_enabled':True,'trace':log_pre})
    post_pre,log_post=checks(pre_draft,evidence,backend,'post_pre',save)
    outcome_save('V3',{'statements':post_pre,**structure(post_pre),'verification_enabled':True,
                       'trace':{'pre':log_pre,'post':log_post}})
