import unittest
from dataclasses import replace
import noepin_al_126_strategic_manipulation_detector as m

class TestAL126(unittest.TestCase): pass

def rec(cid='X',aid='A',claimed=.8,observed=.8,tol=.05,interest=.1,direction=1,evidence=('E1',),expected=('E1',),omitted=(),prior=0,b='B',e='E'):
    return m.ClaimAuditRecord(cid,aid,'M',claimed,observed,tol,interest,direction,evidence,expected,omitted,prior,b,e)
def req(records,policy=None,b='B',e='E'):
    return m.ManipulationRequest('R',tuple(records),policy or m.default_policy(),b,e)

def scenario(k,variant):
    b='B'; e='E'; p=m.default_policy()
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.NORMAL_WEIGHT_CANDIDATE and r.manipulation_class==m.ManipulationClass.NO_SIGNAL and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([rec(claimed=.25,observed=.20,tol=.01)])); return r.manipulation_class==m.ManipulationClass.CALIBRATION_ONLY and r.next_action==m.NextAction.CALIBRATION_CANDIDATE
    if k==2:
        r=m.evaluate(req([rec(claimed=.8,observed=.2,tol=.02,interest=.9,direction=1)])); return r.decision==m.Decision.HOLD and r.manipulation_class==m.ManipulationClass.HIGH_RISK and r.next_action==m.NextAction.AUTHORITY_RESTRICTION_CANDIDATE
    if k==3:
        x=rec(claimed=.45,observed=.20,tol=.02,interest=.2,direction=1,expected=('E1','E2','E3','E4'),omitted=('E2','E3'))
        r=m.evaluate(req([x])); return r.manipulation_class==m.ManipulationClass.SUSPECT and r.next_action==m.NextAction.WEIGHT_REDUCTION_CANDIDATE
    if k==4:
        x=rec(claimed=.45,observed=.20,tol=.02,interest=.8,direction=1,expected=('E1','E2','E3','E4'),omitted=('E2','E3'),prior=4)
        r=m.evaluate(req([x])); return r.manipulation_class==m.ManipulationClass.HIGH_RISK and 'A' in r.high_risk_agent_ids
    if k==5:
        x=rec(observed=None); r=m.evaluate(req([x])); return r.manipulation_class==m.ManipulationClass.UNVERIFIABLE and r.next_action==m.NextAction.WEIGHT_REDUCTION_CANDIDATE and r.unverifiable_claim_ids==('X',)
    if k==6:
        x=rec(claimed=.2,observed=.8,tol=.02,interest=.9,direction=1); r=m.evaluate(req([x])); return r.manipulation_class in (m.ManipulationClass.CALIBRATION_ONLY,m.ManipulationClass.SUSPECT) and r.decision==m.Decision.ALLOW
    if k==7:
        x=rec(expected=('E1','E2'),omitted=('E3',)); return m.evaluate(req([x])).manipulation_class==m.ManipulationClass.INVALID
    if k==8:
        x=rec(cid='X'); y=rec(cid='X',aid='B'); return m.evaluate(req([x,y])).manipulation_class==m.ManipulationClass.INVALID
    if k==9:
        x=replace(rec(),self_interest_score=1.2); return m.evaluate(req([x])).manipulation_class==m.ManipulationClass.INVALID
    if k==10:
        x=replace(rec(),claimed_value=float('nan')); return m.evaluate(req([x])).manipulation_class==m.ManipulationClass.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.manipulation_promoted_to_malicious_intent,r.mismatch_promoted_to_intent_proof,r.trust_adjustment_executed,r.authority_restriction_executed,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_record_fingerprint=st.record_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_record_fingerprint=st.record_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.decision==m.Decision.HOLD
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rs=list(q.records); rs[-1]=replace(rs[-1],claimed_value=rs[-1].claimed_value+.01); q2=replace(q,records=tuple(rs)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_records)==1 and d.changed_records[0].claim_id=='C3'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rs=q.records+(replace(q.records[0],claim_id='C4'),); q2=replace(q,records=rs); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('CLAIM:C4',) and not sp.full_resend_required
    if k==17:
        q=m.default_request(); r1=m.evaluate(q); r2=m.evaluate(replace(q,records=tuple(reversed(q.records)))); return m._canon(r1)==m._canon(r2)
    if k==18:
        x=rec(claimed=.65,observed=.2,tol=.01,interest=.9,direction=1,prior=4); y=rec(cid='Y',aid='B',claimed=.4,observed=.4); r=m.evaluate(req([x,y])); aa={a.agent_id:a for a in r.trust_adjustments}; return aa['A'].authority_restriction_candidate and aa['A'].vote_weight_cap==p.high_risk_vote_weight_cap and aa['B'].manipulation_class==m.ManipulationClass.NO_SIGNAL
    if k==19:
        x=rec(claimed=.52,observed=.2,tol=.01,interest=.1,direction=1,prior=4); r=m.evaluate(req([x])); return r.manipulation_class==m.ManipulationClass.CALIBRATION_ONLY and not r.high_risk_agent_ids
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL126,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
