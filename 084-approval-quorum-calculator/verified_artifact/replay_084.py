from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_084_approval_quorum_calculator import *
base=(default_proposal(),default_role_matrix(),default_approvals(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        q,m,a,p=base; mode=n%10
        if mode==0: pass
        elif mode==1: q=replace(q,risk_level=RiskLevel.LOW,blast_radius=BlastRadius.LOCAL); a=(a[0],)
        elif mode==2: a=(a[0],)
        elif mode==3: a=(a[0],replace(a[1],conflict_of_interest=True))
        elif mode==4: a=(a[0],replace(a[1],signature_verified=False))
        elif mode==5: m=tuple(replace(x,authority_group='OPS') if x.actor_id=='bob' else x for x in m)
        elif mode==6: q=replace(q,risk_level=RiskLevel.HIGH,blast_radius=BlastRadius.ORGANIZATION); a=a+(ApprovalEvidence('C',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('D',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch))
        elif mode==7: q=replace(q,risk_level=RiskLevel.CRITICAL,blast_radius=BlastRadius.GLOBAL); a=a+(ApprovalEvidence('C',q.proposal_id,'carol',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('D',q.proposal_id,'dave',True,True,False,p.binding,p.state_epoch),ApprovalEvidence('E',q.proposal_id,'erin',True,True,False,p.binding,p.state_epoch))
        elif mode==8: m=tuple(replace(x,eligible=False) if x.actor_id=='bob' else x for x in m)
        else: p=replace(p,revoked=True)
        z=evaluate(q,m,a,p)
        rows.append((n,z.decision.value,z.reasons,z.required_quorum,z.required_roles,z.effective_approval_count,z.effective_actor_ids,z.effective_authority_groups,z.satisfied_roles,z.missing_roles,tuple((x.role,x.actor_id,x.authority_group) for x in z.role_assignments),z.approval_state.value,z.next_gate_candidate,z.permission_granted,z.approval_executed,z.action_executed,z.plan_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success,z.sender_authority_inherited,z.sender_intent_inherited,z.consent_inherited))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':84,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
