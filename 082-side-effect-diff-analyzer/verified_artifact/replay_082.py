from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_082_side_effect_diff_analyzer import *
base=(default_request(),default_policy(),default_before_state(),default_after_state(),default_expected_effects(),default_protected_fields(),default_severity_rules())
digests=[]
for run in range(3):
    rows=[]
    for n in range(1000):
        q,p,b,a,e,pr,s=base; m=n%8
        if m==0: pass
        elif m==1: a=tuple(replace(x,value='CHANGED') if x.path=='secrets/token' else x for x in a)
        elif m==2: b=b+(StateField('project/settings/x','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField('project/settings/x','b',True,True,'R',p.binding,p.state_epoch),)
        elif m==3: a=tuple(replace(x,value='trace',exists=True) if x.path=='logs/trace' else x for x in a)
        elif m==4: q=replace(q,before_complete=False)
        elif m==5: a=(replace(a[0],observed=False),)+a[1:]
        elif m==6: a=(replace(a[0],value='old'),)+a[1:]
        else: b=b+(StateField('other/x','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField('other/x','b',True,True,'R',p.binding,p.state_epoch),)
        z=evaluate(q,p,b,a,e,pr,s)
        rows.append((n,z.decision.value,z.reasons,tuple((x.path,x.kind.value,x.severity.value,x.matched_expected_effect_id,x.protected_rule_id) for x in z.expected_diff),tuple((x.path,x.kind.value,x.severity.value,x.matched_expected_effect_id,x.protected_rule_id) for x in z.unexpected_diff),z.missing_expected_effects,z.highest_severity.value,z.actual_change_count,z.next_gate_candidate,z.rollback_candidate))
    digests.append(sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
out={'schema':'NOEPIN_AL_REPLAY_V1','technology':82,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':len(set(digests))-1,'digest':digests[0]}
print(json.dumps(out,sort_keys=True))
