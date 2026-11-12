import unittest
from dataclasses import replace
import noepin_al_135_contradiction_aware_memory_resolver as m
B='B'; E='E'
def mem(i,val='A',ctx='ROOM',src='S',trust=.8,ts=100,latest=False,critical=False,kind=m.RecordKind.MEMORY,entity='ENT',rel='setting'):
    return m.MemoryRecord(i,entity,rel,val,ctx,src,trust,ts,latest,critical,kind,'P',B,E)
def req(xs,target='ROOM',now=200,policy=None): return m.ResolutionRequest('R',tuple(xs),target,now,policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.resolution_state==m.ResolutionState.SELECTED_CANDIDATE and r.selected_memory_ids==('MEM-NEW',) and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([mem('A','x','CTX-A'),mem('B','y','CTX-B')],target='ANY')); return r.decision==m.Decision.ALLOW and r.resolution_state==m.ResolutionState.CONTEXT_PARALLEL and r.selected_memory_ids==('A','B')
    if k==2:
        r=m.evaluate(req([mem('A','x',trust=.8,ts=100),mem('B','y',trust=.8,ts=100)])); return r.decision==m.Decision.HOLD and r.resolution_state==m.ResolutionState.UNRESOLVED_CONFLICT and set(r.unresolved_memory_ids)=={'A','B'}
    if k==3:
        r=m.evaluate(req([mem('A','x',src=None,trust=.9),mem('B','y',src='S2',trust=.6)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SOURCE_UNKNOWN and 'A' in r.refresh_memory_ids
    if k==4:
        r=m.evaluate(req([mem('OLD','x',trust=.8,ts=100),mem('NEW','y',trust=.95,ts=190,latest=True)])); return r.decision==m.Decision.ALLOW and r.selected_memory_ids==('NEW',)
    if k==5:
        r=m.evaluate(req([mem('OLD','x',trust=.95,ts=100),mem('NEW','y',trust=.2,ts=190,latest=True)])); return r.decision==m.Decision.HOLD and not r.selected_memory_ids
    if k==6:
        r1=m.evaluate(req([mem('A','x',trust=.8,ts=100),mem('B','y',trust=.8,ts=100)])); r2=m.evaluate(req([mem('A','x',trust=.8,ts=100),mem('B','y',trust=.8,ts=100),mem('R','y',trust=.99,ts=195,latest=True)])); return r1.decision==m.Decision.HOLD and r2.decision==m.Decision.ALLOW and r2.selected_memory_ids==('R',)
    if k==7:
        r=m.evaluate(req([mem('M','x',kind=m.RecordKind.MENTION)])); return r.decision==m.Decision.ALLOW and r.resolution_state==m.ResolutionState.MENTION_ONLY and not r.selected_memory_ids and not r.mention_promoted_to_memory
    if k==8:
        r=m.default_evaluation(); names=('memory_promoted_to_truth','mention_promoted_to_memory','selected_promoted_to_known_fact','source_trust_promoted_to_source_authority','recency_promoted_to_truth','conflict_auto_overwritten','refresh_executed','memory_write_performed','dcsr_reconstruction_created_memory','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'); return not any(getattr(r,n) for n in names)
    if k==9:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,memories=tuple(reversed(q.memories)))))
    if k==10:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st)
    if k==11:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],source_trust=.77); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_memories)==1 and d.changed_memories[0].memory_id=='MEM-OLD'
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[0]=replace(xs[0],source_trust=.77); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('MEMORY:MEM-OLD',) and not p.full_resend_required
    if k==15:
        p=replace(m.default_policy(),decisive_margin=float('nan')); return m.evaluate(req([],policy=p)).decision==m.Decision.HOLD
    if k==16:
        r=m.evaluate(req([mem('A'),mem('A','B')])); return r.decision==m.Decision.HOLD and r.resolution_state==m.ResolutionState.INVALID
    if k==17:
        r=m.evaluate(req([mem('A','x',ts=None),mem('B','y',ts=None)])); return r.decision==m.Decision.HOLD and set(r.refresh_memory_ids)=={'A','B'}
    if k==18:
        r=m.evaluate(req([mem('A','x',critical=True),mem('B','y',critical=True)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.IMPORTANT_CONFLICT
    if k==19:
        pol=replace(m.default_policy(),unresolved_hold=False,critical_hold=False); r=m.evaluate(req([mem('A','x'),mem('B','y')],policy=pol)); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.REFRESH_REQUEST_CANDIDATE and r.resolution_state==m.ResolutionState.REFRESH_NEEDED
    return False
class TestAL135(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL135,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
