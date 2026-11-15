import unittest
from dataclasses import replace
import noepin_al_182_failure_state_propagation_protocol as m
NEG=('recovery_authorization_promoted_to_truth','recovery_authorization_promoted_to_permission','recovery_executed','state_downgrade_executed','permission_granted','permit_issued','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_downgraded_failure_state','dcsr_invented_recovery_authorization','dcsr_substituted_recovery_authorization','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')

def scenario(k,v):
 q=m.default_request()
 if k==0:
  x=m.evaluate(q); return x.decision==m.Decision.ALLOW and x.current_state==m.FailureState.HOLD and x.incoming_state==m.FailureState.DENY and x.effective_state==m.FailureState.DENY and x.escalated and x.next_gate_candidate and not any(getattr(x,n) for n in NEG)
 if k==1:
  x=m.evaluate(m.make_request('DENY','HOLD')); return x.effective_state==m.FailureState.DENY and x.lower_incoming_ignored and x.engine_state==m.EngineState.FAILURE_STATE_RETAINED_CANDIDATE
 if k==2:
  x=m.evaluate(m.make_request('DENY','OK','HOLD')); return x.decision==m.Decision.DENY and x.effective_state==m.FailureState.DENY and x.downgrade_requested and not x.downgrade_accepted and x.escalation==m.Escalation.DOWNGRADE_WITHOUT_RECOVERY_AUTHORIZATION
 if k==3:
  a=m.build_recovery_authorization('REC-1','DENY','HOLD','DEFAULT-BINDING','EPOCH-1'); x=m.evaluate(m.make_request('DENY','OK','HOLD',a)); return x.decision==m.Decision.ALLOW and x.effective_state==m.FailureState.HOLD and x.recovery_authorization_valid and x.downgrade_accepted and not x.recovery_executed
 if k==4:
  x=m.evaluate(m.make_request('OK','ABORT')); return x.effective_state==m.FailureState.ABORT and x.escalated
 if k==5:
  x=m.evaluate(m.make_request('HOLD','HUMAN_APPROVAL')); return x.effective_state==m.FailureState.HUMAN_APPROVAL and x.escalated
 if k==6:
  x=m.evaluate(m.make_request('HUMAN_APPROVAL','DENY')); return x.effective_state==m.FailureState.DENY
 if k==7:
  x=m.evaluate(m.make_request('HOLD','HOLD')); return x.effective_state==m.FailureState.HOLD and not x.escalated and not x.lower_incoming_ignored
 if k==8:
  try: m.make_request('UNKNOWN','HOLD'); return False
  except ValueError: return True
 if k==9:
  try: m.make_request('OK','UNKNOWN'); return False
  except ValueError: return True
 if k==10:
  try: m.make_request('OK','HOLD','UNKNOWN'); return False
  except ValueError: return True
 if k==11:
  try: m.build_recovery_authorization('REC','HOLD','DENY','B','E'); return False
  except ValueError: return True
 if k==12:
  a=m.build_recovery_authorization('REC','DENY','HOLD','OTHER','EPOCH-1'); x=m.evaluate(m.make_request('DENY','OK','HOLD',a)); return x.decision==m.Decision.DENY and not x.recovery_authorization_valid
 if k==13:
  a=m.build_recovery_authorization('REC','DENY','HOLD','DEFAULT-BINDING','EPOCH-1',False); x=m.evaluate(m.make_request('DENY','OK','HOLD',a)); return x.decision==m.Decision.DENY and not x.recovery_authorization_valid
 if k==14:
  x=m.evaluate(m.make_request('HOLD','OK','ABORT')); return x.effective_state==m.FailureState.ABORT and x.escalated and x.decision==m.Decision.ALLOW
 if k==15:
  st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_binding=q.binding,current_state_epoch=q.state_epoch,current_current_state=q.current_state,current_incoming_state=q.incoming_state,current_proposed_state=q.proposed_state,current_recovery_authorization=q.recovery_authorization); return x==m.evaluate(q)
 if k==16:
  st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=False,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_binding=q.binding,current_state_epoch=q.state_epoch,current_current_state=q.current_state,current_incoming_state=q.incoming_state,current_proposed_state=q.proposed_state,current_recovery_authorization=q.recovery_authorization); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==17:
  p=m.plan_missing_only('HOLD','DENY'); return p.missing_or_changed_record_ids==('FAILURE_STATE',) and p.metadata_bytes_required>0 and not p.full_resend_required
 if k==18:
  d=m.make_delta('HOLD','DENY'); return d.record_id=='FAILURE_STATE' and d.from_state==m.FailureState.HOLD and d.to_state==m.FailureState.DENY
 if k==19:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and a.severity_effective>=a.severity_before and not a.dcsr_downgraded_failure_state
 return False

class TestAL182(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL182,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
