import unittest
from dataclasses import replace
import noepin_al_176_evidence_bundle_artifact as m
Q=m.default_request(); B=Q.binding; E=Q.state_epoch
NEG=('evidence_promoted_to_truth','source_promoted_to_authority','provenance_promoted_to_truth','trust_promoted_to_truth','independence_promoted_to_truth','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.bundle_fingerprint_valid and r.stale_ids==() and r.future_ids==() and len(r.fresh_ids)==4 and r.independent_group_count==3
 if k==1:
  old=Q.bundle.items[0]; b=m.build_bundle((replace(old,observed_time='2026-11-13T10:00:00+00:00'),)+Q.bundle.items[1:]); r=m.evaluate(replace(Q,bundle=b)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.STALE_EVIDENCE_PRESENT and 'EV-176-001' in r.stale_ids
 if k==2:
  old=Q.bundle.items[0]; b=m.build_bundle((replace(old,observed_time='2026-11-13T12:01:00+00:00'),)+Q.bundle.items[1:]); r=m.evaluate(replace(Q,bundle=b)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.FUTURE_EVIDENCE_PRESENT and 'EV-176-001' in r.future_ids and 'EV-176-001' in r.stale_ids
 if k==3:
  bad=replace(Q.bundle,fingerprint='0'*64); r=m.evaluate(replace(Q,bundle=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.BUNDLE_FINGERPRINT_MISMATCH
 if k==4:
  try: m.build_bundle(()); return False
  except ValueError: return True
 if k==5:
  try: m.build_bundle((Q.bundle.items[0],Q.bundle.items[0])); return False
  except ValueError: return True
 if k==6:
  try: m.build_bundle((replace(Q.bundle.items[0],trust=-0.01),)); return False
  except ValueError: return True
 if k==7:
  try: m.build_bundle((replace(Q.bundle.items[0],trust=1.01),)); return False
  except ValueError: return True
 if k==8:
  try: m.build_bundle((replace(Q.bundle.items[0],provenance_digest='Z'*64),)); return False
  except ValueError: return True
 if k==9:
  try: m.build_bundle((replace(Q.bundle.items[0],observed_time='2026-11-13T11:00:00'),)); return False
  except ValueError: return True
 if k==10:
  r=m.evaluate(replace(Q,max_age_seconds=-1)); return r.decision==m.Decision.HOLD and r.engine_state==m.EngineState.INVALID and r.escalation==m.Escalation.INVALID_CONFIGURATION
 if k==11:
  r=m.evaluate(replace(Q,at_time='2026-11-13T12:00:00')); return r.decision==m.Decision.HOLD and r.engine_state==m.EngineState.INVALID
 if k==12:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_bundle_fingerprint=st.bundle_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=Q.at_time); return r==st.result
 if k==13:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_bundle_fingerprint=st.bundle_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=Q.at_time); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(Q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_bundle_fingerprint=st.bundle_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time='2026-11-13T13:00:01+00:00'); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.STALE_EVIDENCE_PRESENT
 if k==15:
  st=m.prepare_state(Q,B,E); x=replace(Q.bundle.items[0],claim='Changed claim'); b=m.build_bundle((x,)+Q.bundle.items[1:]); st2=m.prepare_state(replace(Q,bundle=b),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('EVIDENCE:EV-176-001',) and not p.full_resend_required
 if k==16:
  st=m.prepare_state(Q,B,E); st2=m.prepare_state(replace(Q,max_age_seconds=1800.0),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('EVIDENCE_QUERY',)
 if k==17:
  b=m.build_bundle(Q.bundle.items[:3]+(replace(Q.bundle.items[3],independence_group='IND-X'),)); r=m.evaluate(replace(Q,bundle=b)); return r.independent_group_count==4
 if k==18:
  b=m.build_bundle(tuple(reversed(Q.bundle.items))); return b==Q.bundle and b.fingerprint==Q.bundle.fingerprint
 if k==19:
  r=m.default_evaluation(); a=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r==a and m._canon(r)==m._canon(a) and len(Q.bundle.fingerprint)==64
 return False
class TestAL176(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL176,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
