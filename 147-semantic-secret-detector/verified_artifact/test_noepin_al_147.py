import unittest
from dataclasses import replace
import noepin_al_147_semantic_secret_detector as m
B='B'; E='E'
def frag(fid='F1',content='hello world',role='TEXT',prov=('S1',),**kw):
    d=dict(fragment_id=fid,content=content,role=role,provenance_ids=prov,binding=B,state_epoch=E); d.update(kw); return m.ContentFragment(**d)
def pat(**kw):
    d=dict(pattern_id='P1',regex=r'\bKEY_[A-Z0-9]{12,}\b',secret_class=m.SecretClass.API_KEY,enabled=True,binding=B,state_epoch=E); d.update(kw); return m.KnownSecretPattern(**d)
def usage(**kw):
    d=dict(external_target=False,auth_usage_expected=False,public_credential_declared=False,policy_verified=True,context_tags=('test',),binding=B,state_epoch=E); d.update(kw); return m.UsageSemantics(**d)
def req(**kw):
    d=dict(request_id='Q',fragments=(frag(),),context='test context',known_patterns=(pat(),),usage=usage(),semantic_coverage_known=True,binding=B,state_epoch=E); d.update(kw); return m.SecretRequest(**d)
def neg(r):
    return (r.secret_label_promoted_to_truth,r.confidence_promoted_to_safety_proof,r.redaction_plan_executed,r.content_mutated,r.external_send_executed,r.disclosure_executed,r.credential_used,r.tool_invoked,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
def prep(st):
    return m.evaluate_prepared(st,integrity_validated=True,current_fragments_fingerprint=st.fragments_fingerprint,current_context_fingerprint=st.context_fingerprint,current_patterns_fingerprint=st.patterns_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.CLEAR_CANDIDATE and not r.secret_labels
    if k==1:
        q=req(fragments=(frag(content='KEY_ABCDEFGHIJKLMN'),),usage=usage(external_target=True)); r=m.evaluate(q); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.KNOWN_SECRET
    if k==2:
        q=req(fragments=(frag(content='recovery code: 8241-9912'),),usage=usage(external_target=True,auth_usage_expected=True)); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SEMANTIC_SECRET
    if k==3:
        fs=(frag('F1','internal login https://internal.example/login',prov=('S1',)),frag('F2','access token=ABCDEF123456',prov=('S2',))); q=req(fragments=fs,usage=usage(external_target=True)); r=m.evaluate(q); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SPLIT_SECRET
    if k==4:
        q=req(fragments=(frag(content='ordinary configuration value=blue'),)); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and not r.secret_labels
    if k==5:
        q=req(fragments=(frag(content='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789xyz'),)); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.LOW_CONFIDENCE
    if k==6:
        q=req(fragments=(frag(content='api key: demo-only'),),usage=usage(public_credential_declared=True,auth_usage_expected=True)); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.PUBLIC_CREDENTIAL_POLICY
    if k==7:
        q=req(fragments=(frag(content='password=not-used-here'),),usage=usage(external_target=True,auth_usage_expected=True),semantic_coverage_known=False); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.LOW_CONFIDENCE
    if k==8:
        q=req(fragments=(frag(content='client secret = abc'),),usage=usage(auth_usage_expected=True)); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.SECRET_DETECTED_CANDIDATE and not r.credential_used
    if k==9:
        q=req(known_patterns=(pat(enabled=False),),fragments=(frag(content='KEY_ABCDEFGHIJKLMN'),)); r=m.evaluate(q); return r.decision in {m.Decision.ALLOW,m.Decision.HOLD} and all('KNOWN_PATTERN:' not in e for x in r.secret_labels for e in x.evidence)
    if k==10:
        q=req(fragments=(frag('F1','username=alice'),frag('F2','password=secret')) ,usage=usage(external_target=True)); r=m.evaluate(q); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SPLIT_SECRET
    if k==11:
        q=req(fragments=(frag('F1','token=abc'),frag('F2','token=def'))); r=m.evaluate(q); return r.redaction_plan is not None and not r.redaction_plan_executed
    if k==12:
        return m.evaluate(req(fragments=())).engine_state==m.EngineState.INVALID
    if k==13:
        return m.evaluate(req(fragments=(frag(binding='X'),))).engine_state==m.EngineState.INVALID
    if k==14:
        return m.evaluate(req(known_patterns=(pat(regex='['),))).engine_state==m.EngineState.INVALID
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); return prep(st)==st.result
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=False,current_fragments_fingerprint=st.fragments_fingerprint,current_context_fingerprint=st.context_fingerprint,current_patterns_fingerprint=st.patterns_fingerprint,current_usage_fingerprint=st.usage_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.engine_state==m.EngineState.INVALID
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,context='changed'); st2=m.prepare_state(q2,B,E); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return d.context_changed and p.missing_or_changed_record_ids==('CONTEXT',) and not p.full_resend_required
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,usage=usage(external_target=True)); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('USAGE_SEMANTICS',)
    if k==19:
        return not any(neg(m.default_evaluation()))
    return False
class TestAL147(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL147,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
