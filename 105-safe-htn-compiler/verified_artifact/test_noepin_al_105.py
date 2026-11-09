import unittest
from dataclasses import replace
import noepin_al_105_safe_htn_compiler as m
class TestAL105(unittest.TestCase): pass

def _base(): return m.default_request(),m.default_state(),list(m.default_methods()),list(m.default_leaves()),m.default_policy()
def _scenario(k,v):
    q,s,mm,ll,p=_base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.default_evaluation(); return z.decision==m.Decision.ALLOW and tuple(x.task_id for x in z.hierarchical_plan)==('INSPECT','PATCH','VERIFY') and 'M-SAFE' in z.method_trace
    if k==1:
        z=m.default_evaluation(); return any(x[0]=='M-UNSAFE' for x in z.rejected_methods) and all(x.task_id!='DELETE_ALL' for x in z.hierarchical_plan)
    if k==2:
        xs=tuple(replace(x,hard_constraint_passed=False) for x in mm); z=m.evaluate(q,s,xs,tuple(ll),p); return z.decision==m.Decision.HOLD and not z.hierarchical_plan
    if k==3:
        s2=replace(s,authority_tier=1); z=m.evaluate(q,s2,tuple(mm),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==4:
        z=m.evaluate(replace(q,goal_task='UNKNOWN'),s,tuple(mm),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==5:
        bad=replace(ll[1],policy_verified=False); z=m.evaluate(q,s,tuple(mm),tuple([ll[0],bad,ll[2],ll[3]]),p); return z.decision==m.Decision.HOLD
    if k==6:
        s2=replace(s,capabilities=('read','test')); z=m.evaluate(q,s2,tuple(mm),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==7:
        # A genuinely nested decomposition beyond max_depth must HOLD.
        outer=m.HTNMethod('M-OUT','PROJECT_FIX',('INNER',),('repo_loaded',),1,.01,True,20,'V1','OUT',True,b,e)
        inner=m.HTNMethod('M-IN','INNER',('INSPECT',),('repo_loaded',),1,.01,True,20,'V1','IN',True,b,e)
        z=m.evaluate(replace(q,max_depth=1),s,(outer,inner),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==8:
        z=m.evaluate(replace(q,max_leaf_tasks=2),s,tuple(mm),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(q,s,tuple(mm),tuple(ll),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==10:
        st=m.prepare_state(q,s,tuple(mm),tuple(ll),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,s,tuple(mm),tuple(ll),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_decomposition_fingerprint=st.decomposition_fingerprint); return z==m.evaluate(q,s,tuple(mm),tuple(ll),p)
    if k==12:
        st=m.prepare_state(q,s,tuple(mm),tuple(ll),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_decomposition_fingerprint=st.decomposition_fingerprint); return z.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,s,tuple(mm),tuple(ll),p,binding=b,state_epoch=e); ll2=tuple(replace(x,cost=x.cost+.1) if x.task_id=='PATCH' else x for x in ll); st2=m.prepare_state(q,s,tuple(mm),ll2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_leaves)==1 and sp.missing_or_changed_record_ids==('LEAF:PATCH',)
    if k==14:
        z=m.default_evaluation(); neg=(z.plan_promoted_to_permission,z.permission_granted,z.authority_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==15:
        return m.evaluate(q,s,tuple(mm),tuple(ll),p)==m.evaluate(q,s,tuple(reversed(mm)),tuple(reversed(ll)),p)
    if k==16:
        # Multiple safe methods: lower total risk wins even if priority lower.
        alt=m.HTNMethod('M-ALT','PROJECT_FIX',('INSPECT','VERIFY'),('repo_loaded',),1,.05,True,1,'V1','ALT',True,b,e); z=m.evaluate(q,s,tuple(mm+[alt]),tuple(ll),p); return z.decision==m.Decision.ALLOW and z.method_trace[0]=='M-ALT'
    if k==17:
        # Cycle remains HOLD.
        cyc=m.HTNMethod('M-CYC','PROJECT_FIX',('LOOP',),('repo_loaded',),1,.01,True,20,'V1','C1',True,b,e); cyc2=m.HTNMethod('M-CYC2','LOOP',('PROJECT_FIX',),('repo_loaded',),1,.01,True,20,'V1','C2',True,b,e); z=m.evaluate(q,s,tuple([cyc,cyc2]),tuple(ll),p); return z.decision==m.Decision.HOLD
    if k==18:
        # Critical/high-risk plan yields review candidate only.
        q2=replace(q,risk=m.RiskClass.HIGH); p2=replace(p,high_risk_cap=2.0,max_authority_high=2,approval_risk_threshold=.2); z=m.evaluate(q2,s,tuple(mm),tuple(ll),p2); return z.decision==m.Decision.HUMAN_APPROVAL and not z.permission_granted
    if k==19:
        # Fingerprint mismatch invalidates reuse.
        st=m.prepare_state(q,s,tuple(mm),tuple(ll),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',current_frontier_fingerprint=st.frontier_fingerprint,current_decomposition_fingerprint=st.decomposition_fingerprint); return z.decision==m.Decision.HOLD
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL105,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
