from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_054_isolated_test_orchestrator as m
NOW=1_800_000_000

def base():
    p=m.default_policy(NOW); r=m.default_request(NOW); s,e=m.default_registry(NOW); return p,r,s,e
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,r,s,e=base()
    if k==0:
        x=m.evaluate(r,p,s,e,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.sandbox_ready_candidate and x.sandbox_pass_candidate and not x.permission_granted and not x.production_safe_proven
    elif k==1:
        x=m.evaluate(r,p,(replace(s[0],ephemeral=False),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'SANDBOX_NOT_EPHEMERAL' in x.reasons
    elif k==2:
        x=m.evaluate(r,p,(replace(s[0],real_secrets_mounted=True),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'REAL_SECRET_ISOLATION_VIOLATION' in x.reasons
    elif k==3:
        x=m.evaluate(r,p,(replace(s[0],fake_secrets_only=False),),e,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==4:
        rr=replace(r,requested_network_mode='OPEN'); x=m.evaluate(rr,p,s,e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'REQUESTED_NETWORK_MODE_NOT_ALLOWED' in x.reasons
    elif k==5:
        x=m.evaluate(r,p,(replace(s[0],filesystem_mode='HOST_RW'),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'FILESYSTEM_ISOLATION_MISMATCH' in x.reasons
    elif k==6:
        x=m.evaluate(r,p,(replace(s[0],privileged=True),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'PRIVILEGED_SANDBOX_FORBIDDEN' in x.reasons
    elif k==7:
        x=m.evaluate(r,p,(replace(s[0],persistence_enabled=True),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'PERSISTENT_SANDBOX_FORBIDDEN' in x.reasons
    elif k==8:
        x=m.evaluate(r,p,(replace(s[0],external_service_access=True),),e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'EXTERNAL_SERVICE_ACCESS_FORBIDDEN' in x.reasons
    elif k==9:
        rr=replace(r,expected_policy_version='bad'); x=m.evaluate(rr,p,s,e,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in x.reasons
    elif k==10:
        rr=replace(r,subject_type='UNKNOWN'); x=m.evaluate(rr,p,s,e,now=NOW); assert x.decision is m.ControlDecision.DENY and 'SUBJECT_TYPE_NOT_ALLOWED' in x.reasons
    elif k==11:
        x=m.evaluate(r,p,s,(),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'INDEPENDENT_RUN_EVIDENCE_REQUIRED' in x.reasons
    elif k==12:
        x=m.evaluate(r,p,s,(replace(e[0],network_escaped=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'NETWORK_ISOLATION_BREACH' in x.reasons
    elif k==13:
        x=m.evaluate(r,p,s,(replace(e[0],real_secret_accessed=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'REAL_SECRET_ACCESS_OBSERVED' in x.reasons
    elif k==14:
        x=m.evaluate(r,p,s,(replace(e[0],host_mutation_observed=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'HOST_OR_PERSISTENCE_MUTATION_OBSERVED' in x.reasons
    elif k==15:
        reg=m.prepare_registry(p,s,e,now=NOW); x=m.evaluate(r,p,s,e,now=NOW); y=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==16:
        reg=m.prepare_registry(p,s,e,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==17:
        ns=(replace(s[0],created_at=NOW-40),m.SandboxProfile('PROFILE-X',True,True,False,'DENY','TEMP_ONLY',False,False,False,NOW-20,'BIND-X',False)); ne=(replace(e[0],output_bytes=4096),)
        d=m.make_registry_delta(s,e,ns,ne); rs,re_=m.apply_registry_delta(s,e,d); assert m.registry_fingerprint(rs,re_)==m.registry_fingerprint(ns,ne)
    elif k==18:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==19:
        x=m.evaluate(replace(r,risk=m.TestRisk.HIGH),p,s,e,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.sandbox_pass_candidate and x.human_review_candidate and not x.permission_granted
    elif k==20:
        x=m.evaluate(r,replace(p,revoked=True),s,e,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_REVOKED' in x.reasons
    elif k==21:
        bad=replace(p,expires_at=NOW-1); x=m.evaluate(r,bad,s,e,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==22:
        x=m.evaluate(r,p,s,(replace(e[0],revoked=True),),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'INDEPENDENT_RUN_EVIDENCE_REQUIRED' in x.reasons
    elif k==23:
        x=m.evaluate(r,p,s,(replace(e[0],verified=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==24:
        x=m.evaluate(r,p,s,(replace(e[0],independent_observer=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==25:
        x=m.evaluate(r,p,s,(replace(e[0],evidence_binding='WRONG'),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==26:
        x=m.evaluate(r,p,s,(replace(e[0],ended_at=NOW-4000,started_at=NOW-4010),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==27:
        x=m.evaluate(r,p,s,(replace(e[0],output_bytes=p.max_output_bytes+1),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'OUTPUT_LIMIT_EXCEEDED' in x.reasons
    elif k==28:
        x=m.evaluate(r,p,s,(replace(e[0],privileged_used=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'PRIVILEGED_USE_OBSERVED' in x.reasons
    elif k==29:
        x=m.evaluate(r,p,s,(replace(e[0],external_service_contacted=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'EXTERNAL_SERVICE_CONTACT_OBSERVED' in x.reasons
    elif k==30:
        known={**{'profile:'+x.profile_id:m.fingerprint(x) for x in s},**{'evidence:'+x.evidence_id:m.fingerprint(x) for x in e}}; plan=m.plan_registry_sync(s,e,known); assert plan.missing_or_changed_profile_ids==() and plan.missing_or_changed_evidence_ids==() and not plan.permission_granted and not plan.production_execution_authorized
    elif k==31:
        x=m.evaluate(r,p,s,e,now=NOW); assert not x.permission_granted and not x.sandbox_execution_started and not x.production_execution_started and not x.real_secret_accessed and not x.network_egress_performed and not x.host_mutation_performed and not x.production_safe_proven and not x.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
