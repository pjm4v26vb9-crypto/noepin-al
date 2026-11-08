from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
import json
import noepin_al_043_safe_handoff as al

NOW=1_800_000_000

def one_run():
    p=al.default_policy(NOW); a=al.default_authority(); rows=[]
    for i in range(1000):
        base=al.default_request(NOW)
        intent=f'replay-{i%100}'
        items=(
            al.make_context(f'CTX-{i%100}-T','task',intent),
            al.make_context(f'CTX-{i%100}-A','authority',intent),
            al.make_context(f'CTX-{i%100}-S','state',intent),
        )
        scopes=(frozenset({'READ_CONTEXT'}),frozenset({'READ_CONTEXT','VERIFY'}),frozenset({'READ_CONTEXT','ANALYZE'}))[i%3]
        op=('VERIFY','ANALYZE','SUMMARIZE')[i%3]
        r=replace(base,delegation_id=f'R-{i%100:03d}',task_id=f'T-{i%100:03d}',intent=intent,operation=op,requested_scopes=scopes,context_items=items)
        d=al.evaluate(r,p,a,now=NOW)
        rows.append({'i':i,'decision':d.decision.value,'reasons':d.reasons,'trace':d.trace_hash,'token':d.token_candidate_fingerprint,'manifest':d.context_manifest_fingerprint,'grant':d.permission_granted,'handoff':d.handoff_executed})
    raw=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    return sha256(raw).hexdigest()

def main():
    digests=[one_run() for _ in range(3)]
    result={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':digests,'divergence':len(set(digests))-1,'digest':digests[0]}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0 if result['divergence']==0 else 2
if __name__=='__main__': raise SystemExit(main())
