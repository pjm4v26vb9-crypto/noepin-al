from dataclasses import replace
import json,statistics,time
from noepin_al_068_evidence_sufficiency_stopper import *
NOW=1_800_000_000

def fixture(n=1500):
    p=default_policy(NOW); common=dict(binding='ESS-BIND',verified=True,revoked=False,policy_id='ESS-POLICY',policy_version='1',authority_epoch='ESS-EPOCH')
    c=(ClaimSpec('B-CLAIM',**common),); s=[]; e=[]
    for i in range(n):
        sid=f'S{i:04d}'; s.append(SourceMetadata(sid,f'G{i:04d}','BENCH',**common)); e.append(EvidenceRecord(f'E{i:04d}','B-CLAIM',sid,EvidenceKind.DIRECT if i<1000 else EvidenceKind.INDIRECT,EvidenceState.SUPPORTS,.9,NOW-10,NOW+1000,**common))
    r=EvidenceRequest('BREQ','B-CLAIM',Risk.HIGH,'ESS-BIND','ESS-POLICY','1','ESS-EPOCH',NOW-1,NOW+1000)
    return p,c,tuple(s),tuple(e),r

def run():
    p,c,s,e,r=fixture(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); valid=validate_prepared_integrity(st); full=[]; prep=[]; semantic=True
    for _ in range(5):
        t=time.perf_counter();
        for __ in range(10): z=evaluate(r,p,c,s,e,now=NOW)
        full.append((time.perf_counter()-t)*1000)
        t=time.perf_counter();
        for __ in range(10): z2=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW)
        prep.append((time.perf_counter()-t)*1000)
        semantic = semantic and ((z.decision.value,z.reasons,z.evidence_score,z.independent_source_count,z.direct_source_count)==(z2.decision.value,z2.reasons,z2.evidence_score,z2.independent_source_count,z2.direct_source_count))
    ee=list(e)
    for i in range(50): ee[i]=replace(ee[i],confidence=.88)
    ee=ee[5:]
    for i in range(5): ee.append(EvidenceRecord(f'NEW{i}','B-CLAIM',f'S{100+i:04d}',EvidenceKind.DIRECT,EvidenceState.SUPPORTS,.91,NOW-5,NOW+1000,'ESS-BIND',True,False,'ESS-POLICY','1','ESS-EPOCH'))
    st2=prepare_state(p,c,s,tuple(ee),binding=r.binding,now=NOW); d=make_delta(st,st2); rebuilt=apply_delta(st,d,now=NOW)
    remote={'claims':dict(st2.claim_fingerprints),'sources':dict(st2.source_fingerprints),'evidence':dict(st2.evidence_fingerprints)}
    for k in list(remote['evidence'])[:10]: remote['evidence'].pop(k)
    sync=missing_only_sync_plan(st2,remote)
    return {'schema':'NOEPIN_AL_DCSR_BENCHMARK_V1','technology':68,'condition':{'runtime':'Python standard library','claims':len(c),'sources':len(s),'evidence':len(e),'evaluations_per_batch':10,'batches':5},'full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(d),'delta_ratio_percent':delta_bytes(d)/full_registry_bytes(st2)*100,'delta_fixture':{'changed_evidence':50,'removed_evidence':5,'added_evidence':5},'reconstruction_fingerprint_match':rebuilt.registry_fingerprint==st2.registry_fingerprint,'missing_only':{'evidence':len(sync.missing_or_changed_evidence_ids),'metadata_bytes_required':sync.metadata_bytes_required,'full_resend_required':sync.full_resend_required},'authority':{'truth':False,'permission_grant':False,'evidence_write':False,'approval_execution':False,'data_send':False,'action_execution':False,'safety':False,'action_success':False}}
if __name__=='__main__': print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
