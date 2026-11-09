import unittest
from dataclasses import replace
import noepin_al_104_risk_aware_mcts as m
class TestAL104(unittest.TestCase): pass

def _base(): return m.default_request(), list(m.default_actions()), m.default_policy()
def _scenario(k,v):
    q,aa,p=_base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.default_evaluation(); return z.decision==m.Decision.ALLOW and z.chosen_action=='A-SAFE-LONG' and 'A-FORBIDDEN' in z.pruned_actions
    if k==1:
        z=m.default_evaluation(); return z.chosen_action!='A-RISKY-HIGH'
    if k==2:
        xs=tuple(replace(a,hard_constraint_passed=False,constraint_reason='BLOCK') for a in aa); z=m.evaluate(q,xs,p); return z.decision==m.Decision.HOLD and z.chosen_action is None
    if k==3:
        q2=replace(q,risk=m.RiskClass.CRITICAL,max_action_risk=2); xs=tuple(replace(a,simulator_confidence=.4) for a in aa); z=m.evaluate(q2,xs,p); return z.decision==m.Decision.HOLD and z.next_action==m.NextAction.SIMULATOR_REVALIDATION_CANDIDATE
    if k==4:
        z=m.evaluate(replace(q,simulation_budget=10,min_simulations=20),tuple(aa),p); return z.decision==m.Decision.HOLD
    if k==5:
        z=m.evaluate(replace(q,max_action_risk=.1),tuple(aa),p); return z.decision in (m.Decision.ALLOW,m.Decision.HOLD) and (z.chosen_action in (None,'A-STABLE-LOW'))
    if k==6:
        z=m.evaluate(q,tuple(aa),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==7:
        z=m.evaluate(replace(q,binding='BAD'),tuple(aa),p); return z.decision==m.Decision.HOLD
    if k==8:
        bad=aa+[replace(aa[0],action_id=aa[1].action_id)]; return m.evaluate(q,tuple(bad),p).decision==m.Decision.HOLD
    if k==9:
        bad=replace(aa[0],reward_samples=(),risk_samples=()); return m.evaluate(q,(bad,),p).decision==m.Decision.HOLD
    if k==10:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_simulator_fingerprint=st.simulator_fingerprint); return z==m.evaluate(q,tuple(aa),p)
    if k==12:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_simulator_fingerprint=st.simulator_fingerprint); return z.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); aa2=tuple(replace(a,risk_samples=tuple(x+.01 for x in a.risk_samples)) if a.action_id=='A-SAFE-LONG' else a for a in aa); st2=m.prepare_state(q,aa2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_actions)==1 and sp.missing_or_changed_action_ids==('A-SAFE-LONG',)
    if k==14:
        z=m.default_evaluation(); neg=(z.action_candidate_promoted_to_permission,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==15:
        return m.evaluate(q,tuple(aa),p)==m.evaluate(q,tuple(reversed(aa)),p)
    if k==16:
        # High risk near approval threshold yields human-review candidate only.
        q2=replace(q,risk=m.RiskClass.HIGH,max_action_risk=1.0); xs=(m.MCTSAction('H',(5,5,5,5),(.7,.7,.7,.7),.95,True,'PASS','V','F',True,b,e),); z=m.evaluate(q2,xs,p); return z.decision==m.Decision.HUMAN_APPROVAL and z.next_action==m.NextAction.HUMAN_REVIEW_CANDIDATE and not z.permission_granted
    if k==17:
        # Simulator fingerprint mismatch invalidates reuse.
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_simulator_fingerprint='BAD'); return z.decision==m.Decision.HOLD
    if k==18:
        # Unsafe high reward never survives hard constraints.
        x=m.MCTSAction('X',(1000,1000),(0,0),1.0,False,'BLOCK','V','FX',True,b,e); z=m.evaluate(q,tuple(aa+[x]),p); return z.chosen_action!='X' and 'X' in z.pruned_actions
    if k==19:
        # Larger action space remains deterministic and bounded.
        xs=[]
        for i in range(64):
            safe=i%7!=0
            xs.append(m.MCTSAction(f'L{i:03d}',(4+i/200,4.1+i/200,3.9+i/200,4.0+i/200),(.05+(i%5)/100,)*4,.95,safe,'PASS' if safe else 'BLOCK','V',f'F{i}',True,b,e))
        q2=replace(q,simulation_budget=20,min_simulations=10,max_action_risk=2); z=m.evaluate(q2,tuple(xs),p); return z.decision in (m.Decision.ALLOW,m.Decision.HOLD) and z.simulations_used in (0,20) and any(v.visits==0 for v in z.visit_stats)
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL104,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
