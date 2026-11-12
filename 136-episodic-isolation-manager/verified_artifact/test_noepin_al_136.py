import unittest
from dataclasses import replace
import noepin_al_136_episodic_isolation_manager as m
B='B'; E='E'
def mem(i,task='T1',session='S1',scope=m.ScopeMode.TASK,sens=m.Sensitivity.INTERNAL,reuse=.9,trust=.9,approved=True,kind=m.RecordKind.MEMORY):
    return m.SessionMemory(i,'v',task,session,scope,sens,reuse,trust,approved,kind,'SRC','P',B,E)
def req(xs,task='T1',session='S2',promo=True,policy=None): return m.IsolationRequest('R',tuple(xs),task,session,promo,policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.isolation_state==m.IsolationState.PROMOTION_CANDIDATE and r.promotion_candidate_ids==('MEM-1',) and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([mem('A')],promo=False)); return r.decision==m.Decision.ALLOW and r.visible_memory_ids==('A',) and r.next_action==m.NextAction.SAME_SCOPE_REFERENCE_CANDIDATE
    if k==2:
        r=m.evaluate(req([mem('A',task='T2')],promo=False)); return r.decision==m.Decision.ALLOW and r.blocked_transfer_ids==('A',) and r.isolation_state==m.IsolationState.BLOCKED_CROSS_SCOPE
    if k==3:
        r=m.evaluate(req([mem('A',scope=m.ScopeMode.SESSION_ONLY,session='S1')],session='S2',promo=False)); return r.blocked_transfer_ids==('A',)
    if k==4:
        r=m.evaluate(req([mem('A',sens=m.Sensitivity.SENSITIVE,approved=False)])); return r.decision==m.Decision.HUMAN_APPROVAL and r.human_approval_ids==('A',) and r.escalation==m.Escalation.SENSITIVE_APPROVAL_REQUIRED
    if k==5:
        r=m.evaluate(req([mem('A',approved=False)])); return r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.PROMOTION_APPROVAL_REQUIRED
    if k==6:
        r=m.evaluate(req([mem('A',task=None)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_TASK_SCOPE
    if k==7:
        r=m.evaluate(req([mem('A',sens=m.Sensitivity.UNKNOWN)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_SENSITIVITY and not r.promotion_candidate_ids
    if k==8:
        r=m.evaluate(req([mem('A',reuse=.2)])); return r.decision==m.Decision.ALLOW and not r.promotion_candidate_ids and 'A' in r.isolated_memory_ids
    if k==9:
        r=m.evaluate(req([mem('A',trust=.2)])); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.LOW_TRUST and not r.promotion_candidate_ids
    if k==10:
        r=m.evaluate(req([mem('M',kind=m.RecordKind.MENTION)])); return r.isolation_state==m.IsolationState.MENTION_ONLY and not r.mention_promoted_to_memory
    if k==11:
        r=m.default_evaluation(); names=('memory_promoted_to_truth','mention_promoted_to_memory','promotion_written_to_long_term','approval_evidence_promoted_to_approval_execution','same_scope_visibility_promoted_to_cross_scope_authority','sensitivity_promoted_to_truth','blocked_transfer_executed','memory_write_performed','dcsr_reconstruction_created_memory','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'); return not any(getattr(r,n) for n in names)
    if k==12:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,memories=tuple(reversed(q.memories)))))
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st)
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],trust=.88); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_memories)==1 and d.changed_memories[0].memory_id=='MEM-1'
    if k==17:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],trust=.88); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('MEMORY:MEM-1',) and not p.full_resend_required
    if k==18:
        p=replace(m.default_policy(),min_trust=float('nan')); return m.evaluate(req([],policy=p)).decision==m.Decision.HOLD
    if k==19:
        r=m.evaluate(req([mem('A'),mem('A')])); return r.decision==m.Decision.HOLD and r.isolation_state==m.IsolationState.INVALID
    return False
class TestAL136(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL136,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
