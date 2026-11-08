from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_067_assumption_verification_graph import *
NOW=1_800_000_000

def case(i):
    p=default_policy(NOW); a=default_assumptions(); e=default_edges(); v=default_evidence(NOW); o=default_observations(NOW); x=default_actions(); r=default_request(NOW)
    m=i%4
    if m==1: v=tuple(q for q in v if q.assumption_id!="ASM-SCHEMA-COMPAT")
    elif m==2: v=v+(replace(v[0],evidence_id=f"RC{i}",state=EvidenceState.CONTRADICTED),)
    elif m==3: r=replace(r,selected_action_ids=("ACT-READ-LOG",))
    return r,p,a,e,v,o,x

def run():
    rows=[]; div=0
    for i in range(1000):
        r,p,a,e,v,o,x=case(i); z=evaluate(r,p,a,e,v,o,x,now=NOW); rows.append((z.decision.value,z.reasons,z.verified_assumption_ids,z.unverified_assumption_ids,z.contradicted_assumption_ids,round(z.low_unverified_risk,6),z.next_gate_candidate))
    digest=sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    for _ in range(2):
        rows2=[]
        for i in range(1000):
            r,p,a,e,v,o,x=case(i); z=evaluate(r,p,a,e,v,o,x,now=NOW); rows2.append((z.decision.value,z.reasons,z.verified_assumption_ids,z.unverified_assumption_ids,z.contradicted_assumption_ids,round(z.low_unverified_risk,6),z.next_gate_candidate))
        d2=sha256(json.dumps(rows2,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest(); div += 0 if d2==digest else 1
    return {"schema":"NOEPIN_AL_REPLAY_RESULT_V1","technology":67,"runs":3,"cases_per_run":1000,"total":3000,"divergence":div,"digest":digest}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
