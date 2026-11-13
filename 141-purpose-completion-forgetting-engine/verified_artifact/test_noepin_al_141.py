import unittest
from dataclasses import replace
import noepin_al_141_purpose_completion_forgetting_engine as m
B='B'; E='E'
def mem(k='M',purposes=('P',),kind=m.MemoryKind.GENERAL,rc=m.RetentionClass.DELETE_AFTER_PURPOSE,legal=False,audit=False,prov=False,reason=''):
    return m.MemoryRecord(k,tuple(purposes),kind,rc,(f'TRACE-{k}',),legal,audit,prov,reason,B,E)
def req(xs=(),completed=('P',),policy=None): return m.ForgetRequest('R',tuple(completed),tuple(xs),policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.PLAN_READY_CANDIDATE and r.delete_candidate_ids==('MEM-141-A',) and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([mem(legal=True)])); return r.retain_candidate_ids==('M',) and r.plan[0].action==m.PlanAction.RETAIN_CANDIDATE
    if k==2:
        r=m.evaluate(req([mem(kind=m.MemoryKind.CREDENTIAL)])); return r.delete_candidate_ids==('M',) and not r.credential_revoked and not r.delete_executed
    if k==3:
        r=m.evaluate(req([mem(rc=m.RetentionClass.ARCHIVE_AFTER_PURPOSE)])); return r.archive_candidate_ids==('M',) and not r.archive_executed
    if k==4:
        r=m.evaluate(req([mem(rc=m.RetentionClass.UNKNOWN)])); return r.decision==m.Decision.HOLD and r.review_memory_ids==('M',) and r.next_action==m.NextAction.REVIEW_RETENTION_CANDIDATE
    if k==5:
        r=m.evaluate(req([mem(audit=True)])); return r.retain_candidate_ids==('M',) and 'AUDIT_RETENTION_REQUIRED' in r.plan[0].reasons
    if k==6:
        r=m.evaluate(req([mem(prov=True)])); return r.retain_candidate_ids==('M',) and 'PROVENANCE_RETENTION_REQUIRED' in r.plan[0].reasons
    if k==7:
        r=m.evaluate(req([mem(purposes=('P','ACTIVE'))])); return r.retain_candidate_ids==('M',) and r.plan[0].remaining_purposes==('ACTIVE',)
    if k==8:
        r=m.evaluate(req([mem(purposes=('OTHER',))])); return r.plan[0].action==m.PlanAction.NO_CHANGE_CANDIDATE and not r.delete_candidate_ids
    if k==9:
        r=m.evaluate(req([mem(rc=m.RetentionClass.ANONYMIZE_AFTER_PURPOSE,kind=m.MemoryKind.PERSONAL)])); return r.anonymize_candidate_ids==('M',) and not r.anonymize_executed
    if k==10:
        r=m.evaluate(req([])); return r.engine_state==m.EngineState.EMPTY and r.next_gate_candidate
    if k==11:
        r=m.evaluate(req([mem('A'),mem('A')])); return r.engine_state==m.EngineState.INVALID
    if k==12:
        r=m.evaluate(req([replace(mem(),binding='OTHER')])); return r.engine_state==m.EngineState.INVALID
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memories_fingerprint=st.memories_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return m.validate_prepared_integrity(st) and r==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memories_fingerprint=st.memories_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint='BAD',current_memories_fingerprint=st.memories_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,memories=(replace(q.memories[0],retention_reason='changed'),)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_memories)==1 and p.missing_or_changed_record_ids==('MEMORY:MEM-141-A',) and not p.full_resend_required
    if k==17:
        r=m.evaluate(req([mem()],completed=('P','P'))); return r.engine_state==m.EngineState.INVALID
    if k==18:
        r=m.evaluate(req([mem(legal=True)])); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.delete_executed,r.archive_executed,r.anonymize_executed,r.credential_revoked,r.memory_write_performed,r.memory_delete_performed,r.retention_policy_modified,r.legal_hold_enforced_externally,r.proof_log_written_externally,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==19:
        r=m.evaluate(req([mem(),mem('A',rc=m.RetentionClass.ARCHIVE_AFTER_PURPOSE),mem('R',legal=True)])); return r.delete_candidate_ids==('M',) and r.archive_candidate_ids==('A',) and r.retain_candidate_ids==('R',) and all(not x.destructive_execution_performed for x in r.plan)
    return False
class TestAL141(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL141,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
