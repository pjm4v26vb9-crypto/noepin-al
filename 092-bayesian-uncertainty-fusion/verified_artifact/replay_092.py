from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_092_bayesian_uncertainty_fusion import *
base=(default_request(),default_hypotheses(),default_evidence(),default_sources(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,h,e,s,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: e=tuple(replace(x,likelihoods=(('H-SAFE',.02),('H-UNSAFE',.98))) for x in e)
        elif mode==2: r=replace(r,risk=RiskLevel.HIGH)
        elif mode==3: e=(replace(e[0],model_known=False),)+e[1:]; r=replace(r,risk=RiskLevel.HIGH)
        elif mode==4: p=replace(p,revoked=True)
        elif mode==5: e=(replace(e[0],observed=False),)+e[1:]
        elif mode==6: s=(replace(s[0],observed=False),s[1])
        elif mode==7: r=replace(r,observed=False)
        elif mode==8: e=tuple(replace(x,dependency_group='SAME') for x in e)
        else: h=(replace(h[0],prior=.05),replace(h[1],prior=.95))
        z=evaluate(r,h,e,s,p)
        rows.append((k,z.decision.value,z.reasons,z.posterior,z.target_posterior,z.credible_interval,z.interval_width,z.decision_confidence,z.effective_evidence_weight,z.dependency_penalty,z.unknown_model_count,z.next_gate_candidate,z.refutation_candidate,z.reevaluation_candidate,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.authority_promoted,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':92,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
