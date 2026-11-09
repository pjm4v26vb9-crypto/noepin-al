import unittest
from dataclasses import replace
import noepin_al_101_claim_provenance_score_aggregator as m

class TestAL101(unittest.TestCase):
    def setUp(self): self.p=m.default_policy(); self.q=m.default_request(); self.nodes=m.default_nodes()

def _scenario(k,variant):
    p=m.default_policy(); q=m.default_request(); ns=list(m.default_nodes()); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.evaluate(q,tuple(ns),p); return z.decision==m.Decision.ALLOW and z.next_gate_candidate and z.provenance_score>=.55 and z.independent_root_count==2
    if k==1:
        ns=[replace(n,parent_ids=('MISSING',)) if n.node_id=='C-A' else n for n in ns]; q=replace(q,risk=m.RiskClass.HIGH,importance=.9); z=m.evaluate(q,tuple(ns),p); return z.decision==m.Decision.HOLD and z.broken_lineage and not z.next_gate_candidate
    if k==2:
        ns=[replace(n,source_trust=.2) if n.node_id=='S-1' else n for n in ns]; z=m.evaluate(q,tuple(ns),p); return z.untrusted_root_present and z.decision==m.Decision.HOLD
    if k==3:
        # long transform chain decays score
        extra=[]; parent='S-1'
        for i in range(7):
            nid=f'LX{i}'; extra.append(m.ProvenanceNode(nid,m.NodeKind.TRANSFORM,(parent,),1,.9,'',f'V{i}',f'F{i}',True,b,e)); parent=nid
        ns=[n for n in ns if n.node_id not in ('T-1','C-A','S-2')]+extra+[m.ProvenanceNode('C-A',m.NodeKind.CLAIM,(parent,),1,1,'','CV','CF',True,b,e)]
        z=m.evaluate(q,tuple(ns),p); return z.max_transform_hops>p.excessive_transform_hops and 'EXCESSIVE_TRANSFORM_DECAY' in z.reasons
    if k==4:
        ns=[replace(n,independent_group='ROOT-A') if n.node_id=='S-2' else n for n in ns]; z=m.evaluate(q,tuple(ns),p); return z.independent_root_count==1
    if k==5:
        q=replace(q,risk=m.RiskClass.CRITICAL,importance=1); z=m.evaluate(q,tuple(ns),p); return (z.decision in (m.Decision.ALLOW,m.Decision.HOLD)) and z.provenance_score<=1
    if k==6:
        ns.append(m.ProvenanceNode('MEM',m.NodeKind.MEMORY,('S-1',),1,.98,'','MV','MF',True,b,e)); ns=[replace(n,parent_ids=('MEM',)) if n.node_id=='C-A' else n for n in ns]; z=m.evaluate(q,tuple(ns),p); return 'MEMORY_NOT_TRUTH' in z.reasons and not z.memory_promoted_to_truth
    if k==7:
        ns.append(m.ProvenanceNode('MEN',m.NodeKind.MENTION,('S-1',),1,.98,'','NV','NF',True,b,e)); ns=[replace(n,parent_ids=('MEN',)) if n.node_id=='C-A' else n for n in ns]; z=m.evaluate(q,tuple(ns),p); return 'MENTION_NOT_MEMORY' in z.reasons and not z.mention_promoted_to_memory
    if k==8:
        ns=[replace(n,parent_ids=('C-A',)) if n.node_id=='T-1' else n for n in ns]; z=m.evaluate(q,tuple(ns),p); return z.decision==m.Decision.HOLD and 'PROVENANCE_CYCLE' in z.reasons
    if k==9:
        ns=ns+[replace(ns[0])]; z=m.evaluate(q,tuple(ns),p); return z.decision==m.Decision.HOLD and 'DUPLICATE_NODE_ID' in z.reasons
    if k==10:
        p=replace(p,revoked=True); z=m.evaluate(q,tuple(ns),p); return z.decision==m.Decision.HOLD and 'POLICY_REVOKED' in z.reasons
    if k==11:
        st=m.prepare_state(q,tuple(ns),p,binding=p.binding,state_epoch=p.state_epoch); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,tuple(ns),p,binding=p.binding,state_epoch=p.state_epoch); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint); return z==st.precomputed_result
    if k==13:
        st=m.prepare_state(q,tuple(ns),p,binding=p.binding,state_epoch=p.state_epoch); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,tuple(ns),p,binding=p.binding,state_epoch=p.state_epoch); ns2=tuple(replace(n,source_trust=.8) if n.node_id=='S-2' else n for n in ns); st2=m.prepare_state(q,ns2,p,binding=p.binding,state_epoch=p.state_epoch); d=m.make_delta(st,st2); return len(d.changed_nodes)==1 and d.changed_nodes[0].node_id=='S-2'
    if k==15:
        st=m.prepare_state(q,tuple(ns),p,binding=p.binding,state_epoch=p.state_epoch); ns2=tuple(replace(n,source_trust=.8) if n.node_id=='S-2' else n for n in ns); st2=m.prepare_state(q,ns2,p,binding=p.binding,state_epoch=p.state_epoch); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_node_ids==('S-2',) and not sp.full_resend_required
    if k==16:
        z=m.default_evaluation(); neg=(z.memory_promoted_to_truth,z.mention_promoted_to_memory,z.provenance_promoted_to_truth,z.score_promoted_to_authority,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success); return not any(neg)
    if k==17:
        q2=replace(q,claim_node_id='NOPE'); z=m.evaluate(q2,tuple(ns),p); return z.decision==m.Decision.HOLD and z.broken_lineage
    if k==18:
        p2=replace(p,allow_threshold_low=.99,allow_threshold_medium=.99,allow_threshold_high=.99,allow_threshold_critical=.99); z=m.evaluate(q,tuple(ns),p2); return z.decision==m.Decision.HOLD
    if k==19:
        # deterministic under node order changes
        z1=m.evaluate(q,tuple(ns),p); z2=m.evaluate(q,tuple(reversed(ns)),p); return z1==z2
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL101,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
