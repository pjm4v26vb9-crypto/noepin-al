import unittest
from dataclasses import replace
import noepin_al_145_aggregation_sensitivity_detector as m

B='B'; E='E'
def frag(fid='F1',entity='E1',attrs=(('a','1'),),joins=(('person_id','P1'),),sens=m.Sensitivity.PUBLIC,prov=('S1',),**kw):
    d=dict(fragment_id=fid,entity_id=entity,attributes=attrs,join_values=joins,sensitivity=sens,provenance_ids=prov,binding=B,state_epoch=E); d.update(kw); return m.DataFragment(**d)
def rule(**kw):
    d=dict(rule_id='R1',required_attributes=('a','b'),inferred_fact_type='derived_secret',inferred_sensitivity=m.Sensitivity.CONFIDENTIAL,required_join_key='person_id',enabled=True,binding=B,state_epoch=E); d.update(kw); return m.InferenceRule(**d)
def aud(**kw):
    d=dict(audience_id='A1',external=False,max_allowed_sensitivity=m.Sensitivity.CONFIDENTIAL,policy_verified=True,binding=B,state_epoch=E); d.update(kw); return m.AudienceContext(**d)
def req(**kw):
    fs=(frag('F1',attrs=(('a','1'),),prov=('S1',)),frag('F2',attrs=(('b','2'),),prov=('S2',)))
    d=dict(request_id='Q',fragments=fs,inference_rules=(rule(),),audience=aud(),inference_coverage_known=True,binding=B,state_epoch=E); d.update(kw); return m.AggregationRequest(**d)

def neg(r):
    return (r.inferred_fact_promoted_to_truth,r.aggregate_sensitivity_promoted_to_policy,r.leak_risk_promoted_to_leak_proof,r.disclosure_executed,r.external_send_executed,r.label_mutated,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.tool_invoked,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)

def scenario(k,j):
    if k==0:
        q=req(inference_rules=(),fragments=(frag(),),audience=aud(max_allowed_sensitivity=m.Sensitivity.PUBLIC)); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.aggregate_sensitivity==m.Sensitivity.PUBLIC and not r.inferred_facts
    if k==1:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.aggregate_sensitivity==m.Sensitivity.CONFIDENTIAL and len(r.inferred_facts)==1
    if k==2:
        fs=(frag('F1',attrs=(('a','1'),),joins=(('person_id','P1'),)),frag('F2',attrs=(('b','2'),),joins=(('person_id','P2'),))); r=m.evaluate(req(fragments=fs)); return r.decision==m.Decision.ALLOW and not r.inferred_facts
    if k==3:
        r=m.evaluate(req(audience=aud(external=True,max_allowed_sensitivity=m.Sensitivity.PUBLIC))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.AGGREGATE_SENSITIVITY
    if k==4:
        r=m.evaluate(req(audience=aud(external=True,max_allowed_sensitivity=m.Sensitivity.CONFIDENTIAL))); return r.decision==m.Decision.ALLOW and not r.disclosure_executed
    if k==5:
        r=m.evaluate(req(audience=aud(external=True),inference_coverage_known=False)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_INFERENCE_IMPACT
    if k==6:
        r=m.evaluate(req(audience=aud(policy_verified=False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AUDIENCE_POLICY
    if k==7:
        q=req(fragments=tuple(frag(f'F{i}',attrs=((('a','1') if i%2==0 else ('b','2')),),joins=(('person_id','P1'),),prov=(f'S{i}',)) for i in range(100))); r=m.evaluate(q); return len(r.inferred_facts)==1 and r.aggregate_sensitivity==m.Sensitivity.CONFIDENTIAL
    if k==8:
        q=req(inference_rules=(rule(enabled=False),)); r=m.evaluate(q); return not r.inferred_facts and r.decision==m.Decision.ALLOW
    if k==9:
        q=req(inference_rules=(rule(required_attributes=('a','c')),)); r=m.evaluate(q); return not r.inferred_facts
    if k==10:
        q=req(fragments=(frag(sens=m.Sensitivity.RESTRICTED),),inference_rules=(),audience=aud(max_allowed_sensitivity=m.Sensitivity.CONFIDENTIAL)); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AUDIENCE_POLICY
    if k==11:
        q=req(fragments=(frag(sens=m.Sensitivity.SECRET),),inference_rules=(),audience=aud(external=True,max_allowed_sensitivity=m.Sensitivity.PUBLIC)); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AUDIENCE_POLICY
    if k==12:
        q=req(fragments=()); r=m.evaluate(q); return r.engine_state==m.EngineState.INVALID
    if k==13:
        q=req(fragments=(frag(binding='X'),)); r=m.evaluate(q); return r.engine_state==m.EngineState.INVALID
    if k==14:
        q=req(inference_rules=(rule(state_epoch='X'),)); r=m.evaluate(q); return r.engine_state==m.EngineState.INVALID
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=True,current_fragments_fingerprint=st.fragments_fingerprint,current_rules_fingerprint=st.rules_fingerprint,current_audience_fingerprint=st.audience_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=False,current_fragments_fingerprint=st.fragments_fingerprint,current_rules_fingerprint=st.rules_fingerprint,current_audience_fingerprint=st.audience_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.engine_state==m.EngineState.INVALID
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,fragments=q.fragments+(frag('F3',attrs=(('c','3'),),prov=('S3',)),)); st2=m.prepare_state(q2,B,E); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return d.fragments_changed and p.missing_or_changed_record_ids==('FRAGMENTS',) and not p.full_resend_required
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,audience=aud(max_allowed_sensitivity=m.Sensitivity.RESTRICTED)); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('AUDIENCE_CONTEXT',)
    if k==19:
        return not any(neg(m.default_evaluation()))
    return False

class TestAL145(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL145,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
