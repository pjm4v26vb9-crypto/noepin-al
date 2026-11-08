from __future__ import annotations
import json,time,statistics
from dataclasses import replace
import noepin_al_056_explanation_layer as m
NOW=1_800_000_000

def dataset(n=1200):
    rs=[]; es=[]; ts=[]
    for i in range(n):
        code=f'R{i:05d}'; did=f'D{i:05d}'; bind=f'B{i:05d}'
        rs.append(m.ReasonCodeDefinition(code,'BENCH',f'Benchmark reason {i}',frozenset({'ALLOW'}),frozenset({'META'}),frozenset({f'RULE{i:05d}'}),True))
        es.append(m.EvidenceReference(f'E{i:05d}',did,'META','BENCH',NOW-10,True,True,'INTERNAL',f'Meta {i}',bind,False))
        ts.append(m.PolicyTraceStep(f'T{i:05d}',did,f'RULE{i:05d}','EXPLAIN-056','1',1,'ALLOW',NOW-8,True,bind,False))
    return tuple(rs),tuple(es),tuple(ts)

def main():
    p=m.default_policy(NOW); rs,es,ts=dataset(1200); d=m.DecisionRecord('D00000','REQ-B',m.ControlDecision.ALLOW,'LOW',('R00000',),('E00000',),('T00000',),'EXPLAIN-056','1',1,'B00000')
    reg=m.prepare_registry(p,rs,es,ts,now=NOW)
    full=[]; prep=[]; sem=True
    for _ in range(5):
        t=time.perf_counter(); a=None
        for __ in range(12): a=m.evaluate(d,p,rs,es,ts,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter(); b=None
        for __ in range(12): b=m.evaluate_prepared(d,p,reg,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        sem=sem and m.canonical_json(a)==m.canonical_json(b)
    br,be,bt=dataset(2000)
    tr=list(br); te=list(be); tt=list(bt)
    for i in range(5,55): tr[i]=replace(tr[i],description=f'Changed reason {i}')
    for i in range(5,55): te[i]=replace(te[i],display_label=f'Changed meta {i}')
    for i in range(5,55): tt[i]=replace(tt[i],outcome='REVIEW')
    tr=tr[5:]+[m.ReasonCodeDefinition(f'RNEW{i:02d}','BENCH',f'New {i}',frozenset({'ALLOW'}),frozenset(),frozenset(),True) for i in range(5)]
    te=te[5:]+[m.EvidenceReference(f'ENEW{i:02d}',f'DNEW{i:02d}','META','BENCH',NOW-1,True,True,'INTERNAL',f'New meta {i}',f'BNEW{i:02d}',False) for i in range(5)]
    tt=tt[5:]+[m.PolicyTraceStep(f'TNEW{i:02d}',f'DNEW{i:02d}',f'RULENEW{i:02d}','EXPLAIN-056','1',1,'ALLOW',NOW-1,True,f'BNEW{i:02d}',False) for i in range(5)]
    tr,te,tt=tuple(tr),tuple(te),tuple(tt)
    delta=m.make_registry_delta(br,be,bt,tr,te,tt); rebuilt=m.apply_registry_delta(br,be,bt,delta)
    full_bytes=len(m.canonical_json({'reasons':tr,'evidence':te,'traces':tt}).encode()); delta_bytes=len(m.canonical_json(delta).encode())
    rknown={x.reason_code:m.fingerprint(x) for x in tr}; eknown={x.evidence_id:m.fingerprint(x) for x in te}; tknown={x.trace_id:m.fingerprint(x) for x in tt}
    for x in list(tr)[:10]: rknown.pop(x.reason_code,None)
    for x in list(te)[:10]: eknown.pop(x.evidence_id,None)
    for x in list(tt)[:10]: tknown.pop(x.trace_id,None)
    sync=m.plan_registry_sync(tr,te,tt,rknown,eknown,tknown)
    out={
      'condition':{'registry_reasons':1200,'registry_evidence':1200,'registry_traces':1200,'evaluations_per_batch':12,'batches':5,'runtime':'Python standard library'},
      'full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(prep),'semantic_match':sem,
      'delta':{'base_reasons':2000,'base_evidence':2000,'base_traces':2000,'target_reasons':len(tr),'target_evidence':len(te),'target_traces':len(tt),'changed_reasons':len(delta.changed_reasons),'removed_reasons':len(delta.removed_reason_codes),'added_reasons':len(delta.added_reasons),'changed_evidence':len(delta.changed_evidence),'removed_evidence':len(delta.removed_evidence_ids),'added_evidence':len(delta.added_evidence),'changed_traces':len(delta.changed_traces),'removed_traces':len(delta.removed_trace_ids),'added_traces':len(delta.added_traces),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(*rebuilt)==m.registry_fingerprint(tr,te,tt)},
      'sync':{'target_records':len(tr)+len(te)+len(tt),'remote_known':len(tr)+len(te)+len(tt)-30,'missing_or_changed_reasons':len(sync.missing_or_changed_reason_codes),'missing_or_changed_evidence':len(sync.missing_or_changed_evidence_ids),'missing_or_changed_traces':len(sync.missing_or_changed_trace_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'decision_override_authorized':sync.decision_override_authorized,'action_execution_authorized':sync.action_execution_authorized,'policy_compliance_proven':sync.policy_compliance_proven}}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return out
if __name__=='__main__': main()
