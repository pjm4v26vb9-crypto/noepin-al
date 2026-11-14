import unittest
from dataclasses import replace
import noepin_al_174_intent_contract_artifact as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('source_contract_mutated','consent_executed','policy_decision_executed','permit_issued','permission_granted','tool_invoked','action_executed','action_success','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','approval_executed','authority_granted','stop_executed','world_truth_proven','domain_authority_promoted','safety_proven')
def prep(st,t='2026-11-13T10:00:00+00:00'):
 return m.evaluate_prepared(st,integrity_validated=True,current_contract_fingerprint=st.contract_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=t)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.contract_fingerprint_valid and r.action_allowed and not r.action_explicitly_denied and r.target_in_scope and r.time_active and r.consent_id_present and r.next_gate_candidate
 if k==1:
  r=m.evaluate(replace(q,action='delete')); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.ACTION_EXPLICITLY_DENIED
 if k==2:
  r=m.evaluate(replace(q,action='rename')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.ACTION_NOT_ALLOWED
 if k==3:
  r=m.evaluate(replace(q,target='asset:other')); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.TARGET_OUT_OF_SCOPE
 if k==4:
  r=m.evaluate(replace(q,at_time='2026-11-13T12:00:01+00:00')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONTRACT_EXPIRED
 if k==5:
  r=m.evaluate(replace(q,at_time='2026-11-13T08:59:59+00:00')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONTRACT_NOT_YET_ACTIVE
 if k==6:
  bad=replace(q.contract,fingerprint='0'*64); r=m.evaluate(replace(q,contract=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CONTRACT_FINGERPRINT_MISMATCH
 if k==7:
  try: m.build_contract(user_goal='x',allowed_actions=('read',),denied_actions=(' READ ',),scope_targets=('t',),consent_id='c',created_time='2026-11-13T09:00:00+00:00',expiry_time='2026-11-13T10:00:00+00:00'); return False
  except ValueError: return True
 if k==8:
  try: m.build_contract(user_goal='x',allowed_actions=('read',),denied_actions=(),scope_targets=(),consent_id='c',created_time='2026-11-13T09:00:00+00:00',expiry_time='2026-11-13T10:00:00+00:00'); return False
  except ValueError: return True
 if k==9:
  try: m.build_contract(user_goal='x',allowed_actions=('read',),denied_actions=(),scope_targets=('t',),consent_id='c',created_time='2026-11-13T10:00:00+00:00',expiry_time='2026-11-13T09:00:00+00:00'); return False
  except ValueError: return True
 if k==10:
  try: m.build_contract(user_goal='x',allowed_actions=('read',),denied_actions=(),scope_targets=('t',),consent_id='c',created_time='2026-11-13T09:00:00',expiry_time='2026-11-13T10:00:00+00:00'); return False
  except ValueError: return True
 if k==11:
  c=m.build_contract(user_goal='  A   goal ',allowed_actions=('Analyze',' analyze ','READ'),denied_actions=('Delete','delete'),scope_targets=(' asset:bundle-A ','asset:bundle-A'),consent_id=' C ',created_time='2026-11-13T18:00:00+09:00',expiry_time='2026-11-13T21:00:00+09:00'); return c.allowed_actions==('analyze','read') and c.denied_actions==('delete',) and c.scope_targets==('asset:bundle-A',) and c.created_time=='2026-11-13T09:00:00+00:00'
 if k==12:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_contract_fingerprint=st.contract_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint,current_time=q.at_time); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); c=replace(q.contract,user_goal='Changed goal'); c=replace(c,fingerprint=m._fp(m._contract_payload(c.schema,c.user_goal,c.allowed_actions,c.denied_actions,c.scope_targets,c.consent_id,c.created_time,c.expiry_time))); st2=m.prepare_state(replace(q,contract=c),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('INTENT_CONTRACT',)
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,target='asset:profile-A'),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('AUTHORIZATION_QUERY',)
 if k==16:
  r=m.default_evaluation(); return not any(getattr(r,n) for n in NEG)
 if k==17:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and len(q.contract.fingerprint)==64
 if k==18:
  r=m.evaluate(replace(q,request_id='')); return r.engine_state==m.EngineState.INVALID and not r.next_gate_candidate
 if k==19:
  st=m.prepare_state(q,B,E); r=prep(st,'2026-11-13T12:00:01+00:00'); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONTRACT_EXPIRED
 return False
class TestAL174(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL174,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
