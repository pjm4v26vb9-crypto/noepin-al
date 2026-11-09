import unittest
from dataclasses import replace
import noepin_al_127_delegation_auction_optimizer as m

class TestAL127(unittest.TestCase): pass

def bid(a='A',caps=('x',),auth=('s',),cost=.3,risk=.2,trust=.8,av=.9,b='B',e='E'):
    return m.AgentBid(a,caps,auth,cost,risk,trust,av,b,e)
def task(caps=('x',),auth=('s',),maxrisk=.4,minav=.7,b='B',e='E'):
    return m.DelegationTask('T',caps,auth,maxrisk,minav,b,e)
def req(bids,t=None,p=None,b='B',e='E'):
    return m.AuctionRequest('R',t or task(b=b,e=e),tuple(bids),p or m.default_policy(),b,e)

def scenario(k,variant):
    p=m.default_policy()
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.DELEGATION_ASSIGNMENT_CANDIDATE and r.winner_candidate=='AGENT-A' and r.reserve_candidate=='AGENT-B' and r.next_gate_candidate
    if k==1:
        a=bid('CHEAP',cost=.01,risk=.8); b=bid('SAFE',cost=.5,risk=.2); r=m.evaluate(req([a,b])); return r.winner_candidate=='SAFE' and 'CHEAP' not in r.feasible_agent_ids
    if k==2:
        a=bid('NO',caps=('y',)); b=bid('YES',caps=('x','y')); r=m.evaluate(req([a,b])); return r.winner_candidate=='YES'
    if k==3:
        a=bid('LOWTRUST',cost=.2,trust=.55); b=bid('HITRUST',cost=.2,trust=.9); r=m.evaluate(req([a,b])); return r.winner_candidate=='HITRUST'
    if k==4:
        r=m.evaluate(req([bid('A',caps=('y',)),bid('B',caps=('z',))])); return r.decision==m.Decision.HOLD and r.auction_state==m.AuctionState.NO_FEASIBLE_AGENT and r.escalation==m.Escalation.CAPABILITY_SHORTFALL
    if k==5:
        r=m.evaluate(req([bid('A',risk=.8),bid('B',risk=.9)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.RISK_EXCEEDED
    if k==6:
        r=m.evaluate(req([bid('A',av=.2),bid('B',av=.4)])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AVAILABILITY_SHORTFALL
    if k==7:
        r=m.evaluate(req([bid('A',auth=('z',)),bid('B',auth=())])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AUTHORITY_SCOPE_SHORTFALL
    if k==8:
        a=bid('A',cost=.2,risk=.2,trust=.8,av=.9); b=bid('B',cost=.2,risk=.2,trust=.8,av=.9); r=m.evaluate(req([b,a])); return r.winner_candidate=='A' and r.reserve_candidate=='B'
    if k==9:
        pp=replace(p,reserve_required=True); r=m.evaluate(req([bid('A')],p=pp)); return r.decision==m.Decision.HOLD and r.winner_candidate is None
    if k==10:
        r=m.evaluate(req([bid('A'),bid('A')])); return r.auction_state==m.AuctionState.INVALID
    if k==11:
        r=m.default_evaluation(); neg=(r.winner_promoted_to_permission,r.assignment_executed,r.reserve_promoted_to_authority,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); return m.validate_prepared_integrity(st)
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_bid_fingerprint=st.bid_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); rr=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_bid_fingerprint=st.bid_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.decision==m.Decision.HOLD
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); bs=list(q.bids); bs[-1]=replace(bs[-1],cost=bs[-1].cost+.01); q2=replace(q,bids=tuple(bs)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_bids)==1 and d.changed_bids[0].agent_id=='AGENT-D'
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,binding=q.binding,state_epoch=q.state_epoch); q2=replace(q,bids=q.bids+(replace(q.bids[0],agent_id='AGENT-E'),)); st2=m.prepare_state(q2,binding=q2.binding,state_epoch=q2.state_epoch); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_bid_ids==('BID:AGENT-E',) and not sp.full_resend_required
    if k==17:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,bids=tuple(reversed(q.bids)))))
    if k==18:
        x=replace(bid('A'),cost=float('nan')); return m.evaluate(req([x])).auction_state==m.AuctionState.INVALID
    if k==19:
        x=replace(task(),max_risk=1.2); return m.evaluate(req([bid('A')],t=x)).auction_state==m.AuctionState.INVALID
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL127,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
