from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_083_reversible_first_planner import *
base=(default_goal(),default_actions(),default_approvals(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        g,a,e,p=base; m=n%10; b,ep=p.binding,p.state_epoch
        if m==0: pass
        elif m==1: a=(CandidateAction('I',g.goal_id,1,0,1,Risk.MEDIUM,None,True,True,None,b,ep),)
        elif m==2: a=(CandidateAction('H',g.goal_id,1,None,1,Risk.HIGH,'R',False,True,None,b,ep),)
        elif m==3: a=(CandidateAction('R',g.goal_id,1,.95,1,Risk.HIGH,'RB',False,True,None,b,ep),)
        elif m==4: a=(CandidateAction('C',g.goal_id,1,.95,1,Risk.CRITICAL,'RB',False,True,None,b,ep),)
        elif m==5: a=(CandidateAction('L',g.goal_id,1,.2,1,Risk.LOW,'RB',False,True,None,b,ep),)
        elif m==6: a=(CandidateAction('L',g.goal_id,1,.2,1,Risk.LOW,'RB',False,True,'EV',b,ep),); e=(ApprovalEvidence('EV','L',True,True,b,ep),)
        elif m==7: g=replace(g,min_achievement=.99); a=(CandidateAction('A',g.goal_id,.95,.99,1,Risk.LOW,'R',False,True,None,b,ep),)
        elif m==8: a=(CandidateAction('A',g.goal_id,1,.8,3,Risk.LOW,'R',False,True,None,b,ep),CandidateAction('B',g.goal_id,1,.9,5,Risk.LOW,'R2',False,True,None,b,ep))
        else: p=replace(p,revoked=True)
        z=evaluate(g,a,e,p)
        rows.append((n,z.decision.value,z.reasons,tuple((x.action_id,x.reversibility_score,x.risk.value,x.cost,x.requires_human_approval,x.approval_evidence_valid) for x in z.ordered_plan),z.chosen_action_id,z.rollback_option,z.next_gate_candidate,z.human_approval_candidate,z.permission_granted,z.action_executed,z.rollback_executed,z.plan_committed,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':83,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
