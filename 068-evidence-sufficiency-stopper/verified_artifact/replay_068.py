from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_068_evidence_sufficiency_stopper import *
NOW=1_800_000_000

def case(i):
    p=default_policy(NOW); c=default_claims(); s=default_sources(); e=default_evidence(NOW); r=default_request(NOW)
    m=i%5
    if m==1: e=e[:2]
    elif m==2: e=tuple(replace(x,observed_at=NOW-600) if x.evidence_id=='E-C' else x for x in e)
    elif m==3: r=replace(r,action_risk=Risk.MEDIUM); e=e[:2]
    elif m==4: e=e+(replace(e[0],evidence_id=f'RC{i}',source_id='SRC-C',state=EvidenceState.CONTRADICTS),)
    return r,p,c,s,e

def run():
    rows=[]; div=0
    for i in range(1000):
        r,p,c,s,e=case(i); z=evaluate(r,p,c,s,e,now=NOW); rows.append((z.decision.value,z.reasons,round(z.evidence_score,12),z.independent_source_count,z.direct_source_count,z.fresh_source_count,z.stale_source_count,z.duplicate_evidence_ids,z.excluded_evidence_ids,z.contradictory_evidence_ids,z.missing_requirements,z.next_gate_candidate))
    digest=sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    for _ in range(2):
        rows2=[]
        for i in range(1000):
            r,p,c,s,e=case(i); z=evaluate(r,p,c,s,e,now=NOW); rows2.append((z.decision.value,z.reasons,round(z.evidence_score,12),z.independent_source_count,z.direct_source_count,z.fresh_source_count,z.stale_source_count,z.duplicate_evidence_ids,z.excluded_evidence_ids,z.contradictory_evidence_ids,z.missing_requirements,z.next_gate_candidate))
        d2=sha256(json.dumps(rows2,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(); div += 0 if d2==digest else 1
    return {'schema':'NOEPIN_AL_REPLAY_RESULT_V1','technology':68,'runs':3,'cases_per_run':1000,'total':3000,'divergence':div,'digest':digest}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
