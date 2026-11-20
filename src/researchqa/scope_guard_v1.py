"""Structured, source-linked scope gate. No automatic semantic scope extraction."""
from decimal import Decimal, InvalidOperation

FIELDS=('outcome','population','comparison','condition','measure','unit')


def num(value):
    if value is None or isinstance(value,bool):raise ValueError('Invalid number')
    try:value=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as e:raise ValueError('Invalid number') from e
    if not value.is_finite():raise ValueError('Nonfinite number')
    return value


def span(text,reference):
    if not isinstance(reference,dict):return False
    start,end,quote=reference.get('start'),reference.get('end'),reference.get('quote')
    return (isinstance(start,int) and not isinstance(start,bool) and isinstance(end,int)
            and not isinstance(end,bool) and 0<=start<end<=len(text)
            and isinstance(quote,str) and text[start:end]==quote)


def check_scope_value(claim,contract,evidence):
    """Compare one attributed numeric assertion, never a full summary.

    Contract attributes are externally prepared canonical values, not model gold.
    Matching strings and quotation provenance do not prove semantic equivalence.
    """
    base={'scientific_approval':False,'whole_claim_assessed':False,
          'semantic_scope_extraction_implemented':False}
    def abstain(reason,**extra):
        return {**base,'decision':'Insufficient Evidence','reason':reason,**extra}
    if not isinstance(contract,dict) or not isinstance(evidence,dict):raise ValueError('Invalid source contract')
    scope=contract.get('scope')
    if not isinstance(scope,dict) or any(not isinstance(scope.get(f),str) or not scope[f].strip() for f in FIELDS):
        raise ValueError('Source scope is incomplete')
    refs=contract.get('scope_references',{})
    for f in FIELDS:
        entries=refs.get(f)
        if not isinstance(entries,list) or not entries:raise ValueError('Missing source reference: '+f)
        for ref in entries:
            eid=ref.get('evidence_id') if isinstance(ref,dict) else None
            if eid not in evidence or not span(evidence[eid]['text'],ref):
                raise ValueError('Invalid source scope quotation: '+f)
    value_ref=contract.get('value_reference',{})
    eid=value_ref.get('evidence_id')
    if eid not in evidence or not span(evidence[eid]['text'],value_ref):raise ValueError('Invalid source value quotation')
    expected=num(contract.get('value'))
    if num(value_ref['quote'])!=expected:raise ValueError('Contract value differs from source quotation')
    if not isinstance(claim,dict) or not isinstance(claim.get('text'),str):return abstain('Missing claim text')
    observed_scope=claim.get('scope',{})
    if not isinstance(observed_scope,dict) or any(not isinstance(observed_scope.get(f),str) or not observed_scope[f].strip() for f in FIELDS):
        return abstain('Missing claim scope attributes')
    if not span(claim['text'],claim.get('value_reference')):return abstain('Claim value quotation invalid')
    try:
        observed=num(claim.get('value'))
        if num(claim['value_reference']['quote'])!=observed:return abstain('Extracted value differs from written claim')
    except ValueError:return abstain('Claim number unparseable')
    mismatches=[f for f in FIELDS if scope[f]!=observed_scope[f]]
    if mismatches:return abstain('Source cannot verify a different attributed scope',mismatched_scope_fields=mismatches)
    if contract.get('scope_mapping_review_status')!='reviewed':return abstain('Canonical source scope mapping has not been reviewed')
    if claim.get('scope_mapping_review_status')!='reviewed':return abstain('Claim scope mapping has not been reviewed')
    return {**base,'decision':'Supported' if observed==expected else 'Refuted',
            'reason':'One numeric assertion compared within reviewed canonical scope',
            'source_value':str(expected),'claim_value':str(observed),
            'source_evidence_id':eid,'source_contract_id':contract.get('contract_id')}
