import unittest
from dataclasses import replace
import noepin_al_130_reviewer_rotation_scheduler as m
B='B'; E='E'
def ag(i,f,p,t=.9,av=True,cap=True): return m.ReviewerAgent(i,f,p,t,av,cap,B,E)
def task(risk=m.TaskRisk.CRITICAL,sub='S',fam='F0',prov='P0'): return m.ReviewTask('T',sub,fam,prov,risk,B,E)
def hist(s,r,seq=1): return m.ReviewEvent(s,r,f'OLD-{seq}',seq,'PAIR','PAIR')
def req(agents,history=(),risk=m.TaskRisk.CRITICAL,rules=None,sub='S',fam='F0',prov='P0'):
    return m.RotationRequest('R',task(risk,sub,fam,prov),tuple(agents),tuple(history),rules or m.default_rules(),B,E)

def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.reviewer_assignment=='REVIEWER-B' and r.next_action==m.NextAction.REVIEWER_ASSIGNMENT_CANDIDATE
    if k==1:
        q=req([ag('S','F0','P0'),ag('R1','F1','P1')]); return m.evaluate(q).reviewer_assignment=='R1'
    if k==2:
        q=req([ag('S','F0','P0')]); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.rotation_state==m.RotationState.NO_INDEPENDENT_REVIEWER
    if k==3:
        q=req([ag('R1','F0','P1'),ag('R2','F2','P2')]); return m.evaluate(q).reviewer_assignment=='R2'
    if k==4:
        q=req([ag('R1','F1','P0'),ag('R2','F2','P2')]); return m.evaluate(q).reviewer_assignment=='R2'
    if k==5:
        rules=replace(m.default_rules(),recent_pair_window=3,max_same_pair_in_window=1); q=req([ag('R1','F1','P1'),ag('R2','F2','P2')],[hist('S','R1',1)] ,rules=rules); return m.evaluate(q).reviewer_assignment=='R2'
    if k==6:
        q=req([ag('R1','F1','P1',av=False),ag('R2','F2','P2')]); return m.evaluate(q).reviewer_assignment=='R2'
    if k==7:
        q=req([ag('R1','F1','P1',cap=False),ag('R2','F2','P2')]); return m.evaluate(q).reviewer_assignment=='R2'
    if k==8:
        q=req([ag('R1','F1','P1',t=.2),ag('R2','F2','P2')]); return m.evaluate(q).reviewer_assignment=='R2'
    if k==9:
        rules=replace(m.default_rules(),forbidden_pairs=(('S','R1'),)); q=req([ag('R1','F1','P1'),ag('R2','F2','P2')],rules=rules); return m.evaluate(q).reviewer_assignment=='R2'
    if k==10:
        q=req([ag('R1','F1','P1')],risk=m.TaskRisk.LOW); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.rotation_state==m.RotationState.ASSIGNABLE
    if k==11:
        r=m.default_evaluation(); neg=(r.reviewer_assignment_promoted_to_permission,r.reviewer_assignment_executed,r.review_executed,r.independence_promoted_to_safety_proof,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.rotation_state==m.RotationState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); aa=list(q.agents); aa[0]=replace(aa[0],trust=.91); q2=replace(q,agents=tuple(aa)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_agents)==1 and d.changed_agents[0].agent_id=='REVIEWER-A'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); q2=replace(q,history=q.history+(hist('AGENT-SUBJECT','REVIEWER-B',9),)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); p=m.plan_missing_only(st,st2); return len(p.missing_or_changed_record_ids)==1 and p.missing_or_changed_record_ids[0].startswith('HISTORY:') and not p.full_resend_required
    if k==17:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,agents=tuple(reversed(q.agents)))))
    if k==18:
        rules=replace(m.default_rules(),critical_min_independence=float('nan')); q=req([ag('R1','F1','P1')],rules=rules); return m.evaluate(q).rotation_state==m.RotationState.INVALID
    if k==19:
        q=req([ag('R1','F1','P1'),ag('R1','F2','P2')]); return m.evaluate(q).rotation_state==m.RotationState.INVALID
    return False
class TestAL130(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL130,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
