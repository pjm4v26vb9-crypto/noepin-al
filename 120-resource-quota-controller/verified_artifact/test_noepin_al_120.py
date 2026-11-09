import unittest
from dataclasses import replace
import noepin_al_120_resource_quota_controller as m

class TestAL120(unittest.TestCase): pass

def scenario(k,j):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_CANDIDATE and r.next_gate_candidate and not r.stop_candidate
    if k==1:
        us=tuple(replace(x,current_usage=82.0) if x.resource_id=='CPU_SECONDS' else x for x in q.current_usage); r=m.evaluate(replace(q,current_usage=us)); return r.next_action==m.NextAction.THROTTLE_CANDIDATE and r.escalation==m.Escalation.SOFT_THRESHOLD and 0<r.throttle_factor_candidate<1
    if k==2:
        us=tuple(replace(x,current_usage=100.0) if x.resource_id=='CPU_SECONDS' else x for x in q.current_usage); r=m.evaluate(replace(q,current_usage=us)); return r.decision==m.Decision.DENY and r.next_action==m.NextAction.STOP_CANDIDATE and r.stop_candidate and not r.next_gate_candidate
    if k==3:
        fs=tuple(replace(x,forecast_additional_usage=80.0) if x.resource_id=='CPU_SECONDS' else x for x in q.forecasts); r=m.evaluate(replace(q,forecasts=fs)); return r.next_action==m.NextAction.THROTTLE_CANDIDATE and r.escalation==m.Escalation.FORECAST_OVERAGE
    if k==4:
        us=tuple(replace(x,current_usage=None) if x.resource_id=='COST_USD' else x for x in q.current_usage); r=m.evaluate(replace(q,current_usage=us)); return r.decision==m.Decision.HOLD and r.next_action==m.NextAction.CONSERVATIVE_THROTTLE_CANDIDATE and r.escalation==m.Escalation.MEASUREMENT_UNKNOWN and not r.next_gate_candidate
    if k==5:
        fs=tuple(replace(x,forecast_additional_usage=None) if x.resource_id=='DISK_MB' else x for x in q.forecasts); return m.evaluate(replace(q,forecasts=fs)).decision==m.Decision.HOLD
    if k==6:
        return m.evaluate(replace(q,task_priority=1.2)).decision==m.Decision.HOLD
    if k==7:
        return m.evaluate(replace(q,quotas=q.quotas+(q.quotas[0],))).decision==m.Decision.HOLD
    if k==8:
        return m.evaluate(replace(q,current_usage=q.current_usage[:-1])).decision==m.Decision.HOLD
    if k==9:
        qs=(replace(q.quotas[0],hard_quota=float('nan')),)+q.quotas[1:]; return m.evaluate(replace(q,quotas=qs)).decision==m.Decision.HOLD
    if k==10:
        fs=(replace(q.forecasts[0],forecast_additional_usage=-1.0),)+q.forecasts[1:]; return m.evaluate(replace(q,forecasts=fs)).decision==m.Decision.HOLD
    if k==11:
        r=m.default_evaluation(); neg=(r.continue_promoted_to_permission,r.throttle_promoted_to_permission,r.stop_promoted_to_execution,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.resource_spend_authorized,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_quota_fingerprint=st.quota_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_forecast_fingerprint=st.forecast_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint); return r==st.result
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_quota_fingerprint=st.quota_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_forecast_fingerprint=st.forecast_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint); return r.decision==m.Decision.HOLD
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); us=tuple(replace(x,current_usage=x.current_usage+1 if x.resource_id=='API_CALLS' else x.current_usage) for x in q.current_usage); st2=m.prepare_state(replace(q,current_usage=us),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_usage)==1 and d.changed_usage[0].resource_id=='API_CALLS'
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); fs=tuple(replace(x,forecast_additional_usage=x.forecast_additional_usage+1 if x.resource_id=='TOKENS' else x.forecast_additional_usage) for x in q.forecasts); st2=m.prepare_state(replace(q,forecasts=fs),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('FORECAST:TOKENS',) and not sp.full_resend_required
    if k==17:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,quotas=tuple(reversed(q.quotas)),current_usage=tuple(reversed(q.current_usage)),forecasts=tuple(reversed(q.forecasts)))); return m._canon(r1)==m._canon(r2)
    if k==18:
        qs=(replace(q.quotas[0],hard_quota=0),)+q.quotas[1:]; return m.evaluate(replace(q,quotas=qs)).decision==m.Decision.HOLD
    if k==19:
        a=m.default_evaluation(); b2=m.default_evaluation(); return m._canon(a)==m._canon(b2) and m._fp(a)==m._fp(b2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL120,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
