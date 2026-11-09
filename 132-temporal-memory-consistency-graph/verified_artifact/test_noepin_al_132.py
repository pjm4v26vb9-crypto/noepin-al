import unittest
from dataclasses import replace
import noepin_al_132_temporal_memory_consistency_graph as m
B='B'; E='E'
def mem(mid,val,start=10,end=None,branch='MAIN',sup=(),kind=m.RecordKind.MEMORY,trust=.9,entity='X',rel='STATE',src='SRC'):
    return m.MemoryRecord(mid,entity,rel,val,src,start,end,branch,tuple(sup),kind,trust,B,E)
def req(ms,qt=None,critical=False,policy=None,entity='X',rel='STATE'):
    return m.TemporalMemoryRequest('Q',tuple(ms),entity,rel,qt,critical,policy or m.default_policy(),B,E)

def scenario(k,v):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.temporal_state==m.TemporalState.CURRENT_CANDIDATE and [x.value for x in r.current_candidates]==['B'] and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([mem('A','old',10,None),mem('B','new',20,None,sup=('A',))])); return r.current_candidates[0].memory_id=='B' and any(n.memory_id=='A' and n.status==m.NodeStatus.SUPERSEDED for n in r.graph)
    if k==2:
        r=m.evaluate(req([mem('A','one',10,None),mem('B','two',10,None)])); return r.decision==m.Decision.HOLD and r.temporal_state==m.TemporalState.CONFLICT and r.escalation==m.Escalation.TEMPORAL_CONFLICT
    if k==3:
        r=m.evaluate(req([mem('A','one',10,None),mem('B','two',10,None)],critical=True)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CRITICAL_TEMPORAL_CONFLICT
    if k==4:
        r=m.evaluate(req([mem('A','old',10,20),mem('B','new',20,None)],qt=15)); return r.temporal_state==m.TemporalState.HISTORICAL_CANDIDATE and r.current_candidates[0].value=='old'
    if k==5:
        r=m.evaluate(req([mem('A','x',None,None)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_TIME
    if k==6:
        r=m.evaluate(req([mem('M','x',10,None,kind=m.RecordKind.MENTION)])); return r.decision==m.Decision.HOLD and not r.current_candidates and any(n.status==m.NodeStatus.MENTION_ONLY for n in r.graph)
    if k==7:
        r=m.evaluate(req([mem('A','x',10,None,trust=.2)])); return r.decision==m.Decision.HOLD and any(n.status==m.NodeStatus.BELOW_TRUST for n in r.graph)
    if k==8:
        r=m.evaluate(req([mem('A','one',10,None,branch='P1'),mem('B','two',10,None,branch='P2')])); return r.conflicts[0].reason=='PARALLEL_BRANCH_CURRENT_AMBIGUITY'
    if k==9:
        r=m.evaluate(req([mem('A','same',10,None),mem('B','same',12,None)])); return r.decision==m.Decision.ALLOW and len(r.current_candidates)==2 and not r.conflicts
    if k==10:
        r=m.evaluate(req([mem('A','x',10,10)])); return r.temporal_state==m.TemporalState.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.current_candidate_promoted_to_truth,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).temporal_state==m.TemporalState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); xs=list(q.memories); xs[1]=replace(xs[1],trust=.91); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_memories)==1 and d.changed_memories[0].memory_id=='MEM-NEW'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); q2=replace(q,query_time=25); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('QUERY_CONTEXT',) and not p.full_resend_required
    if k==17:
        q=m.default_request(); q2=replace(q,memories=tuple(reversed(q.memories))); return m._canon(m.evaluate(q))==m._canon(m.evaluate(q2))
    if k==18:
        pol=replace(m.default_policy(),min_trust=float('nan')); return m.evaluate(req([],policy=pol)).temporal_state==m.TemporalState.INVALID
    if k==19:
        a=mem('A','x',10,None,sup=('B',)); b=mem('B','y',20,None,sup=('A',)); return m.evaluate(req([a,b])).temporal_state==m.TemporalState.INVALID
    return False
class TestAL132(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL132,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
