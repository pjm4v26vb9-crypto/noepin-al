import unittest, math
from dataclasses import replace
import noepin_al_166_semantic_importance_precision_allocator as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('element_specs_mutated','bit_allocation_committed','quantization_executed','source_values_mutated','precision_profile_written','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_elements_fingerprint=st.elements_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.PRECISION_ALLOCATION_CANDIDATE and r.budget_feasible and r.next_gate_candidate and not any(neg(r))
 if k==1:
  r=m.evaluate(q); by={a.element_id:a for a in r.allocations}; return all(by[f'EL-{i:04d}'].bit_width>=q.critical_floor_bit for i in (0,127,255,511)) and by['EL-0255'].bit_width==q.max_bit and by['EL-0255'].unknown_critical
 if k==2:
  r=m.evaluate(q); return r.budget_adjustment_count>0 and r.estimated_total_bits<=q.total_bit_budget and all(a.bit_width>=q.critical_floor_bit for a in r.allocations if a.critical)
 if k==3:
  qq=replace(q,total_bit_budget=1000); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.BUDGET_BELOW_MANDATORY_PRECISION and r.original_retention_candidate and not r.next_gate_candidate
 if k==4:
  els=list(q.elements); els[1]=replace(els[1],element_id=els[0].element_id); r=m.evaluate(replace(q,elements=tuple(els))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DUPLICATE_ELEMENT_ID
 if k==5:
  r=m.evaluate(replace(q,min_bit=13,max_bit=12)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.INVALID_CONFIGURATION
 if k==6:
  els=list(q.elements); els[4]=replace(els[4],importance=1.5); r=m.evaluate(replace(q,elements=tuple(els))); return r.escalation==m.Escalation.INVALID_IMPORTANCE
 if k==7:
  els=list(q.elements); els[4]=replace(els[4],error_sensitivity=float('nan')); r=m.evaluate(replace(q,elements=tuple(els))); return r.escalation==m.Escalation.NONFINITE_INPUT
 if k==8:
  els=list(q.elements); els[10]=replace(els[10],importance=None,error_sensitivity=None); r=m.evaluate(replace(q,elements=tuple(els))); a=next(x for x in r.allocations if x.element_id=='EL-0010'); return q.min_bit<=a.bit_width<=q.max_bit and not a.unknown_critical
 if k==9:
  qq=m.PrecisionAllocationRequest('X',(m.ElementSpec('LOW',0.0,0.0,False),m.ElementSpec('HIGH',1.0,1.0,False)),4,12,10,24,B,E); r=m.evaluate(qq); by={a.element_id:a for a in r.allocations}; return by['LOW'].bit_width<by['HIGH'].bit_width
 if k==10:
  r=m.evaluate(q); return all(a.dcsr_priority=='P0' for a in r.allocations if a.critical)
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_elements_fingerprint=st.elements_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_elements_fingerprint='0'*64,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); els=list(q.elements); els[5]=replace(els[5],importance=min(1.0,(els[5].importance or 0)+0.01)); st2=m.prepare_state(replace(q,elements=tuple(els)),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('EL-0005',) and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,total_bit_budget=q.total_bit_budget-1),B,E); return 'PRECISION_CONFIG' in m.plan_missing_only(st,st2).missing_or_changed_record_ids
 if k==16:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==17:
  r=m.default_evaluation(); return not any(neg(r)) and all(x in r.reasons for x in ('CRITICAL_FLOOR_PRESERVED','UNKNOWN_CRITICAL_MAX_BIT_PRESERVED','PRECISION_ALLOCATION_IS_CANDIDATE_NOT_COMMIT'))
 if k==18:
  r=m.evaluate(replace(q,elements=())); return r.escalation==m.Escalation.EMPTY_ELEMENTS and r.decision==m.Decision.HOLD
 if k==19:
  # Minimal exact budget remains feasible without violating floor.
  qq=m.PrecisionAllocationRequest('Y',(m.ElementSpec('C',0.1,0.1,True),m.ElementSpec('N',0.0,0.0,False)),4,12,10,14,B,E); r=m.evaluate(qq); return r.decision==m.Decision.ALLOW and r.estimated_total_bits==14 and r.critical_floor_preserved
 return False
class TestAL166(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL166,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
