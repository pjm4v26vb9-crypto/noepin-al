import unittest
from dataclasses import replace
import noepin_al_177_execution_receipt_artifact as m
Q=m.default_request(); B=Q.binding; E=Q.state_epoch
NEG=('receipt_status_promoted_to_world_truth','receipt_status_promoted_to_action_success','result_digest_promoted_to_truth','postcondition_promoted_to_truth','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed_by_artifact','action_success_promoted','rollback_executed','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted_to_success','dcsr_generated_success_receipt','dcsr_changed_receipt_status','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def kw(**x):
 r=Q.receipt
 d=dict(receipt_id=r.receipt_id,request_id=r.request_id,permit_id=r.permit_id,action=r.action,target=r.target,started_at=r.started_at,finished_at=r.finished_at,status=r.status,changes=r.changes,postconditions=r.postconditions,rollback_reference=r.rollback_reference,intent_fingerprint=r.intent_fingerprint,policy_fingerprint=r.policy_fingerprint,result_digest=r.result_digest,issuer_authority_id=r.issuer_authority_id); d.update(x); return d
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.binding_decision==m.BindingDecision.MATCH and r.next_gate_candidate and r.receipt_fingerprint_valid and r.receipt_status==m.ReceiptStatus.SUCCEEDED and r.postcondition_count==2
 if k==1:
  r=m.evaluate(replace(Q,expected_permit_id='OTHER')); return r.binding_decision==m.BindingDecision.HOLD and r.escalation==m.Escalation.BINDING_MISMATCH and not r.permit_match
 if k==2:
  r=m.evaluate(replace(Q,expected_request_id='OTHER')); return r.binding_decision==m.BindingDecision.HOLD and not r.request_match
 if k==3:
  r=m.evaluate(replace(Q,expected_action='OTHER')); return r.binding_decision==m.BindingDecision.HOLD and not r.action_match
 if k==4:
  r=m.evaluate(replace(Q,expected_target='OTHER')); return r.binding_decision==m.BindingDecision.HOLD and not r.target_match
 if k==5:
  bad=replace(Q.receipt,fingerprint='0'*64); r=m.evaluate(replace(Q,receipt=bad)); return r.binding_decision==m.BindingDecision.DENY and r.escalation==m.Escalation.RECEIPT_FINGERPRINT_MISMATCH
 if k==6:
  try: m.build_receipt(**kw(status='UNKNOWN')); return False
  except ValueError: return True
 if k==7:
  try: m.build_receipt(**kw(finished_at='2026-11-13T16:29:59+00:00')); return False
  except ValueError: return True
 if k==8:
  try: m.build_receipt(**kw(postconditions=())); return False
  except ValueError: return True
 if k==9:
  try: m.build_receipt(**kw(status=m.ReceiptStatus.PARTIAL,postconditions=(),rollback_reference=None)); return False
  except ValueError: return True
 if k==10:
  rct=m.build_receipt(**kw(status=m.ReceiptStatus.PARTIAL,postconditions=(),rollback_reference='RB-177-A')); q=replace(Q,receipt=rct,expected_request_id=rct.request_id,expected_permit_id=rct.permit_id,expected_action=rct.action,expected_target=rct.target); r=m.evaluate(q); return r.binding_decision==m.BindingDecision.MATCH and r.receipt_status==m.ReceiptStatus.PARTIAL and r.rollback_reference_present and not r.partial_state_promoted_to_success
 if k==11:
  rct=m.build_receipt(**kw(status=m.ReceiptStatus.ROLLED_BACK,postconditions=(),rollback_reference='RB-177-B')); return rct.status==m.ReceiptStatus.ROLLED_BACK and bool(rct.rollback_reference)
 if k==12:
  try: m.build_receipt(**kw(result_digest='Z'*64)); return False
  except ValueError: return True
 if k==13:
  try: m.build_receipt(**kw(started_at='2026-11-13T16:30:00')); return False
  except ValueError: return True
 if k==14:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_receipt_fingerprint=st.receipt_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return r==st.result
 if k==15:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_receipt_fingerprint=st.receipt_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==16:
  st=m.prepare_state(Q,B,E); r2=m.build_receipt(**kw(changes=Q.receipt.changes+('additional change evidence',))); q2=replace(Q,receipt=r2); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('CHANGE_SEGMENT:RCPT-177-A',) and not p.full_resend_required
 if k==17:
  st=m.prepare_state(Q,B,E); r2=m.build_receipt(**kw(receipt_id='RCPT-177-B')); q2=replace(Q,receipt=r2); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('RECEIPT:RCPT-177-B',) and not p.full_resend_required
 if k==18:
  st=m.prepare_state(Q,B,E); st2=m.prepare_state(replace(Q,expected_target='artifact:OTHER'),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('BINDING_QUERY',)
 if k==19:
  r=m.default_evaluation(); a=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r==a and m._canon(r)==m._canon(a) and len(Q.receipt.fingerprint)==64
 return False
class TestAL177(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL177,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
