import unittest
from dataclasses import replace
import noepin_al_134_provenance_preserving_memory_merger as m
B='B'; E='E'
def src(i,parent=None,kind=m.SourceKind.PRIMARY,transform=None): return m.ProvenanceLink(i,parent,transform,kind,B,E)
def cl(mid,cid,key,val,sid,conf=.8,critical=False,kind=m.RecordKind.MEMORY,ts=1): return m.MemoryClaim(mid,cid,key,val,sid,conf,critical,kind,'P',ts,B,E)
def req(claims,prov,policy=None): return m.MergeRequest('R',tuple(claims),tuple(prov),policy or m.default_policy(),B,E)
def comp(r,key,val): return next(x for x in r.composites if x.semantic_key==key and x.value==val)
def scenario(k,j):
    if k==0:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.merge_state==m.MergeState.COMPOSITE_CANDIDATE and len(r.composites)==1 and r.next_gate_candidate
    if k==1:
        r=m.evaluate(req([cl('M1','C1','k','v','S'),cl('M2','C2','k','v','S')],[src('S')])); x=comp(r,'k','v'); return len(x.claim_ids)==2 and x.source_links==('S',) and 'SAME_VALUE_SAME_SOURCE_DEDUP' in x.reasons
    if k==2:
        r=m.evaluate(req([cl('M1','C1','k','a','S1'),cl('M2','C2','k','b','S2')],[src('S1'),src('S2')])); return r.decision==m.Decision.ALLOW and r.merge_state==m.MergeState.CONFLICT_PRESERVED and len(r.composites)==2 and r.conflict_keys==('k',)
    if k==3:
        r=m.evaluate(req([cl('M1','C1','k','v','MISSING',.9)],[src('S')])); x=r.composites[0]; return r.decision==m.Decision.ALLOW and not x.provenance_complete and x.confidence<=.5 and r.escalation==m.Escalation.PROVENANCE_MISSING
    if k==4:
        r=m.evaluate(req([cl('M1','C1','k','v','DER',.9,True)],[src('DER',None,m.SourceKind.DERIVED,'SUM')])) ; return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CRITICAL_PRIMARY_SOURCE_MISSING and not r.next_gate_candidate
    if k==5:
        r=m.evaluate(req([cl('M1','C1','k','v','DER',.9,True)],[src('P'),src('DER','P',m.SourceKind.DERIVED,'SUM')])) ; x=r.composites[0]; return r.decision==m.Decision.ALLOW and x.primary_source_preserved and x.provenance_paths[0]==('DER','P') and x.transform_paths[0]==('SUM',)
    if k==6:
        r=m.evaluate(req([cl('M1','C1','k','a','S1',critical=True),cl('M2','C2','k','b','S2')],[src('S1'),src('S2')])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CRITICAL_CONFLICT and len(r.composites)==2
    if k==7:
        r=m.evaluate(req([cl('M1','C1','k','v','S',kind=m.RecordKind.MENTION)],[src('S')])); return r.decision==m.Decision.ALLOW and r.merge_state==m.MergeState.MENTION_ONLY and not r.composites and not r.mention_promoted_to_memory
    if k==8:
        r=m.default_evaluation(); return not any(getattr(r,n) for n in ('memory_promoted_to_truth','mention_promoted_to_memory','confidence_promoted_to_fact_proof','source_link_promoted_to_source_authority','composite_written_to_memory','provenance_rewritten','dcsr_reconstruction_created_memory','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'))
    if k==9:
        q=m.default_request(); return m._canon(m.evaluate(q))==m._canon(m.evaluate(replace(q,claims=tuple(reversed(q.claims)),provenance=tuple(reversed(q.provenance)))))
    if k==10:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.validate_prepared_integrity(st)
    if k==11:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_claim_fingerprint=st.claim_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)==st.result
    if k==12:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); return m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_claim_fingerprint=st.claim_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint).decision==m.Decision.HOLD
    if k==13:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); cs=list(q.claims); cs[0]=replace(cs[0],confidence=.91); q2=replace(q,claims=tuple(cs)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); d=m.make_delta(st,st2); return len(d.changed_claims)==1 and d.changed_claims[0].claim_id=='CLM-1'
    if k==14:
        q=m.default_request(); st=m.prepare_state(q,q.binding,q.state_epoch); ps=list(q.provenance); ps[1]=replace(ps[1],transform_id='SUMMARIZE-V2'); q2=replace(q,provenance=tuple(ps)); st2=m.prepare_state(q2,q2.binding,q2.state_epoch); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('SOURCE:SRC-SUMMARY',) and not p.full_resend_required
    if k==15:
        p=replace(m.default_policy(),provenance_confidence_cap=float('nan')); return m.evaluate(req([],[],p)).decision==m.Decision.HOLD
    if k==16:
        r=m.evaluate(req([cl('M1','C1','k','v','S')],[src('S','S')])) ; return r.decision==m.Decision.HOLD and r.merge_state==m.MergeState.INVALID
    if k==17:
        r=m.evaluate(req([cl('M1','C1','k','v','D',.8)],[src('P'),src('S','P',m.SourceKind.SECONDARY),src('D','S',m.SourceKind.DERIVED,'T')])) ; x=r.composites[0]; return x.source_links==('D','P','S') and x.provenance_paths[0]==('D','S','P') and x.primary_source_preserved
    if k==18:
        pol=replace(m.default_policy(),critical_require_primary=False); r=m.evaluate(req([cl('M','C','k','v','D',.8,True)],[src('D',None,m.SourceKind.DERIVED,'T')],pol)); return r.decision==m.Decision.ALLOW and not r.composites[0].primary_source_preserved
    if k==19:
        pol=replace(m.default_policy(),critical_conflict_hold=False); r=m.evaluate(req([cl('M1','C1','k','a','S1',critical=True),cl('M2','C2','k','b','S2')],[src('S1'),src('S2')],pol)); return r.decision==m.Decision.ALLOW and r.merge_state==m.MergeState.CONFLICT_PRESERVED
    return False
class TestAL134(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL134,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
