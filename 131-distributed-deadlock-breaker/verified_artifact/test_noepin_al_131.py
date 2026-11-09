import unittest
from dataclasses import replace
import noepin_al_131_distributed_deadlock_breaker as m
B='B'; E='E'
def edge(w,h,r,k='RESOURCE'): return m.WaitEdge(w,h,r,k,B,E)
def lock(r,o,critical=False,safe=True,cost=.2): return m.ResourceLock(r,o,critical,safe,cost,B,E)
def pri(a,p=50,risk=.2,cost=.2): return m.AgentPriority(a,p,risk,cost,B,E)
def req(edges,locks,ps,occ=1,policy=None): return m.DeadlockRequest('Q',tuple(edges),tuple(locks),tuple(ps),occ,policy or m.default_policy(),B,E)

def scenario(k,v):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.deadlock_state==m.DeadlockState.BREAK_CANDIDATE and r.victim_agent_id=='AGENT-C' and r.next_action==m.NextAction.RELEASE_RETRY_CANDIDATE and r.next_gate_candidate
    if k==1:
        q=req([edge('A','B','RB')],[lock('RB','B')],[pri('A'),pri('B')]); r=m.evaluate(q); return r.deadlock_state==m.DeadlockState.NO_CYCLE and r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_CANDIDATE
    if k==2:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A'),lock('RB','B',critical=True)],[pri('A',20),pri('B',30)]); r=m.evaluate(q); return r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.CRITICAL_LOCK
    if k==3:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A',safe=False),lock('RB','B',safe=False)],[pri('A'),pri('B')]); r=m.evaluate(q); return r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.SAFETY_INVARIANT_RISK
    if k==4:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A'),lock('RB','B')],[pri('A'),pri('B')],occ=3); r=m.evaluate(q); return r.decision==m.Decision.HUMAN_APPROVAL and r.deadlock_state==m.DeadlockState.REDESIGN_REQUIRED and r.next_action==m.NextAction.PLAN_REDESIGN_CANDIDATE
    if k==5:
        q=req([edge('A','B','RB'),edge('B','A','RA'),edge('C','D','RD'),edge('D','C','RC')],[lock('RA','A'),lock('RB','B'),lock('RC','C'),lock('RD','D')],[pri('A',10),pri('B',20),pri('C',30),pri('D',40)]); r=m.evaluate(q); return len(r.cycles)==2 and r.victim_agent_id=='A'
    if k==6:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A'),lock('RB','B')],[pri('A',20,risk=.9),pri('B',30,risk=.9)]); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NO_SAFE_VICTIM
    if k==7:
        q=req([edge('A','A','RA')],[lock('RA','A')],[pri('A',10)]); r=m.evaluate(q); return len(r.cycles)==1 and r.victim_agent_id=='A'
    if k==8:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A'),lock('RB','B')],[pri('A',80),pri('B',10)]); return m.evaluate(q).victim_agent_id=='B'
    if k==9:
        q=req([edge('A','B','RB'),edge('B','A','RA')],[lock('RA','A',cost=.9),lock('RB','B',cost=.9)],[pri('A',10,cost=.9),pri('B',20,cost=.9)]); return m.evaluate(q).escalation==m.Escalation.NO_SAFE_VICTIM
    if k==10:
        q=req([edge('A','B','RB')],[lock('RB','A')],[pri('A'),pri('B')]); return m.evaluate(q).deadlock_state==m.DeadlockState.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.cycle_promoted_to_truth,r.victim_promoted_to_permission,r.release_plan_executed,r.retry_executed,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_wait_fingerprint=st.wait_fingerprint,current_lock_fingerprint=st.lock_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_wait_fingerprint=st.wait_fingerprint,current_lock_fingerprint=st.lock_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).deadlock_state==m.DeadlockState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); ls=list(q.locks); ls[-1]=replace(ls[-1],safe_release=False); q2=replace(q,locks=tuple(ls)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_locks)==1 and d.changed_locks[0].resource_id=='R-C'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); q2=replace(q,occurrence_count=2); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('OCCURRENCE_COUNT',) and not p.full_resend_required
    if k==17:
        q=m.default_request(); q2=replace(q,wait_edges=tuple(reversed(q.wait_edges)),locks=tuple(reversed(q.locks)),priorities=tuple(reversed(q.priorities))); return m._canon(m.evaluate(q))==m._canon(m.evaluate(q2))
    if k==18:
        pol=replace(m.default_policy(),max_auto_risk=float('nan')); q=req([],[],[],policy=pol); return m.evaluate(q).deadlock_state==m.DeadlockState.INVALID
    if k==19:
        q=req([edge('A','B','RB'),edge('A','B','RB')],[lock('RB','B')],[pri('A'),pri('B')]); return m.evaluate(q).deadlock_state==m.DeadlockState.INVALID
    return False
class TestAL131(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL131,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
