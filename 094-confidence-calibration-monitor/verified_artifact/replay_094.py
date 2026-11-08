from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_094_confidence_calibration_monitor import *
base=(default_request(),default_observations(),default_policy()); digests=[]
for run in range(3):
    rows=[]
    for k in range(1000):
        r,o,p=base; mode=k%10
        if mode==0: pass
        elif mode==1: r=replace(r,risk=RiskLevel.HIGH,predicted_confidence=.95); o=tuple(replace(x,predicted_confidence=.95,observed_outcome=(i%2==0)) for i,x in enumerate(o))
        elif mode==2: o=o[:5]; r=replace(r,risk=RiskLevel.HIGH)
        elif mode==3: p=replace(p,revoked=True)
        elif mode==4: r=replace(r,observed=False)
        elif mode==5: r=replace(r,task_class='OTHER')
        elif mode==6: o=(replace(o[0],observed=False),)+o[1:]
        elif mode==7: r=replace(r,predicted_confidence=.59)
        elif mode==8: r=replace(r,risk=RiskLevel.HIGH)
        else:
            rows2=[]
            for i,x in enumerate(o): rows2.append(replace(x,observed_outcome=(True if i<30 else (i%4==0))))
            o=tuple(rows2)
        z=evaluate(r,o,p)
        rows.append((k,z.decision.value,z.reasons,z.sample_count,z.calibration_error_ece,z.brier_score,z.calibration_curve,z.empirical_accuracy,z.mean_predicted_confidence,z.adjusted_confidence,z.credible_interval,z.overconfidence_gap,z.underconfidence_gap,z.drift_detected,z.recent_accuracy,z.previous_accuracy,z.sparse_history,z.authority_shrink_candidate,z.warning_candidate,z.next_gate_candidate,z.reevaluation_candidate,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.authority_promoted,z.safety_proven,z.action_success))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
print(json.dumps({'schema':'NOEPIN_AL_REPLAY_V1','technology':94,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]},sort_keys=True))
