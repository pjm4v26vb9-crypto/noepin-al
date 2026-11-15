import unittest
from dataclasses import replace
from datetime import timedelta
import noepin_al_181_human_approval_challenge_response_protocol as m

NEG=('human_approval_executed','approval_executed','permission_granted','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_nonce_reused','cached_approval_response_reused','dcsr_substituted_human_approval','dcsr_created_approval_response','dcsr_changed_action_digest','dcsr_changed_risk_digest','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')

def scenario(k,v):
 c=m.default_challenge(); q=m.default_verification_request(); r=q.response
 if k==0:
  x=m.evaluate_response(q); return x.decision==m.Decision.ALLOW and x.approval_response_verified and x.human_approval_evidence_verified and x.next_gate_candidate and not any(getattr(x,n) for n in NEG)
 if k==1:
  x=m.evaluate_response(m.default_verification_request('REJECT')); return x.decision==m.Decision.DENY and x.rejection_response_verified and x.human_rejection_evidence_verified and not x.next_gate_candidate
 if k==2:
  rr=replace(r,nonce='WRONG'); x=m.evaluate_response(replace(q,response=rr)); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.WRONG_NONCE and not x.approval_response_verified
 if k==3:
  rr=replace(r,challenge_fingerprint='c'*64); x=m.evaluate_response(replace(q,response=rr)); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.WRONG_CHALLENGE_FINGERPRINT
 if k==4:
  x=m.evaluate_response(replace(q,current_time=c.expires_at+timedelta(seconds=1))); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.EXPIRED
 if k==5:
  rr=replace(r,responded_at=c.expires_at+timedelta(seconds=1)); x=m.evaluate_response(replace(q,response=rr)); return x.escalation==m.Escalation.EXPIRED
 if k==6:
  x=m.evaluate_response(replace(q,current_action_digest='c'*64)); return x.escalation==m.Escalation.ACTION_DIGEST_MISMATCH and not x.approval_response_verified
 if k==7:
  x=m.evaluate_response(replace(q,current_risk_digest='d'*64)); return x.escalation==m.Escalation.RISK_DIGEST_MISMATCH
 if k==8:
  try: m.build_response('MAYBE',c.challenge_fingerprint,c.nonce,r.responded_at,'H'); return False
  except ValueError: return True
 if k==9:
  try: m.build_challenge('R','x'*64,'b'*64,'scope','n',c.issued_at,c.expires_at); return False
  except ValueError: return True
 if k==10:
  try: m.build_challenge('R','a'*64,'b'*64,'scope','n',c.issued_at,c.issued_at); return False
  except ValueError: return True
 if k==11:
  try: m.build_challenge('R','a'*64,'b'*64,'scope','n',c.issued_at.replace(tzinfo=None),c.expires_at); return False
  except ValueError: return True
 if k==12:
  cc=replace(c,scope_summary='changed'); x=m.evaluate_response(replace(q,challenge=cc)); return x.decision==m.Decision.DENY and x.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=True,current_challenge_state_fingerprint=st.challenge_state_fingerprint,current_response_fingerprint=st.response_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_action_digest=c.action_digest,current_risk_digest=c.risk_digest,current_nonce=c.nonce,current_time=q.current_time); return x==m.evaluate_response(q) and x.approval_response_verified
 if k==14:
  st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=False,current_challenge_state_fingerprint=st.challenge_state_fingerprint,current_response_fingerprint=st.response_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_action_digest=c.action_digest,current_risk_digest=c.risk_digest,current_nonce=c.nonce,current_time=q.current_time); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==15:
  st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=True,current_challenge_state_fingerprint=st.challenge_state_fingerprint,current_response_fingerprint=st.response_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_action_digest=c.action_digest,current_risk_digest=c.risk_digest,current_nonce='NEW-NONCE',current_time=q.current_time); return x.decision==m.Decision.HOLD and not x.approval_response_verified and not x.cached_nonce_reused
 if k==16:
  p=m.plan_missing_only(None,r); return p.missing_or_changed_record_ids==('APPROVAL_RESPONSE',) and not p.full_resend_required and p.metadata_bytes_required>0
 if k==17:
  d=m.make_delta(None,r); return d.response_record_added and d.from_fingerprint!=d.to_fingerprint
 if k==18:
  x=m.default_evaluation(); return x.challenge_fingerprint==c.challenge_fingerprint and x.human_decision==m.HumanDecision.APPROVE and x.within_validity_window
 if k==19:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and not a.dcsr_substituted_human_approval and not a.cached_approval_response_reused
 return False

class TestAL181(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL181,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
