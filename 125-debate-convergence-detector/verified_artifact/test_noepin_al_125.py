import unittest
from dataclasses import replace
import noepin_al_125_debate_convergence_detector as m

class TestAL125(unittest.TestCase): pass

def scenario(k,rpt):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.STOP_DEBATE_CANDIDATE and r.convergence_state==m.ConvergenceState.CONVERGED and r.next_gate_candidate
    if k==1:
        turns=q.turns[:2]; r=m.evaluate(replace(q,turns=turns)); return r.convergence_state==m.ConvergenceState.CONTINUING and r.escalation==m.Escalation.INSUFFICIENT_HISTORY
    if k==2:
        turns=tuple(replace(t,evidence_ids=t.evidence_ids+(f'NEW-{t.turn_index}',),position=.1*t.turn_index) for t in q.turns); r=m.evaluate(replace(q,turns=turns)); return r.next_action==m.NextAction.CONTINUE_DEBATE_CANDIDATE
    if k==3:
        turns=(m.DebateTurn(1,'A','X','C',('E',),.8,b,e),m.DebateTurn(2,'B','Y','C',('E',),-.8,b,e),m.DebateTurn(3,'C','X','C',('E',),.8,b,e),m.DebateTurn(4,'D','Y','C',('E',),-.8,b,e),m.DebateTurn(5,'E','X','C',('E',),.8,b,e)); r=m.evaluate(replace(q,turns=turns)); return r.convergence_state==m.ConvergenceState.OSCILLATING and r.decision==m.Decision.HUMAN_APPROVAL
    if k==4:
        turns=tuple(replace(t,position=(-.4 if i%2 else .4),evidence_ids=('E1',)) for i,t in enumerate(q.turns)); p=replace(q.policy,oscillation_min_flips=99); r=m.evaluate(replace(q,turns=turns,policy=p)); return r.convergence_state==m.ConvergenceState.STAGNANT
    if k==5:
        issues=(m.DebateIssue('CRIT',m.IssueSeverity.CRITICAL,False),); r=m.evaluate(replace(q,risk=m.RiskClass.HIGH,issues=issues)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MATERIAL_ISSUE_UNRESOLVED
    if k==6:
        issues=(m.DebateIssue('LOW',m.IssueSeverity.LOW,False),); r=m.evaluate(replace(q,risk=m.RiskClass.HIGH,issues=issues)); return r.convergence_state==m.ConvergenceState.CONVERGED
    if k==7:
        r=m.evaluate(replace(q,risk=m.RiskClass.UNKNOWN)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_RISK
    if k==8:
        turns=tuple(m.DebateTurn(i,f'M{i}',f'A{i%3}',f'C{i%4}',(f'E{i}',),-0.45+i*0.04,b,e) for i in range(1,21)); issues=(m.DebateIssue('M',m.IssueSeverity.MEDIUM,False),); r=m.evaluate(replace(q,turns=turns,issues=issues)); return r.max_turn_reached and r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.MAX_TURNS
    if k==9:
        turns=tuple(m.DebateTurn(i,f'M{i}',f'A{i%3}',f'C{i%4}',(f'E{i}',),-0.45+i*0.04,b,e) for i in range(1,21)); p=replace(q.policy,allow_human_escalation=False); issues=(m.DebateIssue('M',m.IssueSeverity.MEDIUM,False),); r=m.evaluate(replace(q,turns=turns,issues=issues,policy=p)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MAX_TURNS
    if k==10:
        turns=q.turns+(q.turns[0],); return m.evaluate(replace(q,turns=turns)).escalation==m.Escalation.INVALID_CONFIGURATION
    if k==11:
        turns=tuple(replace(t,position=9) if t.turn_id=='T5' else t for t in q.turns); return m.evaluate(replace(q,turns=turns)).convergence_state==m.ConvergenceState.INVALID
    if k==12:
        r=m.default_evaluation(); neg=(r.convergence_promoted_to_truth,r.confidence_promoted_to_safety_proof,r.stop_candidate_promoted_to_stop_execution,r.continue_candidate_promoted_to_permission,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_turn_fingerprint=st.turn_fingerprint,current_issue_fingerprint=st.issue_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_turn_fingerprint=st.turn_fingerprint,current_issue_fingerprint=st.issue_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); turns=tuple(replace(t,position=t.position+.01) if t.turn_id=='T5' else t for t in q.turns); st2=m.prepare_state(replace(q,turns=turns),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_turns)==1 and d.changed_turns[0].turn_id=='T5'
    if k==17:
        st=m.prepare_state(q,binding=b,state_epoch=e); issues=(m.DebateIssue('ISSUE-LOW',m.IssueSeverity.LOW,False),); st2=m.prepare_state(replace(q,issues=issues),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('ISSUE:ISSUE-LOW',) and not sp.full_resend_required
    if k==18:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,turns=tuple(reversed(q.turns)),issues=tuple(reversed(q.issues)))); return m._canon(r1)==m._canon(r2)
    if k==19:
        issues=(m.DebateIssue('CRIT',m.IssueSeverity.CRITICAL,False),); turns=tuple(replace(t,position=.1,evidence_ids=('E1',)) for t in q.turns); r=m.evaluate(replace(q,risk=m.RiskClass.CRITICAL,issues=issues,turns=turns)); return r.convergence_state==m.ConvergenceState.UNRESOLVED and r.next_action==m.NextAction.HOLD_UNRESOLVED_REVIEW
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL125,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
