from dataclasses import replace
import unittest
import noepin_al_188_safety_suite_distribution as m
A=m.default_artifacts(); R=m.default_request()
def all_false(r): return all(not getattr(r,n) for n in m.FALSE_FIELDS) and not r.authoritative
def sc(k,round_no):
    req=replace(R,request_id=f'SUITE-{round_no}-{k}',context_fingerprint=f'ctx-{round_no}',policy_fingerprint=f'pol-{round_no}')
    if k==0:
        r=m.evaluate(req,A); return r.decision==m.Decision.ALLOW and r.controls_verified==61 and r.next_gate_candidate and all_false(r)
    if k==1:return m.evaluate(replace(req,request_id=''),A).escalation==m.Escalation.MISSING_FIELD
    if k==2:return m.evaluate(replace(req,schema_version='2.0'),A).escalation==m.Escalation.SCHEMA_MISMATCH
    if k==3:return m.evaluate(req,A[:-1]).escalation==m.Escalation.CONTROL_REGISTRY_GAP
    if k==4:return m.evaluate(req,A+(A[-1],)).escalation==m.Escalation.CONTROL_REGISTRY_GAP
    if k==5:
        bad=list(A); bad[0]=replace(bad[0],sha256='0'*64); return m.evaluate(req,tuple(bad)).escalation==m.Escalation.CONTROL_ARTIFACT_MISMATCH
    if k==6:
        bad=list(A); bad[1]=replace(bad[1],verified=False); return m.evaluate(req,tuple(bad)).escalation==m.Escalation.CONTROL_ARTIFACT_MISMATCH
    if k==7:return m.evaluate(replace(req,enabled_controls=()),A).escalation==m.Escalation.INVALID_CONTROL_SELECTION
    if k==8:return m.evaluate(replace(req,enabled_controls=(1,1)),A).escalation==m.Escalation.INVALID_CONTROL_SELECTION
    if k==9:return m.evaluate(replace(req,enabled_controls=(62,)),A).escalation==m.Escalation.INVALID_CONTROL_SELECTION
    if k==10:return m.evaluate(replace(req,gateway_decision='DENY'),A).decision==m.Decision.DENY
    if k==11:return m.evaluate(replace(req,gateway_decision='HOLD'),A).decision==m.Decision.HOLD
    if k==12:return m.evaluate(replace(req,gateway_decision='HUMAN_APPROVAL'),A).decision==m.Decision.HUMAN_APPROVAL
    if k==13:return m.evaluate(replace(req,gateway_decision='MAYBE'),A).escalation==m.Escalation.INVALID_DECISION
    if k==14:return m.evaluate(replace(req,control_decisions=((1,'DENY'),)),A).decision==m.Decision.DENY
    if k==15:return m.evaluate(replace(req,control_decisions=((2,'HOLD'),)),A).decision==m.Decision.HOLD
    if k==16:return m.evaluate(replace(req,control_decisions=((3,'HUMAN_APPROVAL'),)),A).decision==m.Decision.HUMAN_APPROVAL
    if k==17:return m.evaluate(replace(req,control_decisions=((1,'MAYBE'),)),A).escalation==m.Escalation.INVALID_DECISION
    if k==18:return m.evaluate(replace(req,enabled_controls=(1,2,3),control_decisions=((1,'ALLOW'),(2,'ALLOW'),(3,'ALLOW'))),A).decision==m.Decision.ALLOW
    if k==19:
        r=m.evaluate(req,A); return r.controls_total==61 and r.controls_enabled==61 and r.registry_complete
    if k==20:
        a=m.evaluate(req,A); b=m.evaluate(req,A); return m.fingerprint(a)==m.fingerprint(b)
    if k==21:
        p=m.prepare_state(req,A); r=m.evaluate_prepared(p,integrity_validated=True,current_request=req,current_artifacts=A,current_result_fingerprint=p.result_fingerprint,current_integrity_fingerprint=p.integrity_fingerprint); return r.prepared_state_reused and r.decision==m.Decision.ALLOW
    if k==22:
        p=m.prepare_state(req,A); r=m.evaluate_prepared(p,integrity_validated=False,current_request=req,current_artifacts=A,current_result_fingerprint=p.result_fingerprint,current_integrity_fingerprint=p.integrity_fingerprint); return r.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==23:
        p=m.prepare_state(req,A); rr=replace(req,context_fingerprint=req.context_fingerprint+'x'); r=m.evaluate_prepared(p,integrity_validated=True,current_request=rr,current_artifacts=A,current_result_fingerprint=p.result_fingerprint,current_integrity_fingerprint=p.integrity_fingerprint); return r.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==24:
        p=m.prepare_state(req,A); bad=list(A); bad[0]=replace(bad[0],verified=False); r=m.evaluate_prepared(p,integrity_validated=True,current_request=req,current_artifacts=tuple(bad),current_result_fingerprint=p.result_fingerprint,current_integrity_fingerprint=p.integrity_fingerprint); return r.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==25:
        known={'REQUEST':m.request_fingerprint(req),'CONTROL_ARTIFACT_REGISTRY':m.artifacts_fingerprint(A)}; d=m.make_delta(req,A,known); return d.missing_or_changed_fields==('SUITE_DISTRIBUTION',) and not d.full_revalidation_required
    if k==26:
        d=m.make_delta(req,A,{}); return len(d.missing_or_changed_fields)==3 and d.full_revalidation_required
    if k==27:
        known={'REQUEST':m.request_fingerprint(req),'CONTROL_ARTIFACT_REGISTRY':m.artifacts_fingerprint(A),'SUITE_DISTRIBUTION':m._hash({'suite_zip':m.SUITE_ZIP_SHA256,'wheel':m.WHEEL_SHA256})}; d=m.make_delta(req,A,known); return not d.missing_or_changed_fields
    if k==28:return m.request_fingerprint(req)!=m.request_fingerprint(replace(req,policy_fingerprint='x'))
    if k==29:return m.artifacts_fingerprint(A)!=m.artifacts_fingerprint(tuple(reversed(A)))
    if k==30:return m.SUITE_ZIP_SHA256=='25c08aa1fbb16ce0c9f8111a3f212d2214987d9568b6764095d2bc7f87de58ae'
    if k==31:return m.WHEEL_SHA256=='e487143ce659812aceae6d928981dd298bc4f34dded1afcd394e57eae2070378'
    if k==32:return len(m.EXPECTED_BY_ID)==61 and set(m.EXPECTED_BY_ID)==set(range(1,62))
    if k==33:return len({x.sha256 for x in A})==61
    if k==34:return all(len(x.sha256)==64 for x in A)
    if k==35:
        r=m.default_evaluation(); return r.request_id=='SUITE-188-A' and r.decision==m.Decision.ALLOW and all_false(r)
    if k==36:
        r=m.evaluate(req,A); return not r.permission_granted and not r.permit_issued and not r.credential_minted
    if k==37:
        r=m.evaluate(req,A); return not r.dcsr_bypassed_control and not r.dcsr_bypassed_gateway and not r.dcsr_minted_permission
    if k==38:
        r=m.evaluate(req,A); return r.next_action==m.NextAction.CONTINUE_TO_EXTERNAL_POLICY_PERMIT_CANDIDATE and not r.action_executed
    if k==39:
        r=m.evaluate(req,A); return len(r.distribution_manifest_fingerprint)==64 and r.escalation==m.Escalation.NONE
    return False
class T(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(sc(i%40,i//40))
    return t
for i in range(160): setattr(T,f'test_case_{i:03d}',mk(i))
if __name__=='__main__':unittest.main(verbosity=2)
