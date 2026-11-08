from __future__ import annotations
import json
import noepin_al_044_data_purpose as m

NOW=1_800_000_000

def one_run():
    p=m.default_policy(NOW); states=m.default_states(); prepared=m.prepare_registry(p,states,now=NOW)
    out=[]
    patterns=[
      (('D-INT',),'verification','internal','local_ai',False,False),
      (('D-CONF',),'analysis','secure','trusted_ai',False,False),
      (('D-PER',),'support','subject','trusted_ai',True,False),
      (('D-RES',),'verification','secure','local_ai',False,False),
      (('D-PUB',),'publish','public','external_ai',False,False),
      (('D-CONF',),'verification','secure','trusted_ai',True,True),
      (('D-INT',),'publish','internal','local_ai',False,False),
    ]
    for i in range(1000):
        ids,purpose,ctx,recipient,ext,human=patterns[i%len(patterns)]
        req=m.DataUseRequest(f'R{i:04d}',purpose,ctx,recipient,ids,'BIND-044',p.policy_id,p.version,p.authority_epoch,ext,human)
        out.append(m.evaluate_prepared(req,p,prepared,now=NOW))
    return m.assessment_digest(out)

def main():
    digests=[one_run() for _ in range(3)]
    result={'runs':3,'evaluations_per_run':1000,'evaluations':3000,'digests':digests,'divergence':0 if len(set(digests))==1 else 1,'digest':digests[0]}
    print(json.dumps(result,sort_keys=True))
    return 0 if result['divergence']==0 else 2

if __name__=='__main__': raise SystemExit(main())
