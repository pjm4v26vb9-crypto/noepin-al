import unittest
from dataclasses import replace
import noepin_al_140_knowledge_refresh_scheduler as m
B='B'; E='E'
def item(k='K',importance=.8,volatility=.2,usage=.5,cost=.2,age=100,ttl=1000,critical=False,status=m.RefreshStatus.NOT_ATTEMPTED):
    return m.KnowledgeItem(k,'SRC','PROJECT-A',(f'P-{k}',),importance,volatility,usage,cost,age,ttl,critical,status,B,E)
def req(xs=(),policy=None): return m.SchedulerRequest('R',tuple(xs),policy or m.default_policy(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.scheduler_state==m.SchedulerState.CURRENT_CANDIDATE and r.next_gate_candidate and not r.refresh_queue
    if k==1:
        hi=m._evidence(item('H',volatility=.95,age=300,ttl=1000),m.default_policy()); lo=m._evidence(item('L',volatility=.05,age=300,ttl=1000),m.default_policy()); return hi.computed_interval_seconds<lo.computed_interval_seconds
    if k==2:
        p=m.default_policy(); e=m._evidence(item(importance=.1,cost=.95,volatility=0,usage=0,ttl=1000),p); base=m._evidence(item(importance=.9,cost=.05,volatility=0,usage=0,ttl=1000),p); return e.computed_interval_seconds>base.computed_interval_seconds
    if k==3:
        r=m.evaluate(req([item(age=1200,ttl=1000,critical=True)])); return r.decision==m.Decision.HOLD and r.next_action==m.NextAction.REFRESH_REQUIRED_BEFORE_USE_CANDIDATE and r.refresh_queue[0].critical
    if k==4:
        r=m.evaluate(req([item(age=1200,ttl=1000,critical=True,status=m.RefreshStatus.FAILED)])); return r.decision==m.Decision.HOLD and r.scheduler_state==m.SchedulerState.CRITICAL_STALE_HOLD_CANDIDATE and r.stale_knowledge_ids==('K',)
    if k==5:
        r=m.evaluate(req([item(age=1200,ttl=1000,status=m.RefreshStatus.FAILED)])); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.REFRESH_QUEUE_CANDIDATE and r.stale_knowledge_ids==('K',)
    if k==6:
        r=m.evaluate(req([item(age=5000,ttl=1000,status=m.RefreshStatus.SUCCEEDED)])); return r.scheduler_state==m.SchedulerState.CURRENT_CANDIDATE and r.evidence[0].effective_age_seconds==0
    if k==7:
        r=m.evaluate(req([])); return r.scheduler_state==m.SchedulerState.EMPTY and r.next_action==m.NextAction.NO_KNOWLEDGE_CANDIDATE
    if k==8:
        r=m.evaluate(req([item('A'),item('A')])); return r.scheduler_state==m.SchedulerState.INVALID
    if k==9:
        r=m.evaluate(req([replace(item(),volatility=float('nan'))])); return r.scheduler_state==m.SchedulerState.INVALID
    if k==10:
        r=m.evaluate(req([replace(item(),binding='OTHER')])); return r.scheduler_state==m.SchedulerState.INVALID
    if k==11:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_items_fingerprint=st.items_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return m.validate_prepared_integrity(st) and r==st.result
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_items_fingerprint=st.items_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.scheduler_state==m.SchedulerState.INVALID
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint='BAD',current_items_fingerprint=st.items_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.scheduler_state==m.SchedulerState.INVALID
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,items=(replace(q.items[0],age_seconds=121.0),)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_items)==1 and p.missing_or_changed_record_ids==('KNOWLEDGE:KN-140-A',) and not p.full_resend_required
    if k==15:
        r=m.evaluate(req([item('N',age=1500,ttl=1000,critical=False),item('C',age=1500,ttl=1000,critical=True)])); return r.refresh_queue[0].knowledge_id=='C'
    if k==16:
        r=m.evaluate(req([item(age=700,ttl=1000,volatility=.9)])); return r.next_refresh_time_seconds is not None and r.next_refresh_time_seconds>=0
    if k==17:
        r=m.evaluate(req([item(ttl=0)])); return r.scheduler_state==m.SchedulerState.INVALID
    if k==18:
        r=m.evaluate(req([item(age=1200,ttl=1000,critical=True,status=m.RefreshStatus.FAILED)])); neg=(r.freshness_promoted_to_truth,r.knowledge_promoted_to_world_truth,r.refresh_candidate_executed,r.external_retrieval_executed,r.timestamp_mutated,r.knowledge_write_performed,r.knowledge_delete_performed,r.source_promoted_to_authority,r.dcsr_reconstruction_created_knowledge,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==19:
        r=m.evaluate(req([item(age=900,ttl=1000,volatility=.9)])); return not r.external_retrieval_executed and not r.knowledge_write_performed and not r.timestamp_mutated
    return False
class TestAL140(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL140,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
