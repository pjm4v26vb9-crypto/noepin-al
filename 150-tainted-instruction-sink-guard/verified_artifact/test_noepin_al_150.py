import unittest
from dataclasses import replace
import noepin_al_150_tainted_instruction_sink_guard as m
B='B'; E='E'
def inst(source_trusted=False,chain=('EXTRACT','SUMMARIZE','PLAN')): return m.InstructionNode('I','intent','SRC',source_trusted,chain,B,E)
def taint(kind=m.TaintKind.UNTRUSTED_INSTRUCTION,through=('EXTRACT','SUMMARIZE','PLAN'),confidence=1.0,label='T'): return m.TaintLabel(label,kind,'SRC',through,confidence,B,E)
def sink(cls=m.SinkClass.TOOL_EXECUTE,mutating=True,external=True): return m.TargetSink('S',cls,'target://x',mutating,external,B,E)
def auth(explicit=False,classes=(),current=False,ii='I',si='S'): return m.UserAuthorizationEvidence('A' if explicit else 'NONE',explicit,classes,ii,si,current,B,E)
def req(i=None,t=None,s=None,a=None,complete=True): return m.SinkGuardRequest('R',i or inst(),tuple(t if t is not None else [taint()]),s or sink(),a or auth(),complete,B,E)
def neg(r):
    return (r.taint_promoted_to_truth,r.user_authorization_promoted_to_permission,r.sink_decision_executed,r.sanitization_executed,r.tool_invoked,
    r.file_write_executed,r.network_send_executed,r.read_executed,r.policy_modified,r.authorization_modified,r.dlp_replaced,r.authentication_replaced,
    r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,
    r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,
    r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
def prepared(st): return m.evaluate_prepared(st,integrity_validated=True,current_instruction_fingerprint=st.instruction_fingerprint,current_taint_fingerprint=st.taint_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_authorization_fingerprint=st.authorization_fingerprint,current_path_fingerprint=st.path_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DANGEROUS_TAINT_TO_SINK and r.engine_state==m.EngineState.TAINTED_DANGEROUS_SINK_CANDIDATE and not any(neg(r))
    if k==1:
        i=inst(chain=('FETCH','SUMMARIZE','PLAN')); t=taint(through=i.transformation_chain); r=m.evaluate(req(i=i,t=[t])); return r.decision==m.Decision.DENY and 'TRANSFORM:SUMMARIZE' in r.taint_path
    if k==2:
        s=sink(m.SinkClass.READ,False,False); r=m.evaluate(req(t=[taint(m.TaintKind.DATA_ONLY)],s=s)); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.SAFE_SINK_CANDIDATE
    if k==3:
        a=auth(True,(m.SinkClass.TOOL_EXECUTE,),True); r=m.evaluate(req(a=a)); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.REAUTHORIZED_SINK_CANDIDATE and not r.permission_granted
    if k==4:
        r=m.evaluate(req(complete=False)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.TAINT_PATH_UNKNOWN
    if k==5:
        s=sink(m.SinkClass.FILE_WRITE,True,False); r=m.evaluate(req(s=s)); return r.decision==m.Decision.DENY
    if k==6:
        s=sink(m.SinkClass.NETWORK_SEND,False,True); r=m.evaluate(req(s=s)); return r.decision==m.Decision.DENY
    if k==7:
        t=taint(m.TaintKind.TRUSTED_INSTRUCTION); r=m.evaluate(req(t=[t])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.USER_AUTHORIZATION_REQUIRED
    if k==8:
        t=taint(m.TaintKind.TRUSTED_INSTRUCTION); a=auth(True,(m.SinkClass.TOOL_EXECUTE,),True); r=m.evaluate(req(t=[t],a=a)); return r.decision==m.Decision.ALLOW
    if k==9:
        t=taint(m.TaintKind.DATA_ONLY); r=m.evaluate(req(t=[t])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DATA_TAINT_AT_MUTATING_SINK
    if k==10:
        s=sink(m.SinkClass.READ,False,False); r=m.evaluate(req(t=[],s=s)); return r.decision==m.Decision.ALLOW
    if k==11:
        a=auth(True,(m.SinkClass.TOOL_EXECUTE,),True,ii='OTHER'); r=m.evaluate(req(a=a)); return r.engine_state==m.EngineState.INVALID
    if k==12:
        bad=replace(inst(),binding='X'); return m.evaluate(req(i=bad)).engine_state==m.EngineState.INVALID
    if k==13:
        return m.evaluate(req(t=[taint(confidence=1.2)])).engine_state==m.EngineState.INVALID
    if k==14:
        q=req(); st=m.prepare_state(q,B,E); return prepared(st)==st.result
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_instruction_fingerprint=st.instruction_fingerprint,current_taint_fingerprint=st.taint_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_authorization_fingerprint=st.authorization_fingerprint,current_path_fingerprint=st.path_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); q2=req(t=[taint(m.TaintKind.DATA_ONLY)]); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('TAINT_LABELS',) and not p.full_resend_required
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=req(s=sink(m.SinkClass.FILE_WRITE,True,False)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('TARGET_SINK',)
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=req(a=auth(True,(m.SinkClass.TOOL_EXECUTE,),True)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('USER_AUTHORIZATION_EVIDENCE',)
    if k==19:
        r=m.default_evaluation(); return r.decision==m.Decision.DENY and r.next_action==m.NextAction.REJECT_SINK_CANDIDATE and r.escalation==m.Escalation.DANGEROUS_TAINT_TO_SINK and r.engine_state==m.EngineState.TAINTED_DANGEROUS_SINK_CANDIDATE and r.next_gate_candidate and not any(neg(r))
    return False
class TestAL150(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL150,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
