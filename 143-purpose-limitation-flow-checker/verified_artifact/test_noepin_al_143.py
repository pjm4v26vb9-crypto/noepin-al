import unittest
from dataclasses import replace
import noepin_al_143_purpose_limitation_flow_checker as m
B='B'; E='E'
def data(k='D',purposes=('care:medication',),sens=m.Sensitivity.SENSITIVE): return m.DataItem(k,tuple(purposes),sens,(f'SRC-{k}',),B,E)
def cp(cons=(),pol=(),re=False,known=True): return m.ConsentPolicy(tuple(cons),tuple(pol),re,known)
def req(ds=(),purpose='care:medication',use='use',c=None): return m.PurposeRequest('R',tuple(ds),purpose,use,c or cp(),B,E)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.USE_ALLOWED_CANDIDATE and not r.data_use_executed
    if k==1:
        r=m.evaluate(req([data(purposes=('care',))],purpose='care:medication')); return r.decision==m.Decision.ALLOW and r.findings[0].match_kind==m.MatchKind.INCLUDED
    if k==2:
        r=m.evaluate(req([data(purposes=('care:*',))],purpose='care:billing')); return r.decision==m.Decision.ALLOW and r.findings[0].match_kind==m.MatchKind.INCLUDED
    if k==3:
        r=m.evaluate(req([data()],purpose='marketing')); return r.decision==m.Decision.DENY and r.blocked_item_ids==('D',)
    if k==4:
        r=m.evaluate(req([data()],purpose='research',c=cp(re=True))); return r.decision==m.Decision.HUMAN_APPROVAL and r.required_consent_item_ids==('D',) and not r.approval_executed
    if k==5:
        r=m.evaluate(req([data()],purpose='research',c=cp(cons=('research',)))); return r.decision==m.Decision.ALLOW and r.findings[0].match_kind==m.MatchKind.CONSENT_EXCEPTION
    if k==6:
        r=m.evaluate(req([data()],purpose='audit',c=cp(pol=('audit',)))); return r.decision==m.Decision.ALLOW and r.findings[0].match_kind==m.MatchKind.POLICY_EXCEPTION
    if k==7:
        r=m.evaluate(req([data()],purpose='research',c=cp(known=False))); return r.decision==m.Decision.HOLD and r.findings[0].match_kind==m.MatchKind.UNKNOWN
    if k==8:
        r=m.evaluate(req([data('A',('care',)),data('B',('billing',))],purpose='care')); return r.decision==m.Decision.DENY and r.allowed_item_ids==('A',) and r.blocked_item_ids==('B',)
    if k==9:
        r=m.evaluate(req([data('A',('care','care:medication'))],purpose='care:medication')); return r.decision==m.Decision.ALLOW
    if k==10:
        return m.evaluate(req([data('D'),data('D')])).engine_state==m.EngineState.INVALID
    if k==11:
        d=replace(data(),binding='OTHER'); return m.evaluate(req([d])).engine_state==m.EngineState.INVALID
    if k==12:
        q=replace(req([data()]),current_purpose=' '); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint=st.data_fingerprint,current_purpose_fingerprint=st.purpose_fingerprint,current_consent_policy_fingerprint=st.consent_policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return m.validate_prepared_integrity(st) and r==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_data_fingerprint=st.data_fingerprint,current_purpose_fingerprint=st.purpose_fingerprint,current_consent_policy_fingerprint=st.consent_policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint='BAD',current_purpose_fingerprint=st.purpose_fingerprint,current_consent_policy_fingerprint=st.consent_policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,data_items=(replace(q.data_items[0],provenance_ids=('SRC-143-A','SRC-NEW')),)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_data_items)==1 and p.missing_or_changed_record_ids==('DATA:DATA-143-A',) and not p.full_resend_required
    if k==17:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,current_purpose='care:billing'); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); p=m.plan_missing_only(st,st2); return 'PURPOSE_CONTEXT' in p.missing_or_changed_record_ids
    if k==18:
        r=m.default_evaluation(); neg=(r.purpose_match_promoted_to_permission,r.consent_evidence_promoted_to_approval,r.policy_exception_promoted_to_authority,r.data_use_executed,r.consent_requested_externally,r.external_send_executed,r.tool_invoked,r.memory_write_performed,r.label_write_performed,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_consent,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==19:
        r=m.evaluate(req([data('A',('care',),m.Sensitivity.NON_SENSITIVE),data('B',('care:medication',),m.Sensitivity.PERSONAL)],purpose='care:medication')); return r.decision==m.Decision.ALLOW and set(r.allowed_item_ids)=={'A','B'}
    return False
class TestAL143(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL143,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
