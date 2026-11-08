from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_093_evidence_independence_estimator import *
base=(default_request(),default_evidence(),default_edges(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,e,g,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: e=tuple(replace(x,source_id='SAME') for x in e)
        elif mode==2: e=tuple(replace(x,model_id='SAME') for x in e)
        elif mode==3: e=(replace(e[0],lineage_known=False),)+e[1:]; r=replace(r,risk=RiskLevel.HIGH)
        elif mode==4: p=replace(p,revoked=True)
        elif mode==5: e=(replace(e[0],observed=False),)+e[1:]
        elif mode==6: r=replace(r,observed=False)
        elif mode==7: e=e[:1]
        elif mode==8: g=(LineageEdge('E-A','E-B',Relation.CITES,True,p.binding,p.state_epoch),LineageEdge('E-B','E-C',Relation.CITES,True,p.binding,p.state_epoch))
        else: e=tuple(replace(x,lineage_known=False) for x in e)
        z=evaluate(r,e,g,p)
        rows.append((k,z.decision.value,z.reasons,z.independence_matrix,z.clusters,z.effective_evidence_count,z.mean_independence,z.mean_dependence,z.unknown_lineage_count,z.strong_dependence_pairs,z.next_gate_candidate,z.reevaluation_candidate,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.authority_promoted,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':93,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
