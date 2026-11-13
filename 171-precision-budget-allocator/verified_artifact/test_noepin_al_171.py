import unittest
from dataclasses import replace
import noepin_al_171_precision_budget_allocator as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('source_components_mutated','quantization_executed','allocation_committed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_components_fingerprint=st.components_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.all_minimum_floors_preserved and r.all_critical_floors_preserved and r.budget_feasible and r.next_gate_candidate
 if k==1:
  minimum=sum(c.element_count*m._floor_bits(c) for c in q.components); r=m.evaluate(replace(q,total_bit_budget=minimum-1,total_byte_budget=10**9)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MINIMUM_BUDGET_INSUFFICIENT
 if k==2:
  minimum=sum(c.element_count*m._floor_bits(c) for c in q.components); r=m.evaluate(replace(q,total_bit_budget=10**9,total_byte_budget=(minimum-1)//8)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MINIMUM_BUDGET_INSUFFICIENT
 if k==3:
  r=m.default_evaluation(); d={a.component_id:a for a in r.allocations}; return d['CRIT-A'].allocated_bits>=10 and d['CRIT-B'].allocated_bits>=9 and d['CRIT-C'].allocated_bits>=9
 if k==4:
  r=m.default_evaluation(); return r.allocated_total_bits<=r.effective_bit_budget and r.estimated_total_bytes==(r.allocated_total_bits+7)//8
 if k==5:
  r=m.default_evaluation(); a=sorted(r.allocations,key=lambda x:(-x.weight,x.component_id)); return a[0].allocated_bits>=a[-1].allocated_bits
 if k==6:
  cs=list(q.components); cs[0]=replace(cs[0],available=False); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.COMPONENT_UNAVAILABLE
 if k==7:
  cs=list(q.components); cs[0]=replace(cs[0],importance=float('nan')); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.DENY and r.engine_state==m.EngineState.INVALID
 if k==8:
  cs=list(q.components); cs[1]=replace(cs[1],component_id=cs[0].component_id); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.HOLD and r.engine_state==m.EngineState.INVALID
 if k==9:
  cs=list(q.components); cs[0]=replace(cs[0],critical_floor_bits=15,max_bits=14); r=m.evaluate(replace(q,components=tuple(cs))); return r.engine_state==m.EngineState.INVALID
 if k==10:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_components_fingerprint=st.components_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_components_fingerprint='0'*64,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); cs=list(q.components); cs[4]=replace(cs[4],importance=0.87); st2=m.prepare_state(replace(q,components=tuple(cs)),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('PRECISION_COMPONENTS',) and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,total_bit_budget=q.total_bit_budget+8),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('PRECISION_BUDGET_CONFIG',)
 if k==16:
  minimum=sum(c.element_count*m._floor_bits(c) for c in q.components); qq=replace(q,total_bit_budget=minimum,total_byte_budget=(minimum+7)//8); r=m.evaluate(qq); return r.decision==m.Decision.ALLOW and r.allocated_total_bits==minimum and all(a.allocated_bits==a.floor_bits for a in r.allocations)
 if k==17:
  r=m.default_evaluation(); return all(a.allocated_bits<=next(c.max_bits for c in q.components if c.component_id==a.component_id) for a in r.allocations)
 if k==18:
  r=m.default_evaluation(); return r.unused_bits>=0 and r.effective_bit_budget==min(q.total_bit_budget,q.total_byte_budget*8)
 if k==19:
  r=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r.engine_state==m.EngineState.PRECISION_BUDGET_CANDIDATE
 return False
class TestAL171(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL171,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
