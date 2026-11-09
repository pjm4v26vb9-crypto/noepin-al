import unittest
from dataclasses import replace
import noepin_al_128_responsibility_contribution_allocator as m
B='B'; E='E'
def node(i,a='A',role='ACTION',cf=.8): return m.DecisionNode(i,a,role,cf,B,E)
def edge(s,t,w=.9): return m.CausalEdge(s,t,w,B,E)
def req(nodes,edges,out='O',risk='LOW',pol=None,observed=True):
    if not any(n.node_id==out for n in nodes): nodes=list(nodes)+[node(out,None,'OUTCOME',None)]
    return m.AttributionRequest('R',tuple(nodes),tuple(edges),m.OutcomeSpec(out,observed,risk,B,E),pol or m.default_policy(),B,E)

def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.RESPONSIBILITY_CONTRIBUTION_CANDIDATE and r.contribution_scores[0].agent_id=='AGENT-A'
    if k==1:
        q=req([node('A','A','ACTION',1.0)],[edge('A','O',1.0)]); r=m.evaluate(q); return r.critical_contributors==('A',) and abs(r.contribution_scores[0].contribution_score-1)<1e-12
    if k==2:
        q=req([node('A','A','ACTION',.9),node('B','B','ACTION',.9)],[edge('A','O',.9),edge('B','O',.9)]); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and len(r.contribution_scores)==2 and abs(r.contribution_scores[0].contribution_score-r.contribution_scores[1].contribution_score)<1e-12
    if k==3:
        q=req([node('A','A','ACTION',.7),node('B','B','ACTION',.7),node('C','C','ACTION',.7)],[edge('A','O',.8),edge('B','O',.8),edge('C','O',.8)]); r=m.evaluate(q); return len(r.contribution_scores)==3 and not r.critical_contributors
    if k==4:
        q=req([node('A','A','ACTION',None)],[m.CausalEdge('A','O',None,B,E)],risk='HIGH'); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.attribution_state==m.AttributionState.INDETERMINATE
    if k==5:
        q=req([node('P','A','PROPOSAL',.8),node('V','B','APPROVAL',.4)],[edge('P','V',.9),edge('V','O',.9)]); r=m.evaluate(q); d={x.agent_id:x.contribution_score for x in r.contribution_scores}; return d['A']>d['B']
    if k==6:
        q=req([node('A','A','ACTION',.9)],[edge('A','O',.9)],observed=False); return m.evaluate(q).escalation==m.Escalation.OUTCOME_UNOBSERVED
    if k==7:
        q=req([node('A','A','ACTION',.9)],[edge('A','O',.9),edge('O','A',.9)]); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    if k==8:
        q=req([node('A','A','ACTION',.9)],[edge('X','O',.9)]); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    if k==9:
        q=req([node('A','A','ACTION',.9),node('A','B','ACTION',.8)],[edge('A','O',.9)]); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    if k==10:
        q=req([node('A','A','ACTION',.9)],[edge('A','O',.9),edge('A','O',.8)]); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.contribution_promoted_to_liability,r.critical_contributor_promoted_to_sole_responsibility,r.trust_update_executed,r.penalty_executed,r.authority_restriction_executed,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_graph_fingerprint=st.graph_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_graph_fingerprint=st.graph_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.decision==m.Decision.HOLD
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); ns=list(q.nodes); ns[0]=replace(ns[0],counterfactual_effect=.76); q2=replace(q,nodes=tuple(ns)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_nodes)==1 and d.changed_nodes[0].node_id=='PROPOSAL-A'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); es=list(q.edges); es[-1]=replace(es[-1],strength=.21); q2=replace(q,edges=tuple(es)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('EDGE:REVIEW-C->ACTION-A',) and not sp.full_resend_required
    if k==17:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,nodes=tuple(reversed(q.nodes)),edges=tuple(reversed(q.edges)))))
    if k==18:
        q=req([node('A','A','ACTION',float('nan'))],[edge('A','O',.9)]); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    if k==19:
        p=replace(m.default_policy(),min_causal_coverage=1.2); q=req([node('A','A','ACTION',.9)],[edge('A','O',.9)],pol=p); return m.evaluate(q).attribution_state==m.AttributionState.INVALID
    return False
class TestAL128(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL128,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
