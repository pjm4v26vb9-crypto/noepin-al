import unittest
from dataclasses import replace
import noepin_al_119_blast_radius_minimizer as m
class TestAL119(unittest.TestCase): pass

def scenario(k,rep):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); neg=(r.selected_action_promoted_to_permission,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
        return r.decision==m.Decision.ALLOW and r.selected_action_candidate=='LOCAL_PATCH' and r.affected_set==('FILE_A',) and r.next_gate_candidate and not any(neg)
    if k==1:
        r=m.evaluate(q); ev={x.action_id:x for x in r.evaluations}; return ev['SHARED_CONFIG_CHANGE'].blast_radius_score>ev['LOCAL_PATCH'].blast_radius_score and ev['SHARED_CONFIG_CHANGE'].critical_shared_count==1
    if k==2:
        a=m.CandidateAction('UNKNOWN',('MISSING',),1.0,True,b,e); r=m.evaluate(replace(q,candidates=(a,))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_RADIUS
    if k==3:
        a=m.CandidateAction('UNKNOWN',('MISSING',),1.0,True,b,e); r=m.evaluate(replace(q,candidates=(a,q.candidates[0]))); return r.decision==m.Decision.ALLOW and r.selected_action_candidate=='LOCAL_PATCH' and 'UNKNOWN' in r.unknown_radius_candidates
    if k==4:
        a1=m.CandidateAction('B',('FILE_A',),1.0,False,b,e); a2=m.CandidateAction('A',('FILE_B',),1.0,False,b,e); r=m.evaluate(replace(q,candidates=(a1,a2))); return r.selected_action_candidate=='A'
    if k==5:
        p=replace(q.policy,high_radius_threshold=.1); r=m.evaluate(replace(q,policy=p,candidates=q.candidates[:3])); return r.decision==m.Decision.HUMAN_APPROVAL and r.all_goal_candidates_large_radius and not r.next_gate_candidate
    if k==6:
        c=tuple(replace(a,goal_coverage=.2) for a in q.candidates); r=m.evaluate(replace(q,candidates=c)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NO_GOAL_SATISFYING_ACTION
    if k==7:
        c=(q.candidates[0],replace(q.candidates[0],goal_coverage=.95)); return m.evaluate(replace(q,candidates=c)).decision==m.Decision.HOLD
    if k==8:
        rr=(q.resources[0],replace(q.resources[0],criticality=2)); return m.evaluate(replace(q,resources=rr)).decision==m.Decision.HOLD
    if k==9:
        edges=q.dependency_graph+(m.DependencyEdge('SERVICE_A','SHARED_CONFIG'),); r=m.evaluate(replace(q,dependency_graph=edges)); return r.decision==m.Decision.ALLOW and r.selected_action_candidate=='LOCAL_PATCH'
    if k==10:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_candidate_fingerprint=st.candidate_fingerprint,current_resource_fingerprint=st.resource_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return r==m.evaluate(q)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_candidate_fingerprint=st.candidate_fingerprint,current_resource_fingerprint=st.resource_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return r.decision==m.Decision.HOLD
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint='bad',current_candidate_fingerprint=st.candidate_fingerprint,current_resource_fingerprint=st.resource_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return r.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); q2=replace(q,candidates=(replace(q.candidates[0],goal_coverage=.95),)+q.candidates[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_candidates)==1 and d.changed_candidates[0].action_id=='LOCAL_PATCH'
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); q2=replace(q,resources=(replace(q.resources[0],criticality=1.5),)+q.resources[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('RESOURCE:FILE_A',) and not sp.full_resend_required
    if k==15:
        rr=tuple(replace(r,authority_boundary=False) if r.resource_id=='SHARED_CONFIG' else r for r in q.resources); r1=m.evaluate(q); r2=m.evaluate(replace(q,resources=rr)); e1={x.action_id:x for x in r1.evaluations}; e2={x.action_id:x for x in r2.evaluations}; return e2['SHARED_CONFIG_CHANGE'].blast_radius_score<e1['SHARED_CONFIG_CHANGE'].blast_radius_score
    if k==16:
        r1=m.evaluate(q); r2=m.evaluate(replace(q,candidates=tuple(reversed(q.candidates)),resources=tuple(reversed(q.resources)),dependency_graph=tuple(reversed(q.dependency_graph)))); return m._canon(r1)==m._canon(r2)
    if k==17:
        a=replace(q.candidates[0],binding='BAD'); return m.evaluate(replace(q,candidates=(a,)+q.candidates[1:])).decision==m.Decision.HOLD
    if k==18:
        p=replace(q.policy,high_radius_threshold=float('nan')); return m.evaluate(replace(q,policy=p)).decision==m.Decision.HOLD
    if k==19:
        a=m.default_evaluation(); b2=m.default_evaluation(); return m._canon(a)==m._canon(b2) and m._fp(a)==m._fp(b2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL119,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
