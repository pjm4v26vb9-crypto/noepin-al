import unittest
from dataclasses import replace
import noepin_al_107_safe_alternative_path_enumerator as m

class TestAL107(unittest.TestCase): pass

def _scenario(k,variant):
    p=m.default_policy(); q=m.default_request(); edges=list(m.default_edges()); f=m.default_forbidden_nodes(); b=p.binding; e=p.state_epoch
    if variant%2: q=replace(q,request_id=f'REQ-107-{variant}')
    if k==0:
        z=m.evaluate(q,tuple(edges),f,p); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.SAFE_PATHS_CANDIDATE and z.returned_k>=2 and not z.permission_granted
    if k==1:
        one=tuple(x for x in edges if x.edge_id in ('E-SA','E-AG','E-DIRECT-UNSAFE')); z=m.evaluate(q,one,f,p); return z.returned_k==1 and z.safe_paths[0].edge_ids==('E-SA','E-AG')
    if k==2:
        bad=tuple(replace(x,hard_constraint_passed=False) for x in edges); z=m.evaluate(q,bad,f,p); return z.decision==m.Decision.HOLD and z.returned_k==0
    if k==3:
        # same cost, lower risk path must rank first
        es=(m.GraphEdge('A1','START','A',1,1,.4,.9,True,True,'V1','A1',True,b,e),m.GraphEdge('A2','A','GOAL',1,1,.4,.9,True,True,'V1','A2',True,b,e),m.GraphEdge('B1','START','B',1,1,.1,.8,True,True,'V1','B1',True,b,e),m.GraphEdge('B2','B','GOAL',1,1,.1,.8,True,True,'V1','B2',True,b,e)); z=m.evaluate(q,es,(),p); return z.safe_paths[0].total_risk<z.safe_paths[-1].total_risk
    if k==4:
        z=m.evaluate(replace(q,k=1),tuple(edges),f,p); return z.returned_k==1
    if k==5:
        z=m.evaluate(q,tuple(edges),('A','B','C'),p); return z.decision==m.Decision.HOLD
    if k==6:
        # unsafe direct edge must be pruned even if cheapest
        z=m.evaluate(q,tuple(edges),f,p); return any(x[0]=='E-DIRECT-UNSAFE' for x in z.pruned_reasons) and all('E-DIRECT-UNSAFE' not in sp.edge_ids for sp in z.safe_paths)
    if k==7:
        # reversibility is tie-break after cost/risk/time
        es=(m.GraphEdge('A1','START','A',1,1,.1,.5,True,True,'V1','A1',True,b,e),m.GraphEdge('A2','A','GOAL',1,1,.1,.5,True,True,'V1','A2',True,b,e),m.GraphEdge('B1','START','B',1,1,.1,.9,True,True,'V1','B1',True,b,e),m.GraphEdge('B2','B','GOAL',1,1,.1,.9,True,True,'V1','B2',True,b,e)); z=m.evaluate(q,es,(),p); return z.safe_paths[0].reversibility==.9
    if k==8:
        z=m.evaluate(replace(q,max_total_cost=1.0),tuple(edges),f,p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(replace(q,max_hops=1),tuple(edges),f,p); return z.decision==m.Decision.HOLD
    if k==10:
        z=m.evaluate(q,tuple(edges),f,replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==11:
        st=m.prepare_state(q,tuple(edges),f,p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,tuple(edges),f,p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_pareto_fingerprint=st.pareto_fingerprint); return z==m.evaluate(q,tuple(edges),f,p)
    if k==13:
        st=m.prepare_state(q,tuple(edges),f,p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_pareto_fingerprint=st.pareto_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,tuple(edges),f,p,binding=b,state_epoch=e); e2=tuple(replace(x,risk=x.risk+.01) if x.edge_id=='E-SA' else x for x in edges); st2=m.prepare_state(q,e2,f,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_edges)==1 and sp.missing_or_changed_record_ids==('EDGE:E-SA',)
    if k==15:
        z=m.default_evaluation(); neg=(z.paths_promoted_to_permission,z.permission_granted,z.authority_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==16:
        return m.evaluate(q,tuple(edges),f,p)==m.evaluate(q,tuple(reversed(edges)),f,p)
    if k==17:
        z=m.evaluate(replace(q,risk_class=m.RiskClass.HIGH,max_total_risk=2.0),tuple(edges),f,replace(p,human_review_risk=.2)); return z.decision==m.Decision.HUMAN_APPROVAL and z.next_action==m.NextAction.HUMAN_REVIEW_CANDIDATE and not z.permission_granted
    if k==18:
        cyc=edges+[m.GraphEdge('E-AS','A','START',.1,.1,.1,1,True,True,'V1','FP-AS',True,b,e)]; z=m.evaluate(q,tuple(cyc),f,p); return z.returned_k>=1 and all(len(sp.nodes)==len(set(sp.nodes)) for sp in z.safe_paths)
    if k==19:
        st=m.prepare_state(q,tuple(edges),f,p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',current_frontier_fingerprint=st.frontier_fingerprint,current_pareto_fingerprint=st.pareto_fingerprint); return z.decision==m.Decision.HOLD and z.replan_candidate
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL107,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
