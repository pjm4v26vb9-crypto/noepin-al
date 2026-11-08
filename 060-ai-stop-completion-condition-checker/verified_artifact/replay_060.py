from __future__ import annotations
import json,sys
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_060_stop_completion_checker as m
NOW=1_800_000_000

def item(i):
    p=m.default_policy(NOW); r=m.default_request(NOW); ps=m.default_progress(NOW); cs=m.default_criteria(NOW); ds=m.default_dependencies(NOW)
    k=i%10
    if k==1: cs=(replace(cs[0],satisfied=False),cs[1])
    elif k==2: ps=(replace(ps[0],current_step=p.max_steps),)
    elif k==3: ps=(replace(ps[0],no_progress_steps=p.max_no_progress_steps),)
    elif k==4: ps=(replace(ps[0],requested_extra_work=True),)
    elif k==5: ds=(replace(ds[0],completed=False),)
    elif k==6: ps=(replace(ps[0],elapsed_seconds=p.max_elapsed_seconds),)
    elif k==7: ps=(replace(ps[0],fatal_error=True),)
    elif k==8: cs=(replace(cs[0],verified=False),cs[1])
    elif k==9: ds=(replace(ds[0],completed=False,failed=True),)
    a=m.evaluate(r,p,ps,cs,ds,now=NOW)
    return m.canonical_json(a)

def run(n=1000):
    data='\n'.join(item(i) for i in range(n)); return sha256(data.encode()).hexdigest()

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'REPLAY_RESULT.json')
    ds=[run() for _ in range(3)]
    obj={'schema':'NOEPIN_AL_REPLAY_RESULT_V1','technology':60,'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':ds,'digest':ds[0],'divergence':len(set(ds))-1}
    out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps(obj,sort_keys=True))
if __name__=='__main__': main()
