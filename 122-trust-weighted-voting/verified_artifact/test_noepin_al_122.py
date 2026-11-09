import unittest
from dataclasses import replace
import noepin_al_122_trust_weighted_voting as m
class TestAL122(unittest.TestCase): pass

def scenario(k,j):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.weighted_consensus=='OPTION-A' and r.next_gate_candidate and r.confidence>.55
    if k==1:
        vs=tuple(replace(v,choice='SAME') for v in q.votes); r=m.evaluate(replace(q,votes=vs)); return r.decision==m.Decision.ALLOW and r.weighted_consensus=='SAME' and r.dissent==0
    if k==2:
        low=tuple(m.AgentVote(f'L{i}','LOW-MAJ',.2,.3,.3,.7,True,b,e) for i in range(8)); hi=(m.AgentVote('HI','HIGH-MIN',.99,.99,.99,.99,True,b,e),); r=m.evaluate(replace(q,votes=low+hi)); return r.weighted_consensus=='HIGH-MIN' and r.decision==m.Decision.ALLOW
    if k==3:
        vs=(m.AgentVote('A','X',.95,.95,.95,.95,True,b,e),m.AgentVote('B','Y',.95,.95,.95,.95,True,b,e)); r=m.evaluate(replace(q,votes=vs)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MAJOR_HIGH_WEIGHT_DISSENT and not r.next_gate_candidate
    if k==4:
        a=m.AgentVote('A','X',.9,.9,.9,.9,True,b,e); z=m.AgentVote('Z','Y',.9,.9,.9,.9,False,b,e); r=m.evaluate(replace(q,votes=(a,z))); return r.weighted_consensus=='X' and r.decision==m.Decision.ALLOW
    if k==5:
        p=replace(q.policy,minimum_effective_weight=10); return m.evaluate(replace(q,policy=p)).escalation==m.Escalation.INSUFFICIENT_EFFECTIVE_WEIGHT
    if k==6: return m.evaluate(replace(q,votes=q.votes+(q.votes[0],))).decision==m.Decision.HOLD
    if k==7:
        vs=(replace(q.votes[0],trust=float('nan')),)+q.votes[1:]; return m.evaluate(replace(q,votes=vs)).decision==m.Decision.HOLD
    if k==8:
        vs=(replace(q.votes[0],trust=1.2),)+q.votes[1:]; return m.evaluate(replace(q,votes=vs)).decision==m.Decision.HOLD
    if k==9:
        vs=(replace(q.votes[0],binding='BAD'),)+q.votes[1:]; return m.evaluate(replace(q,votes=vs)).decision==m.Decision.HOLD
    if k==10:
        p=replace(q.policy,consensus_threshold=1.2); return m.evaluate(replace(q,policy=p)).decision==m.Decision.HOLD
    if k==11:
        r=m.default_evaluation(); neg=(r.consensus_promoted_to_truth,r.consensus_promoted_to_permission,r.confidence_promoted_to_safety_proof,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_vote_fingerprint=st.vote_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_vote_fingerprint=st.vote_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); vs=tuple(replace(v,trust=v.trust-.01) if v.agent_id=='AGENT-C' else v for v in q.votes); st2=m.prepare_state(replace(q,votes=vs),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_votes)==1 and d.changed_votes[0].agent_id=='AGENT-C'
    if k==16:
        st=m.prepare_state(q,binding=b,state_epoch=e); vs=tuple(replace(v,evidence_quality=v.evidence_quality-.01) if v.agent_id=='AGENT-D' else v for v in q.votes); st2=m.prepare_state(replace(q,votes=vs),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('VOTE:AGENT-D',) and not sp.full_resend_required
    if k==17:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,votes=tuple(reversed(q.votes)))); return m._canon(r1)==m._canon(r2)
    if k==18:
        p=replace(q.policy,consensus_threshold=.99); r=m.evaluate(replace(q,policy=p)); return r.decision==m.Decision.HOLD and not r.next_gate_candidate
    if k==19:
        a=m.default_evaluation(); z=m.default_evaluation(); return m._canon(a)==m._canon(z) and m._fp(a)==m._fp(z)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL122,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
