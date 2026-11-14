import unittest
from dataclasses import replace
import noepin_al_175_decision_envelope_artifact as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('decision_generated_by_dcsr','decision_changed_by_dcsr','source_envelope_mutated','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def prep(st,t='2026-11-13T11:00:00+00:00'):
 return m.evaluate_prepared(st,integrity_validated=True,current_envelope_fingerprint=st.envelope_fingerprint,current_binding_query_fingerprint=st.binding_query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=t)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.binding_decision==m.BindingDecision.MATCH and r.envelope_decision==m.Decision.ALLOW and r.envelope_fingerprint_valid and r.request_match and r.intent_match and r.policy_match and r.evidence_match and r.risk_match and r.time_active and r.reasons_present and r.decision_valid and r.next_gate_candidate
 if k==1:
  r=m.evaluate(replace(q,current_request_id='REQ-OTHER')); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.REQUEST_BINDING_MISMATCH
 if k==2:
  r=m.evaluate(replace(q,current_intent_fingerprint=m._seed_fp('OTHER'))); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.INTENT_BINDING_MISMATCH
 if k==3:
  r=m.evaluate(replace(q,current_policy_fingerprint=m._seed_fp('OTHER'))); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.POLICY_BINDING_MISMATCH
 if k==4:
  r=m.evaluate(replace(q,current_evidence_fingerprint=m._seed_fp('OTHER'))); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.EVIDENCE_BINDING_MISMATCH
 if k==5:
  r=m.evaluate(replace(q,current_risk_fingerprint=m._seed_fp('OTHER'))); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.RISK_BINDING_MISMATCH
 if k==6:
  r=m.evaluate(replace(q,at_time='2026-11-13T12:00:01+00:00')); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.ENVELOPE_EXPIRED
 if k==7:
  r=m.evaluate(replace(q,at_time='2026-11-13T09:59:59+00:00')); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.ENVELOPE_NOT_YET_ACTIVE
 if k==8:
  bad=replace(q.envelope,fingerprint='0'*64); r=m.evaluate(replace(q,envelope=bad)); return r.binding_decision==m.BindingDecision.DENY and r.escalation==m.Escalation.ENVELOPE_FINGERPRINT_MISMATCH
 if k==9:
  try: m.build_envelope(decision='UNKNOWN',request_id='r',reasons=('x',),intent_fingerprint='0'*64,policy_fingerprint='1'*64,evidence_fingerprint='2'*64,risk_fingerprint='3'*64,issued_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T11:00:00+00:00'); return False
  except ValueError: return True
 if k==10:
  try: m.build_envelope(decision='ALLOW',request_id='r',reasons=(),intent_fingerprint='0'*64,policy_fingerprint='1'*64,evidence_fingerprint='2'*64,risk_fingerprint='3'*64,issued_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T11:00:00+00:00'); return False
  except ValueError: return True
 if k==11:
  try: m.build_envelope(decision='ALLOW',request_id='r',reasons=('x',),intent_fingerprint='Z'*64,policy_fingerprint='1'*64,evidence_fingerprint='2'*64,risk_fingerprint='3'*64,issued_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T11:00:00+00:00'); return False
  except ValueError: return True
 if k==12:
  try: m.build_envelope(decision='ALLOW',request_id='r',reasons=('x',),intent_fingerprint='0'*64,policy_fingerprint='1'*64,evidence_fingerprint='2'*64,risk_fingerprint='3'*64,issued_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T10:00:00+00:00'); return False
  except ValueError: return True
 if k==13:
  try: m.build_envelope(decision='ALLOW',request_id='r',reasons=('x',),intent_fingerprint='0'*64,policy_fingerprint='1'*64,evidence_fingerprint='2'*64,risk_fingerprint='3'*64,issued_time='2026-11-13T10:00:00',expiry_time='2026-11-13T11:00:00+00:00'); return False
  except ValueError: return True
 if k==14:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.binding_decision==m.BindingDecision.MATCH
 if k==15:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_envelope_fingerprint=st.envelope_fingerprint,current_binding_query_fingerprint=st.binding_query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time); return r.engine_state==m.EngineState.INVALID
 if k==16:
  st=m.prepare_state(q,B,E); r=prep(st,'2026-11-13T12:00:01+00:00'); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.ENVELOPE_EXPIRED
 if k==17:
  st=m.prepare_state(q,B,E); e2=m.build_envelope(decision=m.Decision.HOLD,request_id=q.envelope.request_id,reasons=('New reason',),intent_fingerprint=q.envelope.intent_fingerprint,policy_fingerprint=q.envelope.policy_fingerprint,evidence_fingerprint=q.envelope.evidence_fingerprint,risk_fingerprint=q.envelope.risk_fingerprint,issued_time=q.envelope.issued_time,expiry_time=q.envelope.expiry_time); q2=replace(q,envelope=e2); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('DECISION_ENVELOPE',)
 if k==18:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,current_request_id='REQ-OTHER'),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('BINDING_QUERY',)
 if k==19:
  r=m.default_evaluation(); a=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r==a and m._canon(r)==m._canon(a) and len(q.envelope.fingerprint)==64
 return False
class TestAL175(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL175,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
