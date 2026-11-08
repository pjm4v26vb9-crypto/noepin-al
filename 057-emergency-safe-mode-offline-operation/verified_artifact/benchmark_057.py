from __future__ import annotations
from dataclasses import replace
import json,statistics,time
import noepin_al_057_emergency_safe_mode as m
NOW=1_800_000_000

def make_data(n):
    sig=[]; rec=[]
    for i in range(n):
        inc='INC-057' if i==0 else f'INC-{i}'
        bind='BIND-057' if i==0 else f'B-{i}'
        sig.append(m.IncidentSignal(f'S-{i:05d}',inc,'HIGH' if i%7==0 else 'LOW',frozenset({'NETWORK_ANOMALY' if i%3==0 else 'DEPENDENCY_OUTAGE'}),NOW-(i%300),True,True,bind,False))
        rec.append(m.ReplayReceipt(f'R-{i:05d}',f'OLD-{i}',f'OLD-N-{i}',m.SafeMode.LOCAL_ONLY,NOW-(i%300),True,bind,False))
    return tuple(sig),tuple(rec)

def median_ms(fn,batches=5):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter(); fn(); vals.append((time.perf_counter()-t)*1000)
    return statistics.median(vals)

def main():
    p=m.default_policy(NOW); req=m.default_request(NOW); sig,rec=make_data(1500)
    def full():
        for _ in range(15): m.evaluate(req,p,sig,rec,now=NOW)
    reg=m.prepare_registry(p,sig,rec,now=NOW)
    def prepared():
        for _ in range(15): m.evaluate_prepared(req,p,reg,now=NOW)
    f=median_ms(full); pr=median_ms(prepared)
    a=m.evaluate(req,p,sig,rec,now=NOW); b=m.evaluate_prepared(req,p,reg,now=NOW)
    bs,br=make_data(2000)
    # non-overlapping 50 changed, 5 removed, 5 added for both state classes
    ts=list(bs); tr=list(br)
    for i in range(50,100): ts[i]=replace(ts[i],severity='CRITICAL' if ts[i].severity!='CRITICAL' else 'HIGH')
    for i in range(50,100): tr[i]=replace(tr[i],verified=not tr[i].verified)
    del ts[0:5]; del tr[0:5]
    for i in range(5):
        ts.append(m.IncidentSignal(f'NEW-S-{i}','NEW-INC','MEDIUM',frozenset({'AUTOMATION_ANOMALY'}),NOW,True,True,'NEW-B',False))
        tr.append(m.ReplayReceipt(f'NEW-R-{i}','NEW-REQ',f'NEW-N-{i}',m.SafeMode.DEGRADED,NOW,True,'NEW-B',False))
    ts=tuple(ts); tr=tuple(tr)
    dl=m.make_registry_delta(bs,br,ts,tr); recon=m.apply_registry_delta(bs,br,dl)
    full_bytes=len(m.canonical_json({'signals':ts,'receipts':tr}).encode()); delta_bytes=len(m.canonical_json(dl).encode())
    targ=m.prepare_registry(p,ts,tr,now=NOW)
    sf=dict(targ.signal_fingerprints); rf=dict(targ.receipt_fingerprints)
    # Pretend 10 signal + 10 receipt fingerprints are missing/changed remotely.
    for k in sorted(sf)[-10:]: sf.pop(k)
    for k in sorted(rf)[-10:]: rf.pop(k)
    sync=m.plan_registry_sync(ts,tr,sf,rf)
    out={
      'condition':'1500 signals + 1500 replay receipts; 15 evaluations per batch; 5 batches; Python standard library',
      'full_materialization_median_ms':f,'prepared_registry_median_ms':pr,'semantic_match':m.canonical_json(a)==m.canonical_json(b),
      'delta':{'base_signals':len(bs),'base_receipts':len(br),'target_signals':len(ts),'target_receipts':len(tr),'changed_signals':len(dl.changed_signals),'removed_signals':len(dl.removed_signal_ids),'added_signals':len(dl.added_signals),'changed_receipts':len(dl.changed_receipts),'removed_receipts':len(dl.removed_receipt_ids),'added_receipts':len(dl.added_receipts),'full_bytes':full_bytes,'delta_bytes':delta_bytes,'ratio_percent':delta_bytes/full_bytes*100,'reconstruction_fingerprint_match':m.registry_fingerprint(*recon)==m.registry_fingerprint(ts,tr)},
      'sync':{'target_records':len(ts)+len(tr),'remote_known':len(ts)+len(tr)-len(sync.missing_or_changed_signal_ids)-len(sync.missing_or_changed_receipt_ids),'missing_or_changed_signals':len(sync.missing_or_changed_signal_ids),'missing_or_changed_receipts':len(sync.missing_or_changed_receipt_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required,'permission_granted':sync.permission_granted,'mode_transition_authorized':sync.mode_transition_authorized,'network_disconnect_authorized':sync.network_disconnect_authorized,'write_disable_authorized':sync.write_disable_authorized,'receipt_persist_authorized':sync.receipt_persist_authorized}}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return out
if __name__=='__main__': main()
