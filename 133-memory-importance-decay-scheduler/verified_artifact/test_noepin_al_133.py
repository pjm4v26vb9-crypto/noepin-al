import unittest, math
from dataclasses import replace
import noepin_al_133_memory_importance_decay_scheduler as m
B='T'; E='E'
def mem(i='M',**kw):
    d=dict(memory_id=i,source_id='S',purpose_id='P',created_at=100,last_used_at=100,usage_count=0,importance=.5,freshness=.5,trust=.8,purpose_active=True,legal_hold=False,safety_critical=False,deletion_forbidden=False,kind=m.RecordKind.MEMORY,binding=B,state_epoch=E); d.update(kw); return m.MemoryMetadata(**d)
def req(xs,policy=None): return m.DecayRequest('R',tuple(xs),policy or replace(m.default_policy(),now=1000),B,E)
def cand(r,i): return next(x for x in r.candidates if x.memory_id==i)
def scenario(k,v):
    if k==0: return cand(m.default_evaluation(),'MEM-IMPORTANT').state==m.RetentionState.PROTECTED
    if k==1:
        r=m.evaluate(req([mem('L',importance=.25,freshness=.15,trust=.7)])); return cand(r,'L').state in (m.RetentionState.ARCHIVE,m.RetentionState.DELETE)
    if k==2:
        r=m.evaluate(req([mem('D',importance=.01,freshness=.01,trust=.5,purpose_active=False)])); return cand(r,'D').state==m.RetentionState.DELETE and not r.delete_executed
    if k==3:
        r=m.evaluate(req([mem('F',usage_count=20,last_used_at=100,importance=.8)])); return cand(r,'F').state==m.RetentionState.REFRESH
    if k==4:
        r=m.evaluate(req([mem('H',importance=0,freshness=0,trust=0,legal_hold=True)])); return cand(r,'H').state==m.RetentionState.PROTECTED and cand(r,'H').escalation==m.Escalation.LEGAL_HOLD
    if k==5:
        r=m.evaluate(req([mem('S',importance=0,freshness=0,trust=0,safety_critical=True)])); return cand(r,'S').state==m.RetentionState.PROTECTED
    if k==6:
        r=m.evaluate(req([mem('N',importance=0,freshness=0,trust=0,deletion_forbidden=True)])); return cand(r,'N').state==m.RetentionState.PROTECTED
    if k==7:
        r=m.evaluate(req([mem('X',kind=m.RecordKind.MENTION)])); return cand(r,'X').state==m.RetentionState.MENTION_ONLY and not r.mention_promoted_to_memory
    if k==8:
        a=cand(m.evaluate(req([mem('A',purpose_active=True)])),'A'); b=cand(m.evaluate(req([mem('A',purpose_active=False)])),'A'); return b.retention_priority<=a.retention_priority
    if k==9:
        p=replace(m.default_policy(),now=1000,min_trust=.9); r=m.evaluate(req([mem('T',trust=.2)],p)); return cand(r,'T').state==m.RetentionState.REFRESH
    if k==10:
        r=m.evaluate(req([mem('I',created_at=1100)])); return r.decision==m.Decision.HOLD
    if k==11:
        r=m.default_evaluation(); neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.delete_executed,r.archive_executed,r.refresh_executed,r.memory_write_performed,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_memory_fingerprint=st.memory_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); xs=list(q.memories); xs[1]=replace(xs[1],importance=.11); q2=replace(q,memories=tuple(xs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_memories)==1 and d.changed_memories[0].memory_id=='MEM-LOW'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,policy=replace(q.policy,archive_threshold=.45)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('RETENTION_POLICY',) and not p.full_resend_required
    if k==17:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,memories=tuple(reversed(q.memories)))))
    if k==18:
        p=replace(m.default_policy(),archive_threshold=float('nan')); return m.evaluate(req([],p)).decision==m.Decision.HOLD
    if k==19:
        p=replace(m.default_policy(),now=1000,delete_threshold=.9,archive_threshold=.95); r=m.evaluate(req([mem('P',importance=0,legal_hold=True)],p)); return cand(r,'P').state==m.RetentionState.PROTECTED and not r.delete_executed
    return False
class TestAL133(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL133,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
