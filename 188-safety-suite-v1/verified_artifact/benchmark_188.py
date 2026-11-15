import json,time
import noepin_al_188_safety_suite_distribution as m
N=1000; req=m.default_request(); arts=m.default_artifacts(); p=m.prepare_state(req,arts)
def full(): m.evaluate(req,arts)
def prep(): m.evaluate_prepared(p,integrity_validated=True,current_request=req,current_artifacts=arts,current_result_fingerprint=p.result_fingerprint,current_integrity_fingerprint=p.integrity_fingerprint)
def bench(fn):
 ts=[]
 for _ in range(5):
  t=time.perf_counter_ns()
  for i in range(N):fn()
  ts.append((time.perf_counter_ns()-t)/1e6/N)
 return sum(ts)/len(ts)
f=bench(full); q=bench(prep); d=m.make_delta(req,arts,{'REQUEST':m.request_fingerprint(req),'CONTROL_ARTIFACT_REGISTRY':m.artifacts_fingerprint(arts)})
print(json.dumps({'full_ms':f,'prepared_ms':q,'semantic_match':m.fingerprint(m.evaluate(req,arts))==p.result_fingerprint,'full_registry_bytes':sum(len(a.filename)+len(a.sha256)+16 for a in arts),'delta_metadata_bytes':d.metadata_bytes,'missing':list(d.missing_or_changed_fields),'full_revalidation_required':d.full_revalidation_required},sort_keys=True))
