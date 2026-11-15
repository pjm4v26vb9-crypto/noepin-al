import unittest
from dataclasses import replace
import noepin_al_178_risk_envelope_artifact as m
Q=m.default_request(); B=Q.binding; E=Q.state_epoch
NEG=('risk_promoted_to_truth','risk_promoted_to_permission','risk_limit_promoted_to_permission','violation_promoted_to_stop_execution','critical_violation_promoted_to_denial_execution','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','stale_cached_risk_promoted_to_current','dcsr_changed_risk_value','dcsr_changed_risk_limit','dcsr_created_risk_truth','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def vals(e=None):
 e=e or Q.envelope; return dict(observed=dict(e.observed),limits=dict(e.limits),critical_dimensions=e.critical_dimensions,rationale=e.rationale,envelope_id=e.envelope_id)
def req_for(e): return replace(Q,envelope=e,current_observed=e.observed,current_limits=e.limits,current_critical_dimensions=e.critical_dimensions)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.dimension_count==7 and not r.violations and not r.critical_violations
 if k==1:
  x=vals(); x['observed']['availability']=0.70; e=m.build_envelope(**x); r=m.evaluate(req_for(e)); return r.decision==m.Decision.HOLD and r.violations==('availability',) and not r.critical_violations and r.escalation==m.Escalation.RISK_LIMIT_VIOLATION
 if k==2:
  x=vals(); x['observed']['privilege']=0.70; e=m.build_envelope(**x); r=m.evaluate(req_for(e)); return r.decision==m.Decision.HOLD and r.critical_violations==('privilege',) and r.escalation==m.Escalation.CRITICAL_RISK_VIOLATION and not r.critical_violation_promoted_to_denial_execution
 if k==3:
  x=vals(); del x['observed']['integrity']
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==4:
  x=vals(); x['observed']['other']=0.1
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==5:
  x=vals(); x['observed']['integrity']=1.1
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==6:
  x=vals(); x['limits']['integrity']=-0.1
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==7:
  x=vals(); x['critical_dimensions']=('unknown',)
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==8:
  x=vals(); x['rationale']='  '
  try: m.build_envelope(**x); return False
  except ValueError: return True
 if k==9:
  bad=replace(Q.envelope,fingerprint='0'*64); r=m.evaluate(replace(Q,envelope=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.ENVELOPE_FINGERPRINT_MISMATCH
 if k==10:
  obs=list(Q.current_observed); obs[0]=(obs[0][0],obs[0][1]+0.01); r=m.evaluate(replace(Q,current_observed=tuple(obs))); return r.decision==m.Decision.HOLD and not r.observed_match and r.escalation==m.Escalation.CONTEXT_OR_LIMIT_MISMATCH
 if k==11:
  lim=list(Q.current_limits); lim[0]=(lim[0][0],lim[0][1]+0.01); r=m.evaluate(replace(Q,current_limits=tuple(lim))); return r.decision==m.Decision.HOLD and not r.limits_match
 if k==12:
  r=m.evaluate(replace(Q,current_critical_dimensions=('privilege',))); return r.decision==m.Decision.HOLD and not r.critical_dimensions_match
 if k==13:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_envelope_fingerprint=st.envelope_fingerprint,current_context_fingerprint=st.context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r==st.result
 if k==14:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_envelope_fingerprint=st.envelope_fingerprint,current_context_fingerprint=st.context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==15:
  st=m.prepare_state(Q,B,E); x=vals(); x['observed']['uncertainty']=0.25; e=m.build_envelope(**x); st2=m.prepare_state(req_for(e),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('OBSERVED:uncertainty',) and not p.full_resend_required
 if k==16:
  st=m.prepare_state(Q,B,E); x=vals(); x['limits']['availability']=0.51; e=m.build_envelope(**x); st2=m.prepare_state(req_for(e),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('LIMIT:availability',)
 if k==17:
  st=m.prepare_state(Q,B,E); x=vals(); x['critical_dimensions']=('externality','privilege'); e=m.build_envelope(**x); st2=m.prepare_state(req_for(e),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('CRITICAL_DIMENSIONS',)
 if k==18:
  st=m.prepare_state(Q,B,E); q2=replace(Q,context_id='CTX-178-B'); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('RISK_CONTEXT',)
 if k==19:
  r=m.default_evaluation(); a=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r==a and m._canon(r)==m._canon(a) and len(Q.envelope.fingerprint)==64
 return False
class TestAL178(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL178,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
