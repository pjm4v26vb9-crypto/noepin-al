from dataclasses import replace
import json,statistics,time
from noepin_al_069_dependency_order_verifier import *
NOW=1_800_000_000

def common():
    return dict(binding="DOV-BIND",verified=True,revoked=False,policy_id="DOV-POLICY",policy_version="1",authority_epoch="DOV-EPOCH")

def fixture(n=1500):
    p=default_policy(NOW); base=list(default_actions()); obs=list(default_observations()); fo=default_forbidden_orders(); c=common()
    for i in range(n):
        aid=f'X{i:04d}'; base.append(ActionSpec(aid,(Predicate('workspace_ready','true'),),(Predicate(f'x_done_{i:04d}','true'),),**c))
    r=default_request(NOW)
    return p,tuple(base),tuple(obs),fo,r

def run():
    p,a,o,f,r=fixture(); st=prepare_state(p,a,o,f,binding=r.binding,now=NOW); valid=validate_prepared_integrity(st); full=[]; prep=[]; semantic=True
    for _ in range(5):
        t=time.perf_counter()
        for __ in range(10): z=evaluate(r,p,a,o,f,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for __ in range(10): z2=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        semantic = semantic and ((z.decision.value,z.reasons,z.legal_order,z.reorder_required)==(z2.decision.value,z2.reasons,z2.legal_order,z2.reorder_required))
    aa=list(a)
    for i in range(50):
        j=4+i; aa[j]=replace(aa[j],postconditions=aa[j].postconditions+(Predicate(f'audit_{i:04d}','true'),))
    aa=aa[:4]+aa[9:]
    c=common()
    for i in range(5): aa.append(ActionSpec(f'NEW{i}',(Predicate('workspace_ready','true'),),(Predicate(f'new_done_{i}','true'),),**c))
    st2=prepare_state(p,tuple(aa),o,f,binding=r.binding,now=NOW); d=make_delta(st,st2); rebuilt=apply_delta(st,d,now=NOW)
    remote={'actions':dict(st2.action_fingerprints),'observations':dict(st2.observation_fingerprints),'forbidden_orders':dict(st2.forbidden_fingerprints)}
    for k in list(remote['actions'])[:10]: remote['actions'].pop(k)
    sync=missing_only_sync_plan(st2,remote)
    return {'schema':'NOEPIN_AL_DCSR_BENCHMARK_V1','technology':69,'condition':{'runtime':'Python standard library','actions':len(a),'observations':len(o),'forbidden_orders':len(f),'evaluations_per_batch':10,'batches':5},'full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_ratio_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'delta_fixture':{'changed_actions':50,'removed_actions':5,'added_actions':5},'reconstruction_fingerprint_match':rebuilt.registry_fingerprint==st2.registry_fingerprint,'missing_only':{'actions':len(sync.missing_or_changed_action_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required},'authority':{'permission_grant':False,'plan_rewrite':False,'state_write':False,'action_execution':False,'deployment_execution':False,'truth':False,'safety':False,'action_success':False}}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
