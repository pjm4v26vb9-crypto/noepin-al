import unittest
from dataclasses import replace
import noepin_al_185_common_state_kernel_v1 as m

A=m.default_address(); META=m.default_meta(); REQ=m.default_request()
def addr(resource,version='v1'): return m.StateAddress('calc',resource,version)
def prepared(q,ok=True):
 st=m.prepare_state(q)
 return m.evaluate_prepared(st,integrity_validated=ok,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q)
def safe_false(r): return not any(getattr(r,n) for n in m._FALSE_FIELDS)

def scenario(k,rep):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.source=='materialized' and not r.authoritative and safe_false(r)
 if k==1: return m.default_evaluation()==m.default_evaluation()
 if k==2: return m.canonicalize_address(m.StateAddress('MEMORY','profile','v1','user','',(('b','2'),('a','1'))))==m.canonicalize_address(m.StateAddress('memory','profile','v1','user','',(('a','1'),('b','2'))))
 if k==3: return m.dependency_fingerprint((('b','2'),('a','1')))==m.dependency_fingerprint((('a','1'),('b','2')))
 if k==4: return m.cache_key(REQ)==m.cache_key(REQ)
 if k==5:
  try: m.canonicalize_address(m.StateAddress('','x','1')); return False
  except ValueError: return True
 if k==6:
  kx=m.CommonStateKernel(); kx.register_materialized(A,1,META); return kx.query_index('memory','profile')==(m.canonicalize_address(A),)
 if k==7:
  kx=m.CommonStateKernel(); kx.register_materialized(A,3,META); r=kx.resolve(REQ); return r.value==3 and r.source=='materialized' and not r.authoritative
 if k==8:
  kx=m.CommonStateKernel(); kx.cache_put(REQ,9,META); r=kx.resolve(REQ); return r.value==9 and r.source=='cache' and not r.cached_result_promoted_to_authoritative
 if k==9:
  kx=m.CommonStateKernel(); kx.cache_put(REQ,9,META); q=replace(REQ,context_fingerprint='other'); return kx.cache_get(q) is None
 if k==10:
  kx=m.CommonStateKernel(); kx.register_prepared(A,(1,2,3),'SUM',META); r=kx.resolve(REQ); return r.value==6 and r.source=='prepared' and r.engine_state==m.EngineState.PREPARED_STATE_CANDIDATE
 if k==11:
  kx=m.CommonStateKernel(); kx.register_prepared(A,({'a':1},{'b':2}),'MERGE_DICT',META); return kx.resolve(REQ).value=={'a':1,'b':2}
 if k==12:
  kx=m.CommonStateKernel(); kx.register_materialized(A,4,META); c=addr('derived'); kx.register_generator(c,(A,),'SUM',m.StateMeta('1','auth-v1','domain://calc')); q=replace(REQ,address=c); r=kx.resolve(q); return r.value==4 and r.source=='lazy-materialization'
 if k==13:
  kx=m.CommonStateKernel(); c=addr('derived'); kx.register_generator(c,(A,),'SUM',m.StateMeta('1','auth-v1')); return kx.resolve(replace(REQ,address=c)).full_recompute_candidate
 if k==14:
  kx=m.CommonStateKernel(); a=addr('a'); b=addr('b'); kx.register_generator(a,(b,),'SUM',m.StateMeta('1','auth-v1')); kx.register_generator(b,(a,),'SUM',m.StateMeta('1','auth-v1')); r=kx.resolve(replace(REQ,address=a)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DEPENDENCY_CYCLE
 if k==15:
  kx=m.CommonStateKernel(max_dependency_depth=0); a=addr('a'); b=addr('b'); kx.register_materialized(b,1,META); kx.register_generator(a,(b,),'SUM',m.StateMeta('1','auth-v1')); r=kx.resolve(replace(REQ,address=a)); return r.escalation==m.Escalation.DEPTH_OVERFLOW
 if k==16:
  kx=m.CommonStateKernel(max_materializations_per_resolve=1); a=addr('a'); b=addr('b'); kx.register_materialized(b,1,META); kx.register_generator(a,(b,),'SUM',m.StateMeta('1','auth-v1')); return kx.resolve(replace(REQ,address=a)).escalation==m.Escalation.BUDGET_OVERFLOW
 if k==17:
  kx=m.CommonStateKernel(); kx.register_materialized(A,1,replace(META,schema_version='2')); r=kx.resolve(REQ); return r.escalation==m.Escalation.SCHEMA_MISMATCH and r.decision==m.Decision.HOLD
 if k==18:
  kx=m.CommonStateKernel(); kx.register_materialized(A,1,replace(META,authority_version='auth-v2')); r=kx.resolve(REQ); return r.escalation==m.Escalation.AUTHORITY_MISMATCH
 if k==19:
  kx=m.CommonStateKernel(); kx.register_materialized(A,1,replace(META,expires_at=5)); r=kx.resolve(replace(REQ,now=6)); return r.source!='materialized' and r.full_recompute_candidate
 if k==20:
  return m.evaluate(replace(REQ,known=False)).decision==m.Decision.HOLD and m.evaluate(replace(REQ,known=False)).full_recompute_candidate
 if k==21: return m.evaluate(replace(REQ,ambiguous=True)).escalation==m.Escalation.UNKNOWN_OR_AMBIGUOUS
 if k==22: return m.evaluate(replace(REQ,unsupported=True)).next_action==m.NextAction.NORMAL_COMPUTATION_FALLBACK_CANDIDATE
 if k==23:
  kx=m.CommonStateKernel(); kx.stage_publication('t',A,7,META); before=kx.resolve(REQ); ok=(before.full_recompute_candidate and kx.abort_publication('t')); return ok and kx.resolve(REQ).full_recompute_candidate
 if k==24:
  kx=m.CommonStateKernel(); kx.stage_publication('t',A,7,META); kx.commit_publication('t',True); return kx.resolve(REQ).value==7
 if k==25:
  kx=m.CommonStateKernel(); kx.stage_publication('t',A,7,META)
  try: kx.commit_publication('t',False); return False
  except ValueError: return kx.resolve(REQ).full_recompute_candidate
 if k==26:
  kx=m.CommonStateKernel(); kx.register_materialized(A,{'z':1},META); return kx.snapshot().fingerprint==kx.snapshot().fingerprint
 if k==27:
  kx=m.CommonStateKernel(); f1=kx.register_materialized(A,{'a':1,'b':2},META); f2=kx.register_materialized(m.StateAddress('memory','profile','v1','user','',A.qualifiers),{'b':2,'a':1},META); return f1==f2
 if k==28:
  r=m.default_evaluation(); return not r.authoritative and not r.memory_promoted_to_truth and not r.candidate_promoted_to_actual and not r.intent_promoted_to_action and not r.action_request_promoted_to_success
 if k==29:
  r=m.default_evaluation(); return safe_false(r) and not r.world_truth_proven and not r.safety_proven
 if k==30:
  q=m.default_request(); a=m.evaluate(q); b=prepared(q); return a.result_fingerprint==b.result_fingerprint and b.prepared_state_reused and b.next_gate_candidate
 if k==31:
  q=m.default_request(); st=m.prepare_state(q); r=m.evaluate_prepared(st,integrity_validated=False,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.PREPARED_STATE_STALE and r.full_recompute_candidate
 if k==32:
  q=m.default_request(); st=m.prepare_state(q); changed=replace(q,context_fingerprint='changed'); r=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=changed); return r.full_recompute_candidate and not r.prepared_state_reused
 if k==33:
  a=m.default_request(); b=replace(a,context_fingerprint='new'); d=m.make_delta(a,b); return d.changed_fields==('context_fingerprint',)
 if k==34:
  a=m.default_request(); b=replace(a,context_fingerprint='new'); p=m.plan_missing_only(a,b); return p.missing_or_changed_record_ids==('REQUEST_FIELD:context_fingerprint',) and not p.full_resend_required
 if k==35:
  a=m.default_request(); b=replace(a,kernel_id='OTHER'); p=m.plan_missing_only(a,b); return p.missing_or_changed_record_ids==('FULL_KERNEL_STATE',) and p.full_resend_required
 if k==36:
  a=m.default_request(); b=replace(a,schema_version='2'); return m.plan_missing_only(a,b).full_resend_required
 if k==37:
  r=m.default_evaluation(); return not r.dcsr_invented_state and not r.dcsr_bypassed_authority and not r.dcsr_bypassed_schema and not r.dcsr_bypassed_dependency and not r.dcsr_promoted_cache_to_truth
 if k==38:
  q1=replace(REQ,temporal_sequence=1); q2=replace(REQ,temporal_sequence=2); return m.cache_key(q1)!=m.cache_key(q2)
 if k==39:
  q1=replace(REQ,authority_version='a'); q2=replace(REQ,authority_version='b'); return m.cache_key(q1)!=m.cache_key(q2)
 return False

class TestAL185(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%40,i//40))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL185,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
