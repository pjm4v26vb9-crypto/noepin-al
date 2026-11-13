import unittest
from dataclasses import replace
import noepin_al_142_semantic_taint_propagation_engine as m
B='B'; E='E'
def data(k='D',labels=(m.TaintLabel.UNTRUSTED,),prov=('SRC',)):
    return m.DataItem(k,tuple(labels),tuple(prov),B,E)
def req(ds=(),ts=(),edges=(),sinks=()):
    return m.TaintRequest('R',tuple(ds),tuple(ts),tuple(edges),tuple(sinks),B,E)
def prop_map(r): return dict(r.propagated_labels)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.DENY and r.engine_state==m.EngineState.RISK_SINK_CANDIDATE and r.next_action==m.NextAction.BLOCK_FLOW_CANDIDATE and not r.execution_sink_invoked
    if k==1:
        q=req([data(labels=(m.TaintLabel.UNTRUSTED,))],[m.Transformation('T',m.TransformKind.SUMMARY,('D',),'O')],[],[]); r=m.evaluate(q); return prop_map(r)['O']==(m.TaintLabel.UNTRUSTED,) and r.decision==m.Decision.ALLOW
    if k==2:
        q=req([data(labels=(m.TaintLabel.EXTERNAL_INSTRUCTION,m.TaintLabel.UNTRUSTED))],[m.Transformation('T',m.TransformKind.PARAPHRASE,('D',),'O')],[m.FlowEdge('O','X')],[m.Sink('X',m.SinkKind.EXECUTION)]); r=m.evaluate(q); return r.decision==m.Decision.DENY
    if k==3:
        q=req([data('A',(m.TaintLabel.SENSITIVE,)),data('B',(m.TaintLabel.UNTRUSTED,))],[m.Transformation('M',m.TransformKind.MERGE,('A','B'),'O')],[],[]); r=m.evaluate(q); return set(prop_map(r)['O'])=={m.TaintLabel.SENSITIVE,m.TaintLabel.UNTRUSTED}
    if k==4:
        q=req([data(labels=(m.TaintLabel.SENSITIVE,m.TaintLabel.UNTRUSTED))],[m.Transformation('S',m.TransformKind.SANITIZER,('D',),'O','EVID-1',(m.TaintLabel.UNTRUSTED,))],[],[]); r=m.evaluate(q); return prop_map(r)['O']==(m.TaintLabel.SENSITIVE,) and r.trace[0].removed_labels==(m.TaintLabel.UNTRUSTED,)
    if k==5:
        q=req([data(labels=(m.TaintLabel.SENSITIVE,))],[m.Transformation('S',m.TransformKind.SANITIZER,('D',),'O')],[],[]); r=m.evaluate(q); return prop_map(r)['O']==(m.TaintLabel.SENSITIVE,)
    if k==6:
        q=req([data(labels=(m.TaintLabel.UNTRUSTED,))],[m.Transformation('U',m.TransformKind.UNKNOWN,('D',),'O')],[],[]); r=m.evaluate(q); return prop_map(r)['O']==(m.TaintLabel.UNTRUSTED,) and r.decision==m.Decision.HOLD and r.unknown_transform_ids==('U',)
    if k==7:
        q=req([data(labels=(m.TaintLabel.SECRET,))],[],[m.FlowEdge('D','X')],[m.Sink('X',m.SinkKind.EXTERNAL)]); r=m.evaluate(q); return r.decision==m.Decision.DENY and r.tainted_sinks[0].severity=='CRITICAL'
    if k==8:
        q=req([data(labels=(m.TaintLabel.SENSITIVE,))],[],[m.FlowEdge('D','X')],[m.Sink('X',m.SinkKind.EXTERNAL)]); r=m.evaluate(q); return r.decision==m.Decision.HOLD and r.tainted_sinks[0].severity=='HIGH'
    if k==9:
        q=req([data(labels=())],[],[m.FlowEdge('D','I')],[m.Sink('I',m.SinkKind.INTERNAL)]); r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.CLEAR_CANDIDATE
    if k==10:
        q=req([data('D'),data('D')],[],[],[]); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==11:
        q=req([replace(data(),binding='OTHER')],[],[],[]); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==12:
        q=req([data()],[m.Transformation('S',m.TransformKind.SUMMARY,('D',),'O','E',(m.TaintLabel.UNTRUSTED,))],[],[]); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint=st.data_fingerprint,current_transform_fingerprint=st.transform_fingerprint,current_flow_fingerprint=st.flow_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return m.validate_prepared_integrity(st) and r==st.result
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=False,current_data_fingerprint=st.data_fingerprint,current_transform_fingerprint=st.transform_fingerprint,current_flow_fingerprint=st.flow_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==15:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); r=m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint='BAD',current_transform_fingerprint=st.transform_fingerprint,current_flow_fingerprint=st.flow_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==16:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); q2=replace(q,data_items=(replace(q.data_items[0],provenance_ids=('SRC-142-A','SRC-NEW')),)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return len(d.changed_data_items)==1 and p.missing_or_changed_record_ids==('DATA:DOC-142-A',) and not p.full_resend_required
    if k==17:
        q=req([data()],[m.Transformation('T',m.TransformKind.SUMMARY,('MISSING',),'O')],[],[]); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==18:
        r=m.default_evaluation(); neg=(r.taint_promoted_to_truth,r.source_promoted_to_authority,r.sanitizer_evidence_promoted_to_safety_proof,r.taint_sink_executed,r.external_send_executed,r.execution_sink_invoked,r.tool_invoked,r.memory_write_performed,r.label_write_performed,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    if k==19:
        q=req([data(labels=(m.TaintLabel.UNTRUSTED,m.TaintLabel.EXTERNAL_INSTRUCTION))],[m.Transformation('A',m.TransformKind.SUMMARY,('D',),'O1'),m.Transformation('B',m.TransformKind.SUMMARY,('O1',),'O2')],[m.FlowEdge('O2','X')],[m.Sink('X',m.SinkKind.TOOL)]); r=m.evaluate(q); return r.decision==m.Decision.DENY and prop_map(r)['O2']==(m.TaintLabel.EXTERNAL_INSTRUCTION,m.TaintLabel.UNTRUSTED) and len(r.trace)==2
    return False
class TestAL142(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL142,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
