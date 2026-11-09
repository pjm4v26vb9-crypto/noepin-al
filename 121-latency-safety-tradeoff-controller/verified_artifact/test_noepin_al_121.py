import unittest
from dataclasses import replace
import noepin_al_121_latency_safety_tradeoff_controller as m
class TestAL121(unittest.TestCase): pass
def scenario(k,j):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); return r.decision==m.Decision.ALLOW and set(r.mandatory_check_set)=={'IDENTITY','POLICY'} and r.expected_latency_ms<=q.latency_budget_ms and r.next_gate_candidate
    if k==1:
        q2=replace(q,risk_class=m.RiskClass.LOW,latency_budget_ms=.4); r=m.evaluate(q2); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.FAST_PATH_CHECK_SET_CANDIDATE and r.selected_check_set==('IDENTITY',)
    if k==2:
        q2=replace(q,risk_class=m.RiskClass.HIGH,latency_budget_ms=2.2); r=m.evaluate(q2); return r.decision==m.Decision.ALLOW and set(r.mandatory_check_set)=={'IDENTITY','POLICY','AUTHORITY'}
    if k==3:
        q2=replace(q,risk_class=m.RiskClass.CRITICAL,latency_budget_ms=2.0); r=m.evaluate(q2); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.LATENCY_BUDGET_INSUFFICIENT and not r.next_gate_candidate
    if k==4:
        cs=tuple(replace(c,available=False) if c.check_id=='POLICY' else c for c in q.checks); r=m.evaluate(replace(q,checks=cs)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MANDATORY_CHECK_UNAVAILABLE
    if k==5:
        cs=tuple(replace(c,timed_out=True) if c.check_id=='POLICY' else c for c in q.checks); r=m.evaluate(replace(q,checks=cs)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MANDATORY_CHECK_TIMEOUT
    if k==6:
        r=m.evaluate(replace(q,latency_budget_ms=10.0)); return r.decision==m.Decision.ALLOW and len(r.selected_check_set)==len(q.checks) and r.residual_risk<=m.evaluate(q).residual_risk
    if k==7: return m.evaluate(replace(q,latency_budget_ms=float('nan'))).decision==m.Decision.HOLD
    if k==8: return m.evaluate(replace(q,checks=q.checks+(q.checks[0],))).decision==m.Decision.HOLD
    if k==9:
        cs=(replace(q.checks[0],latency_ms=-1),)+q.checks[1:]; return m.evaluate(replace(q,checks=cs)).decision==m.Decision.HOLD
    if k==10:
        cs=(replace(q.checks[0],binding='BAD'),)+q.checks[1:]; return m.evaluate(replace(q,checks=cs)).decision==m.Decision.HOLD
    if k==11:
        r=m.default_evaluation(); neg=(r.selected_checks_promoted_to_permission,r.check_execution_performed,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_check_fingerprint=st.check_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint)==st.result
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_check_fingerprint=st.check_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint).decision==m.Decision.HOLD
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); cs=tuple(replace(c,latency_ms=c.latency_ms+.1) if c.check_id=='CONTEXT_DEEP' else c for c in q.checks); st2=m.prepare_state(replace(q,checks=cs),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_checks)==1 and d.changed_checks[0].check_id=='CONTEXT_DEEP'
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); cs=tuple(replace(c,safety_value=c.safety_value+.01) if c.check_id=='COUNTEREXAMPLE' else c for c in q.checks); st2=m.prepare_state(replace(q,checks=cs),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('CHECK:COUNTEREXAMPLE',) and not sp.full_resend_required
    if k==17:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,checks=tuple(reversed(q.checks)))); return m._canon(r1)==m._canon(r2)
    if k==18:
        p=replace(q.policy,residual_risk_floor=2); return m.evaluate(replace(q,policy=p)).decision==m.Decision.HOLD
    if k==19:
        a=m.default_evaluation(); b2=m.default_evaluation(); return m._canon(a)==m._canon(b2) and m._fp(a)==m._fp(b2)
    return False
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL121,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
