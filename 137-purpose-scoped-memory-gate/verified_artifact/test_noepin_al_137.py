import unittest
from dataclasses import replace
import noepin_al_137_purpose_scoped_memory_gate as m
B='B'; E='E'
def mem(mid='M',sem='S',tags=('P',),sens=m.Sensitivity.INTERNAL,rel=.9,nec=.9,trust=.9,perm=True,active=True,kind=m.RecordKind.MEMORY):
    return m.MemoryMetadata(mid,sem,tags,sens,rel,nec,trust,perm,active,kind,'SRC',1,B,E)
def req(xs=(),tags=('P',),clarity=True,goal='goal',policy=None): return m.PurposeGateRequest('R',goal,tags,clarity,tuple(xs),policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.MEMORY_SUPPLY_CANDIDATE and r.gate_state==m.GateState.ALLOWED_SET_CANDIDATE and r.allowed_memory_ids==('MEM-1',)
    if k==1:
        r=m.evaluate(req([mem(nec=.2)])); return r.decision==m.Decision.ALLOW and r.allowed_memory_ids==() and r.gate_state==m.GateState.EXCLUDED_ONLY
    if k==2:
        r=m.evaluate(req([mem(tags=('Q',))])); return r.allowed_memory_ids==() and r.excluded_memory_ids==('M',)
    if k==3:
        r=m.evaluate(req([mem(sens=m.Sensitivity.SENSITIVE,perm=True)])); return r.decision==m.Decision.ALLOW and r.allowed_memory_ids==('M',)
    if k==4:
        r=m.evaluate(req([mem(sens=m.Sensitivity.SENSITIVE,nec=.1,perm=False)])); return r.decision==m.Decision.ALLOW and r.gate_state==m.GateState.EXCLUDED_ONLY
    if k==5:
        r=m.evaluate(req([mem()],tags=(),clarity=False,goal='')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.PURPOSE_AMBIGUOUS and not r.allowed_memory_ids
    if k==6:
        r=m.evaluate(req([mem(sens=m.Sensitivity.SENSITIVE,rel=None)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SENSITIVE_RELEVANCE_UNKNOWN
    if k==7:
        r=m.evaluate(req([mem(sens=m.Sensitivity.RESTRICTED,perm=False)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SENSITIVE_PERMISSION_MISSING
    if k==8:
        r=m.evaluate(req([mem(sens=m.Sensitivity.UNKNOWN)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_SENSITIVITY
    if k==9:
        r=m.evaluate(req([mem(active=False)])); return r.decision==m.Decision.ALLOW and not r.allowed_memory_ids
    if k==10:
        r=m.evaluate(req([mem(kind=m.RecordKind.MENTION)])); return r.gate_state==m.GateState.MENTION_ONLY and not r.allowed_memory_ids
    if k==11:
        a=mem('A','SEM',rel=.91,nec=.91,trust=.9); b=mem('B','SEM',rel=.99,nec=.99,trust=.99); r=m.evaluate(req([a,b])); return r.allowed_memory_ids==('B',) and 'A' in r.excluded_memory_ids
    if k==12:
        r=m.evaluate(req([mem(trust=.2)])); return r.allowed_memory_ids==() and r.gate_state==m.GateState.EXCLUDED_ONLY
    if k==13:
        r=m.evaluate(req([mem('B','S2'),mem('A','S1')])); return r.allowed_memory_ids==('A','B')
    if k==14:
        r=m.default_evaluation(); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.allowed_set_transferred_to_reasoner,r.purpose_match_promoted_to_permission,r.permission_evidence_promoted_to_permission_execution,r.sensitivity_promoted_to_truth,r.external_retrieval_executed,r.memory_write_performed,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st) and m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==17:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],trust=.88); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_memories)==1 and p.missing_or_changed_record_ids==('MEMORY:MEM-1',) and not p.full_resend_required
    if k==18:
        p=replace(m.default_policy(),min_trust=float('nan')); return m.evaluate(req([mem()],policy=p)).decision==m.Decision.HOLD
    if k==19:
        r=m.evaluate(req([mem('A'),mem('A')])); return r.decision==m.Decision.HOLD and r.gate_state==m.GateState.INVALID
    return False
class TestAL137(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL137,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
