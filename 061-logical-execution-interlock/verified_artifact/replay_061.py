from __future__ import annotations
import json,sys
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_061_logical_execution_interlock as m
NOW=1_800_000_000

def app(r): return m.ApprovalEvidence('APP-R',r.request_id,'OWNER',True,True,True,NOW-2,NOW+100,r.evidence_binding,False)
def item(i):
    p=m.default_policy(NOW); r=m.default_request(NOW); aa=(); rr=(); k=i%10
    if k==1: r=replace(r,action='DELETE')
    elif k==2: r=replace(r,counterfactual_available=False)
    elif k==3: r=replace(r,semantic_confidence=.4)
    elif k==4: r=replace(r,privilege_elevation=True)
    elif k==5: r=replace(r,irreversible=True)
    elif k==6: r=replace(r,irreversible=True,explicit_authorization=True); aa=(app(r),)
    elif k==7: r=replace(r,external_side_effect=True)
    elif k==8: r=replace(r,expected_policy_version='OLD')
    elif k==9: r=replace(r,source_trust='UNKNOWN')
    return m.canonical_json(m.evaluate(r,p,aa,rr,now=NOW))
def run(n=1000):
    data='\n'.join(item(i) for i in range(n)); return sha256(data.encode()).hexdigest()
def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'REPLAY_RESULT.json'); ds=[run() for _ in range(3)]
    obj={'schema':'NOEPIN_AL_REPLAY_RESULT_V1','technology':61,'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
