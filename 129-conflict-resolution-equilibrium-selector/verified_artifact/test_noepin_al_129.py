import unittest
from dataclasses import replace
import noepin_al_129_conflict_resolution_equilibrium_selector as m
B='B'; E='E'
def au(a,u): return m.AgentUtility(a,u)
def prop(i,vals,r=.1,g=.9,hard=True,avail=True,who='A'):
    return m.Proposal(i,who,tuple(au(a,u) for a,u in vals),r,g,hard,avail,B,E)
def req(props,known=True,minu=.2,risk=.5,pol=None):
    return m.EquilibriumRequest('R',tuple(props),m.SharedGoal('G',known,minu,risk,B,E),pol or m.default_policy(),B,E)

def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.STABLE_CANDIDATE_CANDIDATE and r.stable_candidate=='P-BALANCED'
    if k==1:
        q=req([prop('P1',[('A',.8),('B',.8)],.1,.95),prop('P2',[('A',.6),('B',.6)],.2,.8)]); r=m.evaluate(q); return r.stable_candidate=='P1' and r.equilibrium_state==m.EquilibriumState.STABLE
    if k==2:
        q=req([prop('SAFE',[('A',.7),('B',.7)],.2,.85),prop('CHEAP_UNSAFE',[('A',.95),('B',.95)],.9,.95)],risk=.4); return m.evaluate(q).stable_candidate=='SAFE'
    if k==3:
        q=req([prop('BAD_CAP',[('A',.9),('B',.9)],hard=False)]); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.equilibrium_state==m.EquilibriumState.NO_SAFE_CANDIDATE
    if k==4:
        p=replace(m.default_policy(),material_tradeoff_gap=.10); q=req([prop('P1',[('A',.8),('B',.72)],.1,.9),prop('P2',[('A',.72),('B',.8)],.1,.9)],pol=p); r=m.evaluate(q); return r.decision==m.Decision.HUMAN_APPROVAL and r.equilibrium_state==m.EquilibriumState.MULTIPLE_TRADEOFFS
    if k==5:
        q=req([prop('MONO',[('A',.98),('B',.40)],.1,.9),prop('BAL',[('A',.70),('B',.70)],.1,.88)],minu=.35); r=m.evaluate(q); return r.stable_candidate=='BAL' or r.decision==m.Decision.HUMAN_APPROVAL
    if k==6:
        q=req([prop('P1',[('A',.8),('B',.8)])],known=False); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.equilibrium_state==m.EquilibriumState.SHARED_GOAL_UNKNOWN
    if k==7:
        q=req([prop('P1',[('A',.8),('B',.8)],avail=False)]); return m.evaluate(q).equilibrium_state==m.EquilibriumState.NO_SAFE_CANDIDATE
    if k==8:
        q=req([prop('P1',[('A',.8),('B',.1)])],minu=.4); return m.evaluate(q).decision==m.Decision.HOLD
    if k==9:
        q=req([prop('P1',[('A',.8),('B',.8)]),prop('P1',[('A',.7),('B',.7)])]); return m.evaluate(q).equilibrium_state==m.EquilibriumState.INVALID
    if k==10:
        q=req([prop('P1',[('A',.8),('A',.7)])]); return m.evaluate(q).equilibrium_state==m.EquilibriumState.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.stable_candidate_promoted_to_permission,r.equilibrium_promoted_to_truth,r.tradeoff_promoted_to_truth,r.human_approval_promoted_to_execution,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_proposal_fingerprint=st.proposal_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_proposal_fingerprint=st.proposal_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.decision==m.Decision.HOLD
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); ps=list(q.proposals); ps[0]=replace(ps[0],risk=.15); q2=replace(q,proposals=tuple(ps)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_proposals)==1 and d.changed_proposals[0].proposal_id=='P-BALANCED'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); ps=list(q.proposals); ps[-1]=replace(ps[-1],shared_goal_alignment=.82); q2=replace(q,proposals=tuple(ps)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('PROPOSAL:P-B-FAVOR',) and not sp.full_resend_required
    if k==17:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,proposals=tuple(reversed(q.proposals)))))
    if k==18:
        q=req([prop('P1',[('A',float('nan')),('B',.8)])]); return m.evaluate(q).equilibrium_state==m.EquilibriumState.INVALID
    if k==19:
        p=replace(m.default_policy(),risk_weight=2.0); q=req([prop('P1',[('A',.8),('B',.8)])],pol=p); return m.evaluate(q).equilibrium_state==m.EquilibriumState.INVALID
    return False
class TestAL129(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL129,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
