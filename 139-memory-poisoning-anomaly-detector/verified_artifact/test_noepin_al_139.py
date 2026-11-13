import unittest
from dataclasses import replace
import noepin_al_139_memory_poisoning_anomaly_detector as m
B='B'; E='E'
def mem(mid='M',content='fact',category='FACT',trust=.92,purpose='PROJECT-A',prov=('P',),shift=.10,taint=(),instruction=False,critical=False,kind=m.RecordKind.MEMORY):
    return m.MemoryWriteCandidate(mid,content,category,'SRC',trust,purpose,prov,shift,taint,instruction,critical,kind,B,E)
def hist(n=5,cat='FACT'):
    return tuple(m.WriteHistoryEntry(f'H{i}',f'OLD{i}',i,'SRC',cat,B,E) for i in range(n))
def req(xs=(),hs=None,base=None): return m.DetectionRequest('R',tuple(xs),hist() if hs is None else tuple(hs),base or m.default_baseline(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.detector_state==m.DetectorState.CLEAN_CANDIDATE and r.next_gate_candidate and not r.affected_memory_ids
    if k==1:
        x=mem(category='POLICY',trust=.1,instruction=True,shift=.8); r=m.evaluate(req([x])); return r.decision==m.Decision.HOLD and r.detector_state==m.DetectorState.QUARANTINE_CANDIDATE and r.quarantine_candidate_ids==('M',)
    if k==2:
        x=mem(category='POLICY',trust=0.0,instruction=True,critical=True,shift=1.0,prov=()); base=replace(m.default_baseline(),deny_threshold=.65); r=m.evaluate(req([x],base=base)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CRITICAL_ANOMALY and not r.next_gate_candidate
    if k==3:
        base=replace(m.default_baseline(),expected_writes_per_window=2,surge_ratio=2.0); r=m.evaluate(req([mem('A'),mem('B')],hs=hist(8),base=base)); return r.decision==m.Decision.HUMAN_APPROVAL and r.escalation==m.Escalation.BULK_WRITE_WARNING
    if k==4:
        r=m.evaluate(req([mem(shift=.05,trust=.99)])); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.MEMORY_CONTINUE_CANDIDATE
    if k==5:
        x=mem(prov=(),shift=.5,trust=.55); r=m.evaluate(req([x])); return r.evidence[0].provenance_gap_risk==1.0 and r.anomaly_score>0
    if k==6:
        x=mem(purpose='OTHER',shift=.6,trust=.55); r=m.evaluate(req([x])); return r.evidence[0].purpose_mismatch_risk==1.0
    if k==7:
        r=m.evaluate(req([mem(kind=m.RecordKind.MENTION)])); return r.detector_state==m.DetectorState.MENTION_ONLY and r.next_action==m.NextAction.NO_MEMORY_CANDIDATE and not r.evidence
    if k==8:
        r=m.evaluate(req([])); return r.detector_state==m.DetectorState.EMPTY and r.next_gate_candidate
    if k==9:
        r=m.evaluate(req([mem('A'),mem('A')])); return r.detector_state==m.DetectorState.INVALID and r.decision==m.Decision.HOLD
    if k==10:
        x=replace(mem(),source_trust=float('nan')); r=m.evaluate(req([x])); return r.detector_state==m.DetectorState.INVALID
    if k==11:
        x=replace(mem(),binding='OTHER'); r=m.evaluate(req([x])); return r.detector_state==m.DetectorState.INVALID
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_new_memory_fingerprint=st.new_memory_fingerprint,current_history_fingerprint=st.history_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return m.validate_prepared_integrity(st) and r==st.result
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_new_memory_fingerprint=st.new_memory_fingerprint,current_history_fingerprint=st.history_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.decision==m.Decision.HOLD
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint='BAD',current_new_memory_fingerprint=st.new_memory_fingerprint,current_history_fingerprint=st.history_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.detector_state==m.DetectorState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.new_memories); xs[0]=replace(xs[0],source_trust=.91); q2=replace(q,new_memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_new_memories)==1 and p.missing_or_changed_record_ids==('MEMORY:MEM-139-A',) and not p.full_resend_required
    if k==16:
        x=mem(trust=.9,taint=('UNTRUSTED_EXTERNAL','POLICY_TAINT')); r=m.evaluate(req([x])); return r.evidence[0].hard_untrusted_policy and r.decision==m.Decision.HOLD
    if k==17:
        base=replace(m.default_baseline(),review_threshold=.1); x=mem(shift=.9,trust=.9); r=m.evaluate(req([x],base=base)); return r.decision in (m.Decision.HUMAN_APPROVAL,m.Decision.HOLD) and not r.source_trust_promoted_to_source_authority
    if k==18:
        r=m.evaluate(req([mem(category='POLICY',trust=.1,instruction=True)])); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.anomaly_promoted_to_fact_proof,r.anomaly_promoted_to_safety_proof,r.source_trust_promoted_to_source_authority,r.quarantine_executed,r.memory_write_performed,r.memory_delete_performed,r.policy_modified,r.identity_modified,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==19:
        base=replace(m.default_baseline(),review_threshold=.7,quarantine_threshold=.6); r=m.evaluate(req([mem()],base=base)); return r.detector_state==m.DetectorState.INVALID
    return False
class TestAL139(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL139,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
