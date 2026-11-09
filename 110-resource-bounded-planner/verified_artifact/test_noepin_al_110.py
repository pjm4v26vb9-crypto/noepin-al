import unittest
from dataclasses import replace
import noepin_al_110_resource_bounded_planner as m

class TestAL110(unittest.TestCase): pass

def base(): return m.default_request(), list(m.default_actions()), list(m.default_limits()), m.default_policy()

def run_prepared(st,ok=True,**changes):
    args=dict(integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_budget_fingerprint=st.budget_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint); args.update(changes); return m.evaluate_prepared(st,**args)

def scenario(k,variant):
    q,a,l,p=base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.evaluate(q,tuple(a),tuple(l),p); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.FEASIBLE_PLAN_CANDIDATE and z.budget_feasible and z.reserve_satisfied and z.mandatory_safety_preserved and z.next_gate_candidate and z.plan==('PREPARE','SAFETY-VERIFY','BUILD','FINAL-CHECK')
    if k==1:
        ll=[replace(x,hard_limit=1000,reserve_required=0) if x.resource=='tokens' else x for x in l]; z=m.evaluate(q,tuple(a),tuple(ll),p); return z.decision==m.Decision.HUMAN_APPROVAL and not z.budget_feasible and any(s.resource=='tokens' for s in z.shortfall) and not z.budget_granted
    if k==2:
        qq=replace(q,additional_budget_candidate_allowed=False); ll=[replace(x,hard_limit=1000,reserve_required=0) if x.resource=='tokens' else x for x in l]; z=m.evaluate(qq,tuple(a),tuple(ll),p); return z.decision==m.Decision.HOLD and not z.budget_granted
    if k==3:
        ll=[replace(x,hard_limit=1800,reserve_required=200) if x.resource=='tokens' else x for x in l]; z=m.evaluate(q,tuple(a),tuple(ll),p); return z.decision==m.Decision.HUMAN_APPROVAL and z.budget_feasible and not z.reserve_satisfied and any(s.basis=='RESERVE' for s in z.shortfall)
    if k==4:
        z=m.default_evaluation(); fm={x.resource:x for x in z.resource_forecast}; return fm['tokens'].used==1750 and fm['api_calls'].used==5 and fm['tool_calls'].used==6
    if k==5:
        # exact hard boundary and reserve disabled
        pp=replace(p,require_reserve=False); ll=[replace(x,hard_limit=1750,reserve_required=0) if x.resource=='tokens' else x for x in l]; z=m.evaluate(q,tuple(a),tuple(ll),pp); return z.decision==m.Decision.ALLOW and z.budget_feasible
    if k==6:
        aa=[replace(x,policy_allowed=False) if x.action_id=='BUILD' else x for x in a]; z=m.evaluate(q,tuple(aa),tuple(l),p); return z.decision==m.Decision.HOLD and 'NO_ELIGIBLE_ROUTE' in z.reasons
    if k==7:
        aa=[replace(x,hard_constraint_passed=False) if x.action_id=='BUILD' else x for x in a]; z=m.evaluate(q,tuple(aa),tuple(l),p); return z.decision==m.Decision.HOLD and 'NO_ELIGIBLE_ROUTE' in z.reasons
    if k==8:
        aa=[replace(x,risk=1.5) if x.action_id=='BUILD' else x for x in a]; z=m.evaluate(q,tuple(aa),tuple(l),p); return z.decision==m.Decision.HOLD and 'NO_ELIGIBLE_ROUTE' in z.reasons
    if k==9:
        # direct route cannot bypass mandatory safety action
        aa=[x for x in a if x.action_id!='BUILD']; z=m.evaluate(q,tuple(aa),tuple(l),p); return z.decision==m.Decision.HOLD and 'NO_ELIGIBLE_ROUTE' in z.reasons
    if k==10:
        bad=tuple(l)+(l[0],); z=m.evaluate(q,tuple(a),bad,p); return z.decision==m.Decision.HOLD and 'RESOURCE_LIMIT_INVALID' in z.reasons
    if k==11:
        st=m.prepare_state(q,tuple(a),tuple(l),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,tuple(a),tuple(l),p,binding=b,state_epoch=e); return run_prepared(st)==st.precomputed_result
    if k==13:
        st=m.prepare_state(q,tuple(a),tuple(l),p,binding=b,state_epoch=e); return run_prepared(st,False).decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,tuple(a),tuple(l),p,binding=b,state_epoch=e); a2=tuple(replace(x,resource_cost=m._rc(tokens=950,api_calls=2,cpu_seconds=2.0,memory_mb=160,money_usd=.18,tool_calls=3),action_fingerprint='FP-BUILD2') if x.action_id=='BUILD' else x for x in a); st2=m.prepare_state(q,a2,tuple(l),p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_actions)==1 and d.changed_actions[0].action_id=='BUILD' and sp.missing_or_changed_record_ids==('ACTION:BUILD',)
    if k==15:
        z=m.default_evaluation(); neg=(z.plan_promoted_to_permission,z.permission_granted,z.budget_granted,z.credential_granted,z.authority_granted,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==16:
        return m.evaluate(q,tuple(a),tuple(l),p)==m.evaluate(q,tuple(reversed(a)),tuple(reversed(l)),p)
    if k==17:
        ll=[replace(x,hard_limit=1000,reserve_required=0) if x.resource=='tokens' else x for x in l]; z=m.evaluate(q,tuple(a),tuple(ll),p); return z.decision==m.Decision.HUMAN_APPROVAL and not z.permission_granted and not z.budget_granted and not z.action_executed
    if k==18:
        st=m.prepare_state(q,tuple(a),tuple(l),p,binding=b,state_epoch=e); z=run_prepared(st,current_budget_fingerprint='BAD'); return z.decision==m.Decision.HOLD and 'PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED' in z.reasons
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL110,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
