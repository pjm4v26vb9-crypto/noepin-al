import unittest
from dataclasses import replace
import noepin_al_184_quantum_transport_interference_simulator as m

def prepared(q,ok=True):
    st=m.prepare_state(q)
    return m.evaluate_prepared(st,integrity_validated=ok,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q)

def scenario(k,rep):
    if k==0:
        x=m.default_evaluation(); return x.decision==m.Decision.ALLOW and x.next_gate_candidate and x.backend_candidate=='CLASSICAL_MODEL_CANDIDATE' and not x.qpu_invoked and not x.action_executed
    if k==1: return m.default_evaluation()==m.default_evaluation()
    if k==2: return m.evaluate(m.make_request(bell_fidelity=.2)).decision==m.Decision.DENY
    if k==3:
        x=m.evaluate(m.make_request(purpose='')); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.MISSING_PURPOSE
    if k==4:
        x=m.evaluate(m.make_request(permission_evidence_present=False)); return x.decision==m.Decision.DENY and x.escalation==m.Escalation.PERMISSION_EVIDENCE_MISSING and not x.permission_granted
    if k==5: return m.evaluate(m.make_request(resource_budget=-1)).decision==m.Decision.DENY
    if k==6: return m.gate_benchmark(1.0,24,10).min_state_fidelity>0.999999999
    if k==7: return m.gate_benchmark(.25,180,10).mean_state_fidelity < m.gate_benchmark(1.0,40,10).mean_state_fidelity-.15
    if k==8:
        d=m.dd_candidates(1.5,.98,.005,1000,1000,.5,8,300,11); z={x.name:x for x in d}; return z['echo'].probability_plus_x>z['free'].probability_plus_x
    if k==9:
        d=m.dd_candidates(.2,.1,.28,1000,1000,.2,8,300,12); z={x.name:x for x in d}; return z['XY8'].probability_plus_x<z['free'].probability_plus_x
    if k==10:
        x=m.evaluate(m.make_request(min_dd_quality=.999999,max_pulses=0)); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.QUALITY_CONSTRAINT_UNSATISFIED
    if k==11:
        r,c=m.route_candidates(m.default_graph(),'A','D',.78,.5,20,10); return bool(r) and r[0].path==('A','B','D') and c>=3
    if k==12:
        r,c=m.route_candidates(m.default_graph(),'A','D',.80,.5,20,10); return not r and c>=3
    if k==13:
        x=m.evaluate(m.make_request(qpu_available=True,estimated_classical_cost=8,estimated_qpu_cost=2)); return x.decision==m.Decision.ALLOW and x.backend_candidate=='QPU_CANDIDATE' and not x.qpu_execution_authorized and not x.qpu_invoked
    if k==14:
        x=m.default_evaluation(); return x.backend_candidate=='CLASSICAL_MODEL_CANDIDATE' and not x.action_executed
    if k==15:
        q=m.default_request(); a=m.evaluate(q); b=prepared(q); return a.decision==b.decision and a.simulation_fingerprint==b.simulation_fingerprint and b.prepared_state_reused
    if k==16:
        q=m.default_request(); st=m.prepare_state(q); x=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint='0'*64,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q); return x.decision==m.Decision.HOLD and x.full_recompute_candidate
    if k==17:
        q=m.default_request(); x=prepared(q,False); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==18:
        a=m.default_request(); b=replace(a,bell_fidelity=.85); d=m.make_delta(a,b); return d.changed_fields==('bell_fidelity',)
    if k==19:
        a=m.default_request(); b=replace(a,bell_fidelity=.85); p=m.plan_missing_only(a,b); return p.missing_or_changed_record_ids==('PARAMETER:bell_fidelity',) and p.metadata_bytes_required>0 and not p.full_resend_required
    if k==20:
        a=m.default_request(); b=replace(a,experiment_id='OTHER'); p=m.plan_missing_only(a,b); return p.full_resend_required and p.missing_or_changed_record_ids==('FULL_EXPERIMENT_STATE',)
    if k==21:
        x=m.default_evaluation(); names=('permission_granted','permit_issued','approval_executed','human_approval_executed','qpu_invoked','qpu_execution_authorized','network_send_executed','tool_invoked','action_executed','action_success','file_write_executed','external_write_performed','unknown_quantum_state_reconstructed','quantum_state_cloned','physical_fidelity_proven','quantum_advantage_proven','world_truth_proven','safety_proven'); return not any(getattr(x,n) for n in names)
    if k==22:
        x=m.evaluate(m.make_request(min_route_fidelity=.81)); return x.decision==m.Decision.HOLD and x.selected_route is None
    if k==23:
        x=m.evaluate(m.make_request(qpu_available=True,permission_evidence_present=False)); return x.decision==m.Decision.DENY and not x.qpu_invoked
    if k==24: return m.evaluate(m.make_request(seed=-1)).decision==m.Decision.DENY
    if k==25: return m.evaluate(m.make_request(gate_trials=0)).decision==m.Decision.DENY
    if k==26: return m.evaluate(m.make_request(t1=0)).decision==m.Decision.DENY
    if k==27: return m.evaluate(m.make_request(graph=())).decision==m.Decision.DENY
    if k==28: return m.gate_benchmark(.8,32,77)==m.gate_benchmark(.8,32,77)
    if k==29: return m.dd_candidates(1,.8,.02,100,100,.6,8,40,88)==m.dd_candidates(1,.8,.02,100,100,.6,8,40,88)
    if k==30:
        q=m.default_request(); st=m.prepare_state(q); changed=replace(q,permission_evidence_present=False); x=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=changed); return x.decision==m.Decision.HOLD and x.full_recompute_candidate
    if k==31:
        x=m.default_evaluation(); return not x.dcsr_reconstructed_unknown_quantum_state and not x.dcsr_invented_measurement and not x.dcsr_improved_hardware_fidelity and not x.classical_recovery_executed and not x.quantum_recovery_executed
    return False

class TestAL184(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%32,i//32))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL184,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
