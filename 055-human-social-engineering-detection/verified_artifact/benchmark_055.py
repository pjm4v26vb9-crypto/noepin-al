from __future__ import annotations
import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_055_social_engineering as m
NOW=1_800_000_000

def make_data(n):
    out=[]
    for i in range(n):
        out.append(m.InteractionEvidence(f'E-{i}',f'I-{i}',f'O-{i}',True,True,NOW-20,m.SignalLevel.LOW,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,1,False,True,True,True,f'B-{i}',False))
    return tuple(out)
def ctx(i): return m.ApprovalContext(f'C-{i}',f'I-{i}','VIEW_INFO','LOW','UNDECIDED','READ',True,'SOCENG-055','1',1,f'B-{i}')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path); a=ap.parse_args(); p=m.default_policy(NOW); es=make_data(2000); full=[]; pre=[]
    for _ in range(5):
        t=time.perf_counter();
        for i in range(20): m.evaluate(ctx(i),p,es,now=NOW)
        full.append((time.perf_counter()-t)*1000)
    reg=m.prepare_registry(p,es,now=NOW)
    for _ in range(5):
        t=time.perf_counter();
        for i in range(20): m.evaluate_prepared(ctx(i),p,reg,now=NOW)
        pre.append((time.perf_counter()-t)*1000)
    semantic=m.canonical_json(m.evaluate(ctx(3),p,es,now=NOW))==m.canonical_json(m.evaluate_prepared(ctx(3),p,reg,now=NOW))
    base=make_data(3000); target=list(base)
    for i in range(50,100): target[i]=replace(target[i],urgency=m.SignalLevel.MEDIUM)
    del target[:5]
    for i in range(5):
        j=3000+i; target.append(m.InteractionEvidence(f'E-{j}',f'I-{j}',f'O-{j}',True,True,NOW-20,m.SignalLevel.LOW,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,1,False,True,True,True,f'B-{j}',False))
    target=tuple(target); d=m.make_registry_delta(base,target); rec=m.apply_registry_delta(base,d)
    fullb=len(m.canonical_json(target).encode()); deltab=len(m.canonical_json(d).encode())
    known={x.evidence_id:m.fingerprint(x) for x in target[:-10]}; sync=m.plan_registry_sync(target,known)
    r={'condition':'2000 interaction evidence; 20 evaluations per batch; 5 batches; Python standard library','full_materialization_median_ms':statistics.median(full),'prepared_registry_median_ms':statistics.median(pre),'semantic_match':semantic,'delta':{'base_items':len(base),'target_items':len(target),'changed':len(d.changed_evidence),'removed':len(d.removed_evidence_ids),'added':len(d.added_evidence),'full_bytes':fullb,'delta_bytes':deltab,'ratio_percent':deltab/fullb*100,'reconstruction_fingerprint_match':m.registry_fingerprint(rec)==m.registry_fingerprint(target)},'sync':{'target_items':len(target),'remote_known':len(target)-10,'missing_or_changed':len(sync.missing_or_changed_evidence_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'approval_execution_authorized':sync.approval_execution_authorized,'user_decision_override_authorized':sync.user_decision_override_authorized,'message_send_authorized':sync.message_send_authorized}}
    txt=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+'\n'; print(txt,end='');
    if a.out: a.out.write_text(txt,encoding='utf-8')
if __name__=='__main__': main()
