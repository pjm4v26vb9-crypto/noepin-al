import unittest
from dataclasses import replace
import noepin_al_148_destination_trust_matcher as m
B='B'; E='E'
def label(i='D1',s=m.Sensitivity.INTERNAL,binding=B,epoch=E): return m.DataLabel(i,s,(f'SRC-{i}',),binding,epoch)
def dest(**kw):
    d=dict(destination_id='DST',verified=True,trust_tier=m.TrustTier.HIGH,owner_org='ORG',region='JP',service_type='API',service_identity_digest='digest',spoof_suspected=False,binding=B,state_epoch=E); d.update(kw); return m.DestinationIdentity(**d)
def alt(i='ALT',**kw):
    d=dict(destination_id=i,verified=True,trust_tier=m.TrustTier.HIGH,owner_org='ORG',region='JP',service_type='API'); d.update(kw); return m.AlternativeDestination(**d)
def policy(**kw):
    d=dict(allowed_regions=('JP',),allowed_owner_orgs=('ORG',),minimum_trust_public=m.TrustTier.LOW,minimum_trust_internal=m.TrustTier.MEDIUM,minimum_trust_confidential=m.TrustTier.HIGH,minimum_trust_secret=m.TrustTier.CRITICAL,allowed_service_types=('API','STORAGE'),alternatives=(),binding=B,state_epoch=E); d.update(kw); return m.NetworkServicePolicy(**d)
def req(**kw):
    d=dict(request_id='R',data_labels=(label(),),destination=dest(),policy=policy(),binding=B,state_epoch=E); d.update(kw); return m.DestinationRequest(**d)
def neg(r):
    return (r.destination_trust_promoted_to_permission,r.destination_identity_promoted_to_identity_authority,r.alternative_destination_routed,r.data_transfer_executed,r.external_send_executed,r.dns_resolution_executed,r.service_call_executed,r.tool_invoked,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_labels_fingerprint=st.labels_fingerprint,current_destination_fingerprint=st.destination_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.TRUSTED_DESTINATION_CANDIDATE and not any(neg(r))
    if k==1:
        r=m.evaluate(req(destination=dest(verified=False,trust_tier=m.TrustTier.UNKNOWN))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.UNKNOWN_DESTINATION
    if k==2:
        r=m.evaluate(req(data_labels=(label(s=m.Sensitivity.CONFIDENTIAL),),destination=dest(trust_tier=m.TrustTier.MEDIUM))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.TRUST_INSUFFICIENT
    if k==3:
        r=m.evaluate(req(destination=dest(region='US'))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.REGION_VIOLATION
    if k==4:
        r=m.evaluate(req(data_labels=(label(s=m.Sensitivity.PUBLIC),),destination=dest(verified=False,trust_tier=m.TrustTier.UNKNOWN))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_DESTINATION
    if k==5:
        r=m.evaluate(req(destination=dest(spoof_suspected=True))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SPOOF_SUSPECTED
    if k==6:
        p=policy(alternatives=(alt(),)); r=m.evaluate(req(destination=dest(region='US'),policy=p)); return 'ALT' in r.alternative_destination_ids and r.next_action==m.NextAction.USE_ALTERNATIVE_CANDIDATE and not r.alternative_destination_routed
    if k==7:
        r=m.evaluate(req(destination=dest(owner_org='OTHER'))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.OWNERSHIP_MISMATCH
    if k==8:
        r=m.evaluate(req(data_labels=(label(s=m.Sensitivity.CONFIDENTIAL),),destination=dest(owner_org='OTHER'))); return r.decision==m.Decision.DENY
    if k==9:
        r=m.evaluate(req(destination=dest(service_type='EMAIL'))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.POLICY_MISMATCH
    if k==10:
        q=req(data_labels=(label('A',m.Sensitivity.PUBLIC),label('B',m.Sensitivity.SECRET)),destination=dest(trust_tier=m.TrustTier.CRITICAL)); r=m.evaluate(q); return r.effective_sensitivity==m.Sensitivity.SECRET and r.decision==m.Decision.ALLOW
    if k==11:
        return m.evaluate(req(data_labels=())).engine_state==m.EngineState.INVALID
    if k==12:
        return m.evaluate(req(destination=dest(binding='X'))).engine_state==m.EngineState.INVALID
    if k==13:
        return m.evaluate(req(policy=policy(allowed_regions=('JP','JP')))).engine_state==m.EngineState.INVALID
    if k==14:
        q=req(); st=m.prepare_state(q,B,E); return prep(st)==st.result
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=False,current_labels_fingerprint=st.labels_fingerprint,current_destination_fingerprint=st.destination_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.engine_state==m.EngineState.INVALID
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,destination=dest(region='US')); st2=m.prepare_state(q2,B,E); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return d.destination_changed and p.missing_or_changed_record_ids==('DESTINATION_IDENTITY',) and not p.full_resend_required
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,policy=policy(allowed_regions=('JP','US'))); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('NETWORK_SERVICE_POLICY',)
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,data_labels=(label(s=m.Sensitivity.CONFIDENTIAL),)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('DATA_LABELS',)
    if k==19:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and not any(neg(r))
    return False
class TestAL148(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL148,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
