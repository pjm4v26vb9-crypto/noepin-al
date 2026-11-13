import unittest
from dataclasses import replace
import noepin_al_153_safe_contextual_bandit_selector as m
B='DEFAULT-BINDING'; E='EPOCH-1'
def q0():return m.default_request()
def neg(r):return [r.arm_executed,r.routing_executed,r.exploration_executed,r.unsafe_arm_explored,r.reward_history_mutated,r.model_updated,r.online_learning_committed,r.safety_constraints_modified,r.policy_modified,r.canary_deployed,r.shadow_promoted_to_production,r.rollback_executed,r.fallback_executed,r.tool_invoked,r.file_write_executed,r.network_send_executed,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success]
def prep(st):return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_arms_fingerprint=st.arms_fingerprint,current_history_fingerprint=st.history_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,j):
 q=q0()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.selected_arm_id=='ARM-LOW-TRUST' and r.engine_state==m.EngineState.SAFE_ARM_SELECTED_CANDIDATE and r.exploration_probability<q.safety.max_exploration_probability and r.next_gate_candidate and not any(neg(r))
 if k==1:
  r=m.evaluate(q); bad=[x for x in r.safety_filter_trace if x.arm_id=='ARM-UNSAFE-HIGH'][0]; return not bad.included and bad.reason=='HARD_SAFETY_FILTER_REJECT' and r.selected_arm_id!='ARM-UNSAFE-HIGH'
 if k==2:
  arms=tuple(replace(a,hard_safe=False) for a in q.arms); r=m.evaluate(replace(q,arms=arms)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NO_SAFE_ARM and r.selected_arm_id is None and r.exploration_probability==0 and not r.unsafe_arm_explored
 if k==3:
  a=m.CandidateArm('ARM-NEW',(0.9,0.1,0.1),0.55,True,0.9,True,B,E); r=m.evaluate(replace(q,arms=q.arms+(a,))); tr=[x for x in r.safety_filter_trace if x.arm_id=='ARM-NEW'][0]; return tr.observation_count==0 and tr.included
 if k==4:
  ctx=replace(q.context,critical=True); r=m.evaluate(replace(q,context=ctx)); return r.exploration_probability<=q.safety.critical_max_exploration_probability and 'CRITICAL_EXPLORATION_REDUCED' in r.reasons
 if k==5:
  arms=tuple(replace(a,trust_score=.4) if a.arm_id=='ARM-SAFE-A' else a for a in q.arms); r=m.evaluate(replace(q,arms=arms)); return r.exploration_probability<q.safety.max_exploration_probability and 'TRUST_LIMIT_APPLIED' in r.reasons
 if k==6:
  s=replace(q.safety,policy_verified=False); r=m.evaluate(replace(q,safety=s)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.POLICY_UNVERIFIED and not r.next_gate_candidate
 if k==7:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SAFETY_REGRESSION and r.fallback_arm_id=='ARM-SAFE-A' and not r.fallback_executed
 if k==8:
  bad=replace(q.context,binding='BAD'); return m.evaluate(replace(q,context=bad)).engine_state==m.EngineState.INVALID
 if k==9:
  a=replace(q.arms[0],feature_weights=(1.0,)); return m.evaluate(replace(q,arms=(a,)+q.arms[1:])).engine_state==m.EngineState.INVALID
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_arms_fingerprint=st.arms_fingerprint,current_history_fingerprint=st.history_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='shadow-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
 if k==13:
  a=m.prepare_state(q,B,E); h=q.reward_history+(m.RewardRecord('RX','ARM-SAFE-B',.9,True,B,E),); b=m.prepare_state(replace(q,reward_history=h),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('REWARD_HISTORY',)
 if k==14:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_SELECTION_CANDIDATE and r.escalation==m.Escalation.NONE and r.next_gate_candidate and not any(neg(r))
 if k==15:
  r=m.evaluate(q); return set(r.eligible_update_arm_ids)=={'ARM-SAFE-A','ARM-SAFE-B','ARM-LOW-TRUST'} and 'ARM-UNSAFE-HIGH' not in r.eligible_update_arm_ids
 if k==16:
  s=replace(q.safety,min_trust_for_selection=.5); r=m.evaluate(replace(q,safety=s)); low=[x for x in r.safety_filter_trace if x.arm_id=='ARM-LOW-TRUST'][0]; return not low.included and low.reason=='TRUST_BELOW_SELECTION_MINIMUM'
 if k==17:
  r=m.evaluate(q); return 'SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY' in r.reasons and not r.shadow_promoted_to_production
 if k==18:
  r=m.evaluate(q); return 0<=r.exploration_probability<=q.safety.max_exploration_probability and not r.exploration_executed
 if k==19:
  r=m.evaluate(q); return all(not x.included for x in r.safety_filter_trace if not [a for a in q.arms if a.arm_id==x.arm_id][0].hard_safe) and not any(neg(r))
 return False
class TestAL153(unittest.TestCase):pass
def mk(i):
 def t(self):self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160):setattr(TestAL153,f'test_case_{i:03d}',mk(i))
if __name__=='__main__':unittest.main(verbosity=2)
