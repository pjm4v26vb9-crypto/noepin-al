import json, time, statistics
from dataclasses import replace
from noepin_al_039_rules_engine import *

NOW=1_800_000_000

def make_profile(n=400):
    return RuleProfile("BENCH","1",2,NOW-100,NOW+10000,False,tuple(
        Rule(f"R{i}","NIST" if i%3==0 else ("OWASP" if i%3==1 else "INTERNAL"),"2026.1",f"C{i}",f"controls.c{i}",Operator.TRUE,severity=Severity.MEDIUM)
        for i in range(n)
    ))

def main():
    p=make_profile(); q=EvaluationRequest("Q","S","AUDIT",{"controls":{f"c{i}":True for i in range(400)}},())
    raw=canonical_json({"profile_id":p.profile_id,"profile_version":p.profile_version,"authority_epoch":p.authority_epoch,"issued_at":p.issued_at,"expires_at":p.expires_at,"revoked":p.revoked,"rules":[{"rule_id":r.rule_id,"source":r.source,"source_version":r.source_version,"control_id":r.control_id,"field":r.field,"operator":r.operator.value,"severity":r.severity.value} for r in p.rules]})
    ctx=prepare_context(q,p,[],now=NOW)
    batches=5; iters=60
    full=[]; prepared=[]
    for _ in range(batches):
        t=time.perf_counter()
        d=None
        for _ in range(iters):
            pp=profile_from_dict(json.loads(raw)); d=evaluate(q,pp,[],now=NOW).fingerprint
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); d2=None
        for _ in range(iters): d2=evaluate_prepared(ctx).fingerprint
        prepared.append((time.perf_counter()-t)*1000)
        assert d==d2
    target=make_profile()
    rules=list(target.rules)
    for i in range(20): rules[i]=replace(rules[i], severity=Severity.HIGH)
    rules=rules[5:]+tuple() if False else rules
    # remove 5, add 5
    rules=rules[5:]
    rules.extend(Rule(f"NEW{i}","INTERNAL","2026.2",f"NC{i}",f"controls.n{i}",Operator.TRUE) for i in range(5))
    target=RuleProfile("BENCH","2",3,NOW-100,NOW+10000,False,tuple(rules))
    delta=make_profile_delta(p,target); rebuilt=apply_profile_delta(p,delta)
    full_bytes=len(canonical_json(target).encode()); delta_bytes=len(canonical_json(delta).encode())
    out={"runtime":"Python standard library","rules":400,"iterations_per_batch":iters,"batches":batches,
         "full_parse_eval_median_ms":statistics.median(full),"prepared_eval_median_ms":statistics.median(prepared),
         "semantic_match":d==d2,"delta":{"changed":len(delta.changed_rules),"removed":len(delta.removed_rule_ids),"added":len(delta.added_rules),"full_bytes":full_bytes,"delta_bytes":delta_bytes,
         "ratio_percent":delta_bytes/full_bytes*100,"reconstruction_fingerprint_match":fingerprint(rebuilt)==fingerprint(target)}}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
