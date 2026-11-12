import unittest
from dataclasses import replace
import noepin_al_138_semantic_memory_deduplicator as m
B='B'; E='E'
def mem(mid='M',sem='S',claim='claim',scope='A',time='T',quals=('Q',),crit=(('k','v'),),score=.98,prov=('P',),trust=.9,kind=m.RecordKind.MEMORY,known=True):
    return m.MemoryClaim(mid,sem,claim,scope,time,quals,crit,score,prov,trust,kind,known,B,E)
def req(xs=(),policy=None): return m.DedupRequest('R',tuple(xs),policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CANONICAL_MEMORY_CANDIDATE and r.dedup_state==m.DedupState.DEDUPLICATION_CANDIDATE and len(r.merged_links)==1
    if k==1:
        a=mem('A',claim='same meaning A',prov=('P1',)); b=mem('B',claim='same meaning B',prov=('P2',)); r=m.evaluate(req([a,b])); return len(r.canonical_memories)==1 and r.merged_links[0].merged_memory_id in ('A','B') and set(r.canonical_memories[0].provenance_ids)=={'P1','P2'}
    if k==2:
        a=mem('A',crit=(('dose','10'),)); b=mem('B',crit=(('dose','20'),)); r=m.evaluate(req([a,b])); return r.decision==m.Decision.ALLOW and not r.merged_links and any(d.reason=='CRITICAL_DIFFERENCE' for d in r.preserved_differences)
    if k==3:
        a=mem('A',time='T1'); b=mem('B',time='T2'); r=m.evaluate(req([a,b])); return not r.merged_links and any(d.reason=='TIME_DIFFERENCE' for d in r.preserved_differences)
    if k==4:
        a=mem('A',scope='A'); b=mem('B',scope='B'); r=m.evaluate(req([a,b])); return not r.merged_links and any(d.reason=='SCOPE_DIFFERENCE' for d in r.preserved_differences)
    if k==5:
        a=mem('A',score=.85,known=False); b=mem('B',score=.86,known=True); r=m.evaluate(req([a,b])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DIFFERENCE_IMPORTANCE_UNKNOWN and not r.next_gate_candidate
    if k==6:
        a=mem('A',score=.85,known=True); b=mem('B',score=.86,known=True); r=m.evaluate(req([a,b])); return r.decision==m.Decision.ALLOW and not r.merged_links and any(d.reason=='APPROXIMATE_NOT_SAFE_EQUIVALENT' for d in r.preserved_differences)
    if k==7:
        a=mem('A',score=.4); b=mem('B',score=.4); r=m.evaluate(req([a,b])); return r.dedup_state==m.DedupState.PRESERVED_SEPARATE and any(d.reason=='SEMANTIC_DISTANCE' for d in r.preserved_differences)
    if k==8:
        r=m.evaluate(req([mem(kind=m.RecordKind.MENTION)])); return r.dedup_state==m.DedupState.MENTION_ONLY and not r.canonical_memories
    if k==9:
        r=m.evaluate(req([])); return r.dedup_state==m.DedupState.EMPTY and r.next_gate_candidate
    if k==10:
        a=mem('A','S1'); b=mem('B','S2'); r=m.evaluate(req([a,b])); return len(r.canonical_memories)==2 and not r.merged_links
    if k==11:
        a=mem('A',quals=('Q1',)); b=mem('B',quals=('Q2',)); r=m.evaluate(req([a,b])); return any(d.reason=='QUALIFIER_DIFFERENCE' for d in r.preserved_differences)
    if k==12:
        a=mem('A',trust=.4); b=mem('B',trust=.9); r=m.evaluate(req([a,b])); return not r.merged_links and len(r.canonical_memories)==2
    if k==13:
        a=mem('B',prov=('P2',),trust=.9); b=mem('A',prov=('P1',),trust=.95); r=m.evaluate(req([a,b])); return r.canonical_memories[0].canonical_memory_id=='A' and r.canonical_memories[0].source_memory_ids==('A','B')
    if k==14:
        r=m.default_evaluation(); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.semantic_similarity_promoted_to_fact_identity,r.canonical_memory_written,r.destructive_merge_executed,r.provenance_dropped,r.difference_suppressed,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st) and m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==17:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],trust=.88); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_memories)==1 and p.missing_or_changed_record_ids==('MEMORY:MEM-1',) and not p.full_resend_required
    if k==18:
        p=replace(m.default_policy(),min_merge_equivalence=float('nan')); return m.evaluate(req([mem()],policy=p)).decision==m.Decision.HOLD
    if k==19:
        r=m.evaluate(req([mem('A'),mem('A')])); return r.decision==m.Decision.HOLD and r.dedup_state==m.DedupState.INVALID
    return False
class TestAL138(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL138,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
