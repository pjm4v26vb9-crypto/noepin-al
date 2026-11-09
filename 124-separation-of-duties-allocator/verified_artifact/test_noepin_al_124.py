import unittest, math
from dataclasses import replace
import noepin_al_124_separation_of_duties_allocator as m

class TestAL124(unittest.TestCase): pass

def scenario(k,rpt):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.ASSIGNMENT_CANDIDATE and r.next_gate_candidate and len(r.assignments)==4 and not r.sod_violations and not r.unassigned_roles
    if k==1:
        # Normal separation: all four roles must be on distinct agents under default conflicts/reviewer policy.
        r=m.evaluate(q); return len({a.agent_id for a in r.assignments})==4
    if k==2:
        # Self-approval: only one agent can PLAN+APPROVE, making a valid split impossible.
        agents=tuple(a for a in q.agents if a.agent_id not in {'AGENT-APPROVE'})
        agents=tuple(replace(a,capabilities=tuple(sorted(set(a.capabilities+('APPROVE',))))) if a.agent_id=='AGENT-PLAN' else a for a in agents)
        r=m.evaluate(replace(q,agents=agents)); return r.decision==m.Decision.HUMAN_APPROVAL and 'TASK-CHANGE:APPROVER' in r.unassigned_roles
    if k==3:
        agents=tuple(replace(a,available=False) if a.agent_id=='AGENT-EXEC' else a for a in q.agents); r=m.evaluate(replace(q,agents=agents)); return r.decision==m.Decision.HUMAN_APPROVAL and 'TASK-CHANGE:EXECUTOR' in r.unassigned_roles
    if k==4:
        # Role conflict forces alternate planner/reviewer mapping but remains satisfiable.
        agents=q.agents+(m.Agent('AGENT-ALT',('PLAN','REVIEW'),.89,'DOMAIN-E',True,False,b,e),)
        r=m.evaluate(replace(q,agents=agents)); return r.decision==m.Decision.ALLOW and not r.sod_violations
    if k==5:
        agents=q.agents+(m.Agent('AGENT-ALT-APPROVE',('APPROVE',),.99,'DOMAIN-E',True,False,b,e),); r=m.evaluate(replace(q,agents=agents)); return r.decision==m.Decision.ALLOW and any(a.agent_id=='AGENT-ALT-APPROVE' for a in r.assignments if a.role_id=='APPROVER')
    if k==6:
        agents=tuple(replace(a,trust=.2) if a.agent_id=='AGENT-REVIEW' else a for a in q.agents); r=m.evaluate(replace(q,agents=agents)); return r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.INDEPENDENT_REVIEWER_UNAVAILABLE
    if k==7:
        p=replace(q.policy,allow_human_escalation=False); agents=tuple(replace(a,available=False) if a.agent_id=='AGENT-EXEC' else a for a in q.agents); r=m.evaluate(replace(q,agents=agents,policy=p)); return r.decision==m.Decision.HOLD
    if k==8:
        roles=q.roles+(q.roles[0],); return m.evaluate(replace(q,roles=roles)).escalation==m.Escalation.INVALID_CONFIGURATION
    if k==9:
        agents=q.agents+(q.agents[0],); return m.evaluate(replace(q,agents=agents)).escalation==m.Escalation.INVALID_CONFIGURATION
    if k==10:
        roles=tuple(replace(x,minimum_trust=float('nan')) if x.role_id=='PLANNER' else x for x in q.roles); return m.evaluate(replace(q,roles=roles)).decision==m.Decision.HOLD
    if k==11:
        bad=(m.ConflictRule('PLANNER','UNKNOWN'),); return m.evaluate(replace(q,conflicts=bad)).escalation==m.Escalation.INVALID_CONFIGURATION
    if k==12:
        r=m.default_evaluation(); neg=(r.assignment_promoted_to_permission,r.assignment_promoted_to_role_authority,r.independent_review_promoted_to_approval_execution,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_role_fingerprint=st.role_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_conflict_fingerprint=st.conflict_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_role_fingerprint=st.role_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_conflict_fingerprint=st.conflict_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); agents=tuple(replace(a,trust=a.trust-.01) if a.agent_id=='AGENT-PLAN' else a for a in q.agents); st2=m.prepare_state(replace(q,agents=agents),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_agents)==1 and d.changed_agents[0].agent_id=='AGENT-PLAN'
    if k==17:
        st=m.prepare_state(q,binding=b,state_epoch=e); roles=tuple(replace(x,minimum_trust=x.minimum_trust+.01) if x.role_id=='PLANNER' else x for x in q.roles); st2=m.prepare_state(replace(q,roles=roles),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('ROLE:TASK-CHANGE:PLANNER',) and not sp.full_resend_required
    if k==18:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,roles=tuple(reversed(q.roles)),agents=tuple(reversed(q.agents)),conflicts=tuple(reversed(q.conflicts)))); return m._canon(r1)==m._canon(r2)
    if k==19:
        # Reviewer requirement cannot be silently dropped.
        roles=tuple(r for r in q.roles if r.role_id!='REVIEWER'); return m.evaluate(replace(q,roles=roles)).escalation==m.Escalation.INVALID_CONFIGURATION
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL124,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
