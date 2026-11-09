import unittest
from dataclasses import replace
import noepin_al_123_byzantine_resilient_agent_quorum as m
class TestAL123(unittest.TestCase): pass

def scenario(k,j):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.quorum_choice=='APPROVE' and r.agreeing_independent_domains==3 and r.required_independent_domains==3 and r.next_gate_candidate
    if k==1:
        ds=q.decisions+(m.AgentDecision('AGENT-X','DOMAIN-X','APPROVE',.9,.9,'SIG-X',False,b,e),); r=m.evaluate(replace(q,decisions=ds)); return r.decision==m.Decision.ALLOW and any('INVALID_SIGNATURE' in x for x in r.fault_suspects)
    if k==2:
        dup=tuple(m.AgentDecision(f'DUP-{i}','DOMAIN-A','APPROVE',.9,.9,f'S{i}',True,b,e) for i in range(10)); ds=dup+(q.decisions[1],q.decisions[3]); r=m.evaluate(replace(q,decisions=ds)); return r.decision==m.Decision.HOLD and r.eligible_independent_domains==3 and r.agreeing_independent_domains<3
    if k==3:
        ds=tuple(replace(d,signature_valid=False) if d.agent_id in {'AGENT-A','AGENT-B'} else d for d in q.decisions); r=m.evaluate(replace(q,decisions=ds)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.INVALID_SIGNATURES
    if k==4:
        r=m.evaluate(replace(q,decisions=q.decisions[:2])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.INSUFFICIENT_INDEPENDENT_QUORUM
    if k==5:
        extra=m.AgentDecision('AGENT-E','DOMAIN-A','REJECT',.9,.9,'SIG-E',True,b,e); r=m.evaluate(replace(q,decisions=q.decisions+(extra,))); return r.decision==m.Decision.HOLD and any('EQUIVOCATION' in x for x in r.fault_suspects)
    if k==6:
        return m.evaluate(replace(q,policy=replace(q.policy,fault_bound=-1))).decision==m.Decision.HOLD
    if k==7: return m.evaluate(replace(q,decisions=())).decision==m.Decision.HOLD
    if k==8: return m.evaluate(replace(q,decisions=q.decisions+(q.decisions[0],))).decision==m.Decision.HOLD
    if k==9:
        ds=(replace(q.decisions[0],binding='BAD'),)+q.decisions[1:]; return m.evaluate(replace(q,decisions=ds)).decision==m.Decision.HOLD
    if k==10:
        ds=(replace(q.decisions[0],signature_id=''),)+q.decisions[1:]; return m.evaluate(replace(q,decisions=ds)).decision==m.Decision.HOLD
    if k==11:
        ds=tuple(replace(d,trust=.1) if d.agent_id in {'AGENT-A','AGENT-B'} else d for d in q.decisions); return m.evaluate(replace(q,decisions=ds)).decision==m.Decision.HOLD
    if k==12:
        r=m.default_evaluation(); neg=(r.quorum_promoted_to_truth,r.quorum_promoted_to_permission,r.signature_evidence_promoted_to_identity_authority,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); ds=tuple(replace(d,evidence_quality=d.evidence_quality-.01) if d.agent_id=='AGENT-C' else d for d in q.decisions); st2=m.prepare_state(replace(q,decisions=ds),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_decisions)==1 and d.changed_decisions[0].agent_id=='AGENT-C'
    if k==17:
        st=m.prepare_state(q,binding=b,state_epoch=e); ds=tuple(replace(d,trust=d.trust-.01) if d.agent_id=='AGENT-D' else d for d in q.decisions); st2=m.prepare_state(replace(q,decisions=ds),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('DECISION:AGENT-D',) and not sp.full_resend_required
    if k==18:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,decisions=tuple(reversed(q.decisions)))); return m._canon(r1)==m._canon(r2)
    if k==19:
        # With f=0, independent one-domain quorums for different choices conflict and must HOLD.
        p=replace(q.policy,fault_bound=0); ds=(q.decisions[0],q.decisions[3]); r=m.evaluate(replace(q,decisions=ds,policy=p)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONFLICTING_QUORUM
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL123,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
