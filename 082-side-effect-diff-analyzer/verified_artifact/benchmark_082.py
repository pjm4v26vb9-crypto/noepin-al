from dataclasses import replace
import json,statistics,time
from noepin_al_082_side_effect_diff_analyzer import *
p=default_policy(); bnd,ep=p.binding,p.state_epoch; N=5000
before=tuple(StateField(f'path/{n:05d}','OLD',True,True,'R1',bnd,ep) for n in range(N))
after=list(before)
expected=[]
for n in range(50):
    after[n]=StateField(f'path/{n:05d}','NEW',True,True,'R2',bnd,ep)
    expected.append(ExpectedEffect(f'E-{n:05d}',f'path/{n:05d}',ChangeKind.CHANGE,'OLD','NEW',True,bnd,ep))
after=tuple(after); expected=tuple(expected); q=DiffRequest('BENCH','INTENT-B',tuple(x.effect_id for x in expected),(),True,True,(),bnd,ep); protected=(); severity=()
st=prepare_state(p,q,before,after,expected,protected,severity,binding=bnd); valid=validate_prepared_integrity(st)
full=[]; prep=[]; semantic=True
for _ in range(5):
    t=time.perf_counter(); z1=None
    for __ in range(10): z1=evaluate(q,p,before,after,expected,protected,severity)
    full.append((time.perf_counter()-t)*1000)
    t=time.perf_counter(); z2=None
    for __ in range(10): z2=evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid)
    prep.append((time.perf_counter()-t)*1000); semantic &= (z1==z2)
after2=list(after)
for n in range(10): after2[n]=replace(after2[n],value='NEW2')
st2=prepare_state(p,q,before,tuple(after2),expected,protected,severity,binding=bnd); delta=make_delta(st,st2)
kb=dict(st2.before_fingerprints); ka=dict(st2.after_fingerprints); ke=dict(st2.expected_fingerprints); kp=dict(st2.protected_fingerprints); ks=dict(st2.severity_fingerprints)
for n in range(10): ka.pop(f'path/{n:05d}')
plan=missing_only_sync_plan(st2,kb,ka,ke,kp,ks)
out={'schema':'NOEPIN_AL_BENCHMARK_V1','technology':82,'condition':'Python stdlib; 5000 Before + 5000 After fields; 50 Expected Effects; 10 evaluations x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':semantic,'full_bytes':full_registry_bytes(st2),'delta_bytes':delta_bytes(delta),'delta_percent':delta_bytes(delta)/full_registry_bytes(st2)*100,'missing_after_records':len(plan.missing_or_changed_after_paths),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend_required':plan.full_resend_required}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
