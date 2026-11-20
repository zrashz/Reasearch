"""Source-specific MAD adapter/decorator for the existing stage controller.

It does not implement general semantic extraction or independent evaluation.
"""
import copy
import importlib.util
import re
from pathlib import Path

OBSERVED=("METHOD is {method}, which has a mean absolute deviation (MAD) of {value} kcal/mol "
          "for conformer energy differences relative to CCSD(T)*/CBS, considering conformations "
          "within 100 kcal/mol of each molecule's energy minimum.")
OBSERVED_PATTERN=re.compile(re.escape(OBSERVED).replace(r'\{method\}',r'(?P<method>[^,\n]+)').replace(r'\{value\}',r'(?P<value>\d+(?:\.\d+)?)'))

def connected_module(project):
    path=Path(project)/'connected_claim_runner_v1.py'
    spec=importlib.util.spec_from_file_location('scope_stage_connected_dependency',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class ScopeStageBackend:
    def __init__(self,base,source,guard,connected):
        self.base=base;self.source=source;self.guard=guard;self.connected=connected
        self.last_meta={'model_calls':0}
        self.config={**getattr(base,'config',{}),'scope_adapter':'train14460 Tab1 MAD exact grammar',
                     'correction':'one source-assisted replacement per enabled controller stage',
                     'independent_review_completed':False,'general_semantic_extraction':False}
    def _delegate(self,name,*args):
        self.base.last_meta={'model_calls':0}
        try:return getattr(self.base,name)(*args)
        finally:self.last_meta=copy.deepcopy(getattr(self.base,'last_meta',{'model_calls':0}))
    def extract(self,title,evidence):return self._delegate('extract',title,evidence)
    def write(self,items,evidence):return self._delegate('write',items,evidence)
    def _parse(self,text):
        standard=self.connected.PATTERN.fullmatch(text.strip())
        observed=OBSERVED_PATTERN.fullmatch(text.strip())
        return standard or observed, bool(observed and not standard)
    def _binding(self,item,evidence):
        refs=item.get('evidence_ids',[])
        required={self.source['table_id'],self.source['prose']['evidence_id']}
        return (isinstance(refs,list) and required.issubset(refs)
                and all(eid in evidence for eid in refs))
    def verify(self,item,evidence):
        match,missing_benchmark=self._parse(item['text'])
        if not match:return self._delegate('verify',item,evidence)
        self.last_meta={'model_calls':0,'method':'source-bound scoped numeric adapter'}
        if not self._binding(item,evidence):return {'label':'Insufficient Evidence','reason':'Required source table/prose anchors unavailable','failure_category':'scope_binding_unresolved','scientific_approval':False}
        if match['method'] not in self.source['values']:return {'label':'Insufficient Evidence','reason':'Method header unresolved','scientific_approval':False}
        if missing_benchmark:
            return {'label':'Insufficient Evidence','reason':'Benchmark absent from original claim; source-assisted completion required',
                    'failure_category':'missing_explicit_benchmark','scientific_verdict_on_original_claim':None,'scientific_approval':False}
        result=self.connected.assess(item['text'],self.source,self.guard)
        return {'label':result['decision'],'reason':result.get('reason'),'numeric_result':result,'scientific_approval':False}
    def correct(self,item,decision,evidence):
        match,missing=self._parse(item['text'])
        if not match:return self._delegate('correct',item,decision,evidence)
        self.last_meta={'model_calls':0,'method':'source-assisted scope/value correction','correction_is_model_generated':False}
        if not self._binding(item,evidence) or match['method'] not in self.source['values']:return None
        method=match['method'];value=self.source['values'][method]
        corrected=self.connected.TEMPLATE.format(method=method,value=value)
        if corrected==item['text']:return None
        # Validate quoted source provenance before offering a replacement; controller rechecks independently.
        probe=self.connected.assess(corrected,self.source,self.guard)
        if probe['decision']!='Supported':return None
        self.last_meta.update(benchmark_added_from_source=missing,
                              numeric_value_changed=value!=match['value'],original_preserved_in_stage_trace=True)
        return {'text':corrected,'evidence_ids':copy.deepcopy(item['evidence_ids'])}

class SavedClaimReplay:
    """Identity writer for wiring checks, explicitly not summary generation."""
    def __init__(self,item):
        self.item=copy.deepcopy(item);self.last_meta={'model_calls':0}
        self.config={'mode':'saved_claim_replay_identity_writer','summary_generation_performed':False}
    def extract(self,title,evidence):
        self.last_meta={'model_calls':0,'method':'saved model claim with externally prepared source anchors'}
        return [copy.deepcopy(self.item)]
    def write(self,items,evidence):
        self.last_meta={'model_calls':0,'method':'identity writer; no summary length padding'}
        return copy.deepcopy(items)
    def verify(self,item,evidence):
        self.last_meta={'model_calls':0}
        return {'label':'Insufficient Evidence','reason':'Unsupported assertion outside numeric adapter','scientific_approval':False}
    def correct(self,item,decision,evidence):
        self.last_meta={'model_calls':0};return None
