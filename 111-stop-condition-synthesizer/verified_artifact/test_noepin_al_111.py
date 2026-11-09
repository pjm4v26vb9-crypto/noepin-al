import unittest
from dataclasses import replace
import noepin_al_111_stop_condition_synthesizer as m

class TestAL111(unittest.TestCase): pass

def base(): return m.default_request()
def run_prepared(st,ok=True,**changes):
    args=dict(integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_budget_fingerprint=st.budget_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_monitor_fingerprint=st.monitor_fingerprint); args.update(changes); return m.evaluate_prepared(st,**args)
def state(q,obs=None,usage=None,steps=10):
    if obs is None: obs=(('tests_passed',120),('artifact_frozen',False),('safety_violation',False),('replay_divergence',0))
    if usage is None: usage=(('risk_units',20.0),('tool_calls',40.0),('tokens',20000.0))
    return m.RuntimeState(tuple(obs),tuple(usage),steps,q.binding,q.state_epoch)

def scenario(k,variant):
    q=base(); mon=m.synthesize(q); b=q.binding; e=q.state_epoch
    if k==0:
        return mon.decision==m.Decision.ALLOW and mon.next_action==m.NextAction.MONITOR_READY_CANDIDATE and mon.runtime_monitor_ready and mon.conflict_free and mon.observable_coverage_complete and mon.next_gate_candidate
    if k==1:
        qq=replace(q,success_criteria=()); z=m.synthesize(qq); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.OBSERVABILITY_GAP and 'SUCCESS_CRITERIA_MISSING' in z.reasons
    if k==2:
        p=replace(q.success_criteria[0],observable=False); qq=replace(q,success_criteria=(p,)+q.success_criteria[1:]); z=m.synthesize(qq); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.OBSERVABILITY_GAP
    if k==3:
        p=replace(q.failure_criteria[0],predicate_id='FAIL:C',field=q.success_criteria[1].field,operator=q.success_criteria[1].operator,expected=q.success_criteria[1].expected); qq=replace(q,failure_criteria=(p,)+q.failure_criteria[1:]); z=m.synthesize(qq); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.PREDICATE_CONFLICT
    if k==4:
        obs=(('tests_passed',160),('artifact_frozen',False),('safety_violation',False),('replay_divergence',0)); z=m.evaluate_runtime(q,mon,state(q,obs=obs)); return z.next_action==m.NextAction.CONTINUE_CANDIDATE and not z.completion_reached and not z.abort_reached
    if k==5:
        obs=(('tests_passed',160),('artifact_frozen',True),('safety_violation',False),('replay_divergence',0)); z=m.evaluate_runtime(q,mon,state(q,obs=obs)); return z.next_action==m.NextAction.NORMAL_STOP_CANDIDATE and z.completion_reached and not z.stop_executed
    if k==6:
        obs=(('tests_passed',160),('artifact_frozen',True),('safety_violation',True),('replay_divergence',0)); z=m.evaluate_runtime(q,mon,state(q,obs=obs)); return z.next_action==m.NextAction.ABORT_STOP_CANDIDATE and z.abort_reached and not z.completion_reached and 'SUCCESS_ALSO_TRUE_ABORT_PRECEDENCE' in z.reasons
    if k==7:
        usage=(('risk_units',101.0),('tool_calls',40.0),('tokens',20000.0)); z=m.evaluate_runtime(q,mon,state(q,usage=usage)); return z.next_action==m.NextAction.ABORT_STOP_CANDIDATE and z.budget_exceeded and not z.stop_executed
    if k==8:
        z=m.evaluate_runtime(q,mon,state(q,steps=q.max_steps)); return z.next_action==m.NextAction.ABORT_STOP_CANDIDATE and z.max_steps_reached
    if k==9:
        qq=replace(q,max_steps=0); z=m.synthesize(qq); return z.decision==m.Decision.HOLD and 'MAX_STEPS_INVALID' in z.reasons
    if k==10:
        bb=q.budgets+(q.budgets[0],); z=m.synthesize(replace(q,budgets=bb)); return z.decision==m.Decision.HOLD and 'DUPLICATE_BUDGET_RESOURCE' in z.reasons
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); return run_prepared(st)==st.precomputed_result
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return run_prepared(st,False).decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); p=replace(q.success_criteria[0],expected=161,predicate_fingerprint='FP-SUCCESS-TESTS2'); q2=replace(q,success_criteria=(p,)+q.success_criteria[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_success_predicates)==1 and sp.missing_or_changed_record_ids==('SUCCESS:SUCCESS:TESTS',)
    if k==15:
        neg=(mon.permission_granted,mon.approval_executed,mon.stop_executed,mon.action_executed,mon.plan_committed,mon.external_write_performed,mon.world_truth_proven,mon.domain_authority_promoted,mon.safety_proven,mon.action_success); return not any(neg)
    if k==16:
        q2=replace(q,success_criteria=tuple(reversed(q.success_criteria)),failure_criteria=tuple(reversed(q.failure_criteria)),budgets=tuple(reversed(q.budgets))); return m.synthesize(q)==m.synthesize(q2)
    if k==17:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=run_prepared(st,current_monitor_fingerprint='BAD'); return z.decision==m.Decision.HOLD and 'PREPARED_FINGERPRINT_MISMATCH_REEVALUATION_REQUIRED' in z.reasons
    if k==18:
        s=state(q); bad=replace(s,binding='BAD'); z=m.evaluate_runtime(q,mon,bad); return z.decision==m.Decision.HOLD and 'RUNTIME_BINDING_MISMATCH' in z.reasons
    if k==19:
        z1=m.default_synthesis(); z2=m.default_synthesis(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL111,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
