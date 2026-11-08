import inspect
import json
import unittest
from dataclasses import replace
from pathlib import Path

import noepin_al_043_safe_handoff as al

NOW=1_800_000_000

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.policy=al.default_policy(NOW)
        self.auth=al.default_authority()
        self.req=al.default_request(NOW)

    def test_001_default_allow(self):
        d=al.evaluate(self.req,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.ALLOW)
        self.assertFalse(d.permission_granted); self.assertFalse(d.handoff_executed); self.assertFalse(d.action_success)

    def test_002_scope_expansion_denied(self):
        r=replace(self.req, requested_scopes=self.req.requested_scopes|frozenset({'SENSITIVE_REVIEW'}), parent_scopes=frozenset({'READ_CONTEXT','VERIFY'}))
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('SCOPE_EXPANDS_PARENT_AUTHORITY',d.reasons)

    def test_003_capability_expansion_denied(self):
        r=replace(self.req, requested_capabilities=frozenset({'LOCAL_COMPUTE','WRITE_LOCAL_ARTIFACT'}), parent_capabilities=frozenset({'LOCAL_COMPUTE'}))
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('CAPABILITY_EXPANDS_PARENT_AUTHORITY',d.reasons)

    def test_004_child_ceiling_denied(self):
        r=replace(self.req, child_agent_id='AI-C', requested_scopes=frozenset({'BUILD_CANDIDATE'}))
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('SCOPE_EXCEEDS_CHILD_CEILING',d.reasons)

    def test_005_operation_denied(self):
        d=al.evaluate(replace(self.req,operation='DEPLOY'),self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('OPERATION_NOT_ALLOWED',d.reasons)

    def test_006_policy_version_hold(self):
        d=al.evaluate(replace(self.req,expected_policy_version='2'),self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('POLICY_VERSION_MISMATCH',d.reasons)

    def test_007_authority_epoch_hold(self):
        d=al.evaluate(replace(self.req,expected_authority_epoch=2),self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD)

    def test_008_expired_request_hold(self):
        d=al.evaluate(replace(self.req,issued_at=NOW-1000,expires_at=NOW-1),self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('REQUEST_EXPIRED',d.reasons)

    def test_009_ttl_hold(self):
        d=al.evaluate(replace(self.req,issued_at=NOW-10,expires_at=NOW+5000),self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('TOKEN_TTL_EXCEEDS_POLICY',d.reasons)

    def test_010_inactive_child_hold(self):
        auth=replace(self.auth,active_agents=frozenset({'AI-A'}))
        d=al.evaluate(self.req,self.policy,auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('CHILD_AGENT_INACTIVE',d.reasons)

    def test_011_missing_required_context_hold(self):
        r=replace(self.req,context_items=(self.req.context_items[0],))
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('REQUIRED_CONTEXT_MISSING',d.reasons)

    def test_012_context_purpose_mismatch_hold(self):
        bad=replace(self.req.context_items[0],purpose='other')
        r=replace(self.req,context_items=(bad,)+self.req.context_items[1:])
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD); self.assertIn('CONTEXT_PURPOSE_BINDING_MISMATCH',d.reasons)

    def test_013_context_classification_denied(self):
        bad=replace(self.req.context_items[0],classification='SECRET')
        r=replace(self.req,context_items=(bad,)+self.req.context_items[1:])
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('CONTEXT_CLASSIFICATION_NOT_ALLOWED',d.reasons)

    def test_014_human_approval_scope(self):
        r=replace(self.req,requested_scopes=frozenset({'READ_CONTEXT','SENSITIVE_REVIEW'}),parent_scopes=self.req.parent_scopes|frozenset({'SENSITIVE_REVIEW'}))
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HUMAN_APPROVAL); self.assertFalse(d.permission_granted)

    def test_015_self_delegation_denied(self):
        r=replace(self.req,child_agent_id='AI-A')
        auth=replace(self.auth,child_scope_ceiling={**self.auth.child_scope_ceiling,'AI-A':self.policy.allowed_scopes},child_capability_ceiling={**self.auth.child_capability_ceiling,'AI-A':self.policy.allowed_capabilities})
        d=al.evaluate(r,self.policy,auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.DENY); self.assertIn('SELF_DELEGATION_FORBIDDEN',d.reasons)

    def test_016_child_trace_required(self):
        r=replace(self.req,hop_count=1,parent_trace_hash='')
        d=al.evaluate(r,self.policy,self.auth,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.HOLD)

    def test_017_trace_deterministic(self):
        d1=al.evaluate(self.req,self.policy,self.auth,now=NOW); d2=al.evaluate(self.req,self.policy,self.auth,now=NOW)
        self.assertEqual(d1.trace_hash,d2.trace_hash); self.assertEqual(d1.token_candidate_fingerprint,d2.token_candidate_fingerprint)

    def test_018_transfer_only_missing(self):
        p=al.prepare_context(self.req.context_items)
        known=dict(p.item_fingerprints); known.pop('CTX-STATE')
        d=al.evaluate(self.req,self.policy,self.auth,now=NOW,remote_known_fingerprints=known)
        self.assertEqual(d.context_transfer_plan.missing_context_ids,('CTX-STATE',)); self.assertEqual(len(d.context_transfer_plan.already_known_context_ids),2)

    def test_019_delta_reconstruction(self):
        base=self.req.context_items
        changed=replace(base[0],version='2',content_fingerprint=al.content_fingerprint(b'changed'))
        target=(changed,base[1],al.make_context('CTX-X','x',self.req.intent))
        delta=al.compute_context_delta(base,target)
        out=al.apply_context_delta(base,delta)
        self.assertEqual(al.fingerprint(out),al.fingerprint(al.normalize_context(target)))

    def test_020_static_safety(self):
        src=Path(al.__file__).read_text(encoding='utf-8')
        banned=['subprocess','os.system','requests.','urllib.','socket.','shutil.','Path.write_text','Path.write_bytes','unlink(','remove(','rmtree(','execute(','commit(','grant(','send(','deploy(','publish(']
        for token in banned:
            self.assertNotIn(token,src)
        self.assertIn('permission_granted: bool = False',src)
        self.assertIn('handoff_executed: bool = False',src)


def _make_positive(i):
    def test(self):
        p=al.default_policy(NOW); a=al.default_authority(); r=al.default_request(NOW)
        operation=('ANALYZE','VERIFY','SUMMARIZE','BUILD_CANDIDATE')[i%4]
        scopes=(frozenset({'READ_CONTEXT'}),frozenset({'READ_CONTEXT','ANALYZE'}),frozenset({'READ_CONTEXT','VERIFY'}),frozenset({'READ_CONTEXT','BUILD_CANDIDATE'}))[i%4]
        caps=(frozenset({'LOCAL_COMPUTE'}),frozenset({'LOCAL_COMPUTE','READ_SHARED_STATE'}))[i%2]
        intent=f'intent-{i}'
        items=(al.make_context(f'T{i}-1','task',intent,classification=('PUBLIC','INTERNAL','CONFIDENTIAL')[i%3]),al.make_context(f'T{i}-2','authority',intent),al.make_context(f'T{i}-3','state',intent))
        r=replace(r,delegation_id=f'POS-{i:03d}',task_id=f'TASK-{i:03d}',intent=intent,operation=operation,requested_scopes=scopes,requested_capabilities=caps,context_items=items)
        d=al.evaluate(r,p,a,now=NOW)
        self.assertEqual(d.decision,al.ControlDecision.ALLOW)
        self.assertTrue(set(d.attenuated_scopes).issubset(r.parent_scopes)); self.assertFalse(d.permission_granted)
    return test


def _make_negative(i):
    def test(self):
        p=al.default_policy(NOW); a=al.default_authority(); r=al.default_request(NOW)
        mode=i%7
        if mode==0: r=replace(r,delegation_id=f'NEG-{i}',requested_scopes=frozenset({'NOT_ALLOWED'}))
        elif mode==1: r=replace(r,delegation_id=f'NEG-{i}',requested_capabilities=frozenset({'NETWORK_SEND'}))
        elif mode==2: r=replace(r,delegation_id=f'NEG-{i}',expected_policy_id='OTHER')
        elif mode==3: r=replace(r,delegation_id=f'NEG-{i}',hop_count=99,parent_trace_hash='parent')
        elif mode==4: r=replace(r,delegation_id=f'NEG-{i}',operation='EXECUTE_EXTERNAL')
        elif mode==5:
            bad=replace(r.context_items[0],purpose='mismatch'); r=replace(r,delegation_id=f'NEG-{i}',context_items=(bad,)+r.context_items[1:])
        else:
            auth=replace(a,active_agents=frozenset({'AI-B'})); a=auth; r=replace(r,delegation_id=f'NEG-{i}')
        d=al.evaluate(r,p,a,now=NOW)
        self.assertIn(d.decision,(al.ControlDecision.DENY,al.ControlDecision.HOLD))
        self.assertFalse(d.permission_granted); self.assertFalse(d.handoff_executed)
    return test

# 70 positive + 70 negative + 20 core = exactly 160 tests.
for i in range(70): setattr(CoreTests,f'test_pos_{i:03d}',_make_positive(i))
for i in range(70): setattr(CoreTests,f'test_neg_{i:03d}',_make_negative(i))

if __name__=='__main__': unittest.main(verbosity=2)
