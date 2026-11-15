import unittest
from dataclasses import replace
import noepin_al_179_decision_execution_handshake_protocol as m
NEG=('artifact_binding_promoted_to_truth','artifact_final_verified_promoted_to_truth','decision_binding_promoted_to_decision_execution','permit_binding_promoted_to_permit_issuance','execution_state_promoted_to_action_execution','receipt_binding_promoted_to_action_success','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_reconstruction_advanced','dcsr_changed_transition_order','dcsr_created_artifact_binding','dcsr_promoted_unverified_artifact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def bind(s,k,final=True): return m.bind_artifact(s,k,m._seed('T-'+k.value),final_verified=final)
def scenario(k,cycle):
 if k==0:
  s=m.build_session('REQ-X'); return s.current_state==m.HandshakeState.REQUESTED and not s.bound_artifacts and not s.history
 if k==1:
  s=bind(m.build_session('REQ-X'),m.ArtifactKind.INTENT); ns,r=m.apply_transition(m.make_transition_request(s,m.HandshakeState.INTENT_BOUND)); return r.decision==m.Decision.ALLOW and r.transitioned and ns.current_state==m.HandshakeState.INTENT_BOUND
 if k==2:
  s=m.build_session('REQ-X'); r=m.evaluate_transition(m.make_transition_request(s,m.HandshakeState.POLICY_BOUND)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.INVALID_STATE_TRANSITION and not r.transitioned
 if k==3:
  s=m.build_session('REQ-X'); r=m.evaluate_transition(m.make_transition_request(s,m.HandshakeState.INTENT_BOUND)); return r.decision==m.Decision.HOLD and r.missing_artifacts==('INTENT',)
 if k==4:
  s=bind(m.build_session('REQ-X'),m.ArtifactKind.INTENT,False); r=m.evaluate_transition(m.make_transition_request(s,m.HandshakeState.INTENT_BOUND)); return r.decision==m.Decision.HOLD and r.unverified_artifacts==('INTENT',) and not r.required_artifacts_final_verified
 if k==5:
  try: m.bind_artifact(m.build_session('REQ-X'),m.ArtifactKind.INTENT,'bad',final_verified=True); return False
  except ValueError: return True
 if k==6:
  try: m.bind_artifact(m.build_session('REQ-X'),'UNKNOWN',m._seed('x'),final_verified=True); return False
  except ValueError: return True
 if k==7:
  s=m.build_session('REQ-X'); ns,r=m.apply_transition(m.make_transition_request(s,m.HandshakeState.HOLD)); return r.decision==m.Decision.HOLD and ns.current_state==m.HandshakeState.HOLD
 if k==8:
  s=m.build_session('REQ-X'); s,_=m.apply_transition(m.make_transition_request(s,m.HandshakeState.HOLD)); r=m.evaluate_transition(m.make_transition_request(s,m.HandshakeState.INTENT_BOUND)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.HOLD_LOCKED and not r.transitioned
 if k==9:
  s=m.build_session('REQ-X'); s,_=m.apply_transition(m.make_transition_request(s,m.HandshakeState.HOLD)); ns,r=m.apply_transition(m.make_transition_request(s,m.HandshakeState.ABORTED)); return r.decision==m.Decision.ALLOW and ns.current_state==m.HandshakeState.ABORTED
 if k==10:
  try: m.build_session('   '); return False
  except ValueError: return True
 if k==11:
  s=m.default_bound_session(); end,rs=m.run_full_handshake(s); return end.current_state==m.HandshakeState.RECEIPT_VERIFIED and len(rs)==7 and all(r.transitioned for r in rs)
 if k==12:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.requested_state==m.HandshakeState.RECEIPT_VERIFIED and r.next_action==m.NextAction.CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE and r.next_gate_candidate
 if k==13:
  s=m.default_session_before_receipt(); bad=replace(s,session_fingerprint='0'*64); r=m.evaluate_transition(m.make_transition_request(bad,m.HandshakeState.RECEIPT_VERIFIED)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SESSION_FINGERPRINT_MISMATCH
 if k==14:
  q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_session_fingerprint=st.session_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return r==st.result
 if k==15:
  q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_session_fingerprint=st.session_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID and not r.transitioned
 if k==16:
  full=m.default_bound_session(); partial=m.build_session(full.request_id)
  for b in full.bound_artifacts:
   if b.kind!=m.ArtifactKind.RECEIPT: partial=m.bind_artifact(partial,b.kind,b.fingerprint,final_verified=b.final_verified)
  p=m.plan_missing_only(partial,full); return p.missing_or_changed_record_ids==('BINDING:RECEIPT',) and not p.full_resend_required
 if k==17:
  s=m.default_session_before_receipt(); end,_=m.apply_transition(m.default_request()); p=m.plan_missing_only(s,end); return p.missing_or_changed_record_ids==('TRANSITION:7:RECEIPT_VERIFIED',)
 if k==18:
  s=m.build_session('REQ-X'); s=m.bind_artifact(s,m.ArtifactKind.INTENT,m._seed('A'),final_verified=False); s2=m.bind_artifact(s,m.ArtifactKind.INTENT,m._seed('A'),final_verified=True); return not dict((b.kind,b.final_verified) for b in s.bound_artifacts)[m.ArtifactKind.INTENT] and dict((b.kind,b.final_verified) for b in s2.bound_artifacts)[m.ArtifactKind.INTENT]
 if k==19:
  r=m.default_evaluation(); a=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r==a and m._canon(r)==m._canon(a) and len(r.session_fingerprint)==64
 return False
class TestAL179(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL179,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
