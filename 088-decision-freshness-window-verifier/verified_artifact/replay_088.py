from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_088_decision_freshness_window_verifier import *
base=(default_request(),default_dependencies(),default_policy())
digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,d,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: d=(replace(d[0],last_observed_at=900,criticality=Criticality.CRITICAL),d[1])
        elif mode==2: r=replace(r,risk=RiskLevel.HIGH,now=1011,decision_time=1008); d=(replace(d[0],volatility_score=None,last_observed_at=1005,criticality=Criticality.LOW),replace(d[1],last_observed_at=1010,criticality=Criticality.LOW))
        elif mode==3: d=(replace(d[0],observed=False),d[1])
        elif mode==4: d=(replace(d[0],source_version=''),d[1])
        elif mode==5: r=replace(r,now=1004,decision_time=1003); d=tuple(replace(x,last_observed_at=1004,volatility_score=1.0,criticality=Criticality.LOW) for x in d)
        elif mode==6: r=replace(r,now=1150); d=tuple(replace(x,last_observed_at=1149,volatility_score=0.0,criticality=Criticality.LOW) for x in d)
        elif mode==7: p=replace(p,revoked=True)
        elif mode==8: d=(replace(d[0],last_observed_at=1013),d[1])
        else: r=replace(r,risk=RiskLevel.LOW,decision_time=1009); d=(replace(d[0],last_observed_at=600,criticality=Criticality.LOW),replace(d[1],last_observed_at=1009,criticality=Criticality.LOW,volatility_score=0.0))
        z=evaluate(r,d,p)
        rows.append((k,z.decision.value,z.freshness_state.value,z.reasons,z.freshness_window_seconds,z.expired_fields,z.refresh_required_fields,z.unknown_volatility_fields,z.reevaluation_required,z.reevaluation_flag.value,z.next_gate_candidate,z.cache_reuse_candidate,z.cache_promoted_to_truth,z.cache_promoted_to_authority,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':88,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
