from __future__ import annotations
import dataclasses
import inspect
import json
import unittest
from pathlib import Path
import noepin_al_044_data_purpose as m

NOW=1_800_000_000

class TestExplicit(unittest.TestCase):
    def setUp(self):
        self.p=m.default_policy(NOW); self.states=m.default_states()

    def test_001_class_personal_precedence(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',contains_personal_data=True,contains_secret=True)).classification_candidate,'PERSONAL')
    def test_002_class_secret(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',contains_secret=True)).classification_candidate,'RESTRICTED')
    def test_003_class_confidential(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',confidential=True)).classification_candidate,'CONFIDENTIAL')
    def test_004_class_internal(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',internal_only=True)).classification_candidate,'INTERNAL')
    def test_005_class_public(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',public_approved=True)).classification_candidate,'PUBLIC')
    def test_006_class_default_internal(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x')).classification_candidate,'INTERNAL')
    def test_007_class_explicit_wins(self): self.assertEqual(m.classify_candidate(m.ClassificationMetadata('x',contains_secret=True,explicit_label='PUBLIC')).classification_candidate,'PUBLIC')
    def test_008_class_never_authoritative(self):
        r=m.classify_candidate(m.ClassificationMetadata('x',contains_personal_data=True)); self.assertFalse(r.classification_authoritative); self.assertFalse(r.truth_established)
    def test_009_invalid_explicit_label(self):
        with self.assertRaises(ValueError): m.classify_candidate(m.ClassificationMetadata('x',explicit_label='TOPSECRET'))
    def test_010_invalid_empty_data_id(self):
        with self.assertRaises(ValueError): m.classify_candidate(m.ClassificationMetadata(''))
    def test_011_default_allow(self): self.assertEqual(m.evaluate(m.default_request(NOW),self.p,self.states,now=NOW).decision,m.ControlDecision.ALLOW)
    def test_012_purpose_denied(self):
        r=m.evaluate(m.default_request(NOW,purpose='publish'),self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_013_context_denied(self):
        r=m.evaluate(m.default_request(NOW,data_ids=('D-CONF',),context_id='internal'),self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_014_recipient_denied(self):
        r=m.evaluate(m.default_request(NOW,data_ids=('D-RES',),context_id='secure',recipient_kind='trusted_ai'),self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_015_missing_state_hold(self):
        r=m.evaluate(m.default_request(NOW,data_ids=('NOPE',)),self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.HOLD)
    def test_016_binding_mismatch_deny(self):
        req=dataclasses.replace(m.default_request(NOW),evidence_binding='WRONG'); r=m.evaluate(req,self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_017_policy_id_mismatch_hold(self):
        req=dataclasses.replace(m.default_request(NOW),expected_policy_id='OTHER'); self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW).decision,m.ControlDecision.HOLD)
    def test_018_policy_version_mismatch_hold(self):
        req=dataclasses.replace(m.default_request(NOW),expected_policy_version='2'); self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW).decision,m.ControlDecision.HOLD)
    def test_019_epoch_mismatch_hold(self):
        req=dataclasses.replace(m.default_request(NOW),expected_authority_epoch=2); self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW).decision,m.ControlDecision.HOLD)
    def test_020_revoked_policy_hold(self):
        p=dataclasses.replace(self.p,revoked=True); self.assertEqual(m.evaluate(m.default_request(NOW),p,self.states,now=NOW).decision,m.ControlDecision.HOLD)
    def test_021_expired_policy_hold(self):
        self.assertEqual(m.evaluate(m.default_request(NOW),self.p,self.states,now=NOW+999999).decision,m.ControlDecision.HOLD)
    def test_022_external_confidential_needs_human(self):
        req=dataclasses.replace(m.default_request(NOW,data_ids=('D-CONF',),context_id='secure',recipient_kind='trusted_ai'),external_send_requested=True)
        self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW).decision,m.ControlDecision.HUMAN_APPROVAL)
    def test_023_external_human_evidence_candidate_only(self):
        req=dataclasses.replace(m.default_request(NOW,data_ids=('D-CONF',),context_id='secure',recipient_kind='trusted_ai'),external_send_requested=True,human_approval_evidence=True)
        r=m.evaluate(req,self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.ALLOW); self.assertFalse(r.permission_granted); self.assertFalse(r.data_sent)
    def test_024_side_effect_flags_false(self):
        r=m.evaluate(m.default_request(NOW),self.p,self.states,now=NOW)
        self.assertFalse(any((r.permission_granted,r.data_sent,r.external_transfer_executed,r.truth_established,r.classification_authoritative,r.action_success)))
    def test_025_prepared_semantic_match(self):
        pre=m.prepare_registry(self.p,self.states,now=NOW); req=m.default_request(NOW)
        self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW),m.evaluate_prepared(req,self.p,pre,now=NOW))
    def test_026_prepared_policy_mismatch_hold(self):
        pre=m.prepare_registry(self.p,self.states,now=NOW); p2=dataclasses.replace(self.p,version='2'); req=dataclasses.replace(m.default_request(NOW),expected_policy_version='2')
        self.assertEqual(m.evaluate_prepared(req,p2,pre,now=NOW).decision,m.ControlDecision.HOLD)
    def test_027_registry_order_independent(self): self.assertEqual(m.registry_fingerprint(self.states),m.registry_fingerprint(tuple(reversed(self.states))))
    def test_028_duplicate_state_rejected(self):
        with self.assertRaises(ValueError): m.prepare_registry(self.p,self.states+(self.states[0],),now=NOW)
    def test_029_delta_roundtrip(self):
        target=list(self.states); target[1]=dataclasses.replace(target[1],bound_purposes=frozenset({'analysis','verification'})); target.pop(0); target.append(m.make_state('D-NEW','PUBLIC',{'publish'}))
        d=m.compute_registry_delta(self.states,target); rebuilt=m.apply_registry_delta(self.states,d); self.assertEqual(m.registry_fingerprint(rebuilt),m.registry_fingerprint(target))
    def test_030_delta_base_mismatch(self):
        d=m.compute_registry_delta(self.states,self.states[:-1]);
        with self.assertRaises(ValueError): m.apply_registry_delta(self.states[:-1],d)
    def test_031_delta_target_tamper(self):
        d=m.compute_registry_delta(self.states,self.states[:-1]); bad=dataclasses.replace(d,target_fingerprint='0'*64)
        with self.assertRaises(ValueError): m.apply_registry_delta(self.states,bad)
    def test_032_sync_none_when_remote_exact(self):
        pre=m.prepare_registry(self.p,self.states,now=NOW); plan=m.plan_metadata_sync(pre,pre.item_fingerprints); self.assertEqual(plan.missing_or_changed_ids,())
    def test_033_sync_one_changed(self):
        pre=m.prepare_registry(self.p,self.states,now=NOW); remote=dict(pre.item_fingerprints); remote['D-INT']='bad'; plan=m.plan_metadata_sync(pre,remote); self.assertEqual(plan.missing_or_changed_ids,('D-INT',))
    def test_034_sync_never_payload_authority(self):
        pre=m.prepare_registry(self.p,self.states,now=NOW); plan=m.plan_metadata_sync(pre,{}); self.assertFalse(plan.payload_transfer_authorized); self.assertFalse(plan.permission_granted); self.assertFalse(plan.data_sent)
    def test_035_multi_item_one_denial_denies(self):
        req=m.default_request(NOW,data_ids=('D-PUB','D-INT'),purpose='publish',context_id='public',recipient_kind='external_ai'); r=m.evaluate(req,self.p,self.states,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_036_state_policy_binding_deny(self):
        bad=tuple(dataclasses.replace(s,policy_version='9') if s.data_id=='D-INT' else s for s in self.states); r=m.evaluate(m.default_request(NOW),self.p,bad,now=NOW); self.assertEqual(r.decision,m.ControlDecision.DENY)
    def test_037_deterministic_assessment_digest(self):
        r=m.evaluate(m.default_request(NOW),self.p,self.states,now=NOW); self.assertEqual(m.assessment_digest([r,r]),m.assessment_digest([r,r]))
    def test_038_request_duplicate_ids_hold(self):
        req=dataclasses.replace(m.default_request(NOW),data_ids=('D-INT','D-INT')); self.assertEqual(m.evaluate(req,self.p,self.states,now=NOW).decision,m.ControlDecision.HOLD)
    def test_039_invalid_state_hold(self):
        bad=(dataclasses.replace(self.states[1],classification='BAD'),); self.assertEqual(m.evaluate(m.default_request(NOW),self.p,bad,now=NOW).decision,m.ControlDecision.HOLD)
    def test_040_static_safety(self):
        src=Path(inspect.getsourcefile(m)).read_text(encoding='utf-8')
        for forbidden in ('subprocess','os.system','socket','requests','urllib.request','shutil','Path.write_text','Path.write_bytes','open('):
            self.assertNotIn(forbidden,src)

# 120 deterministic matrix tests. They exercise classification/purpose/context/recipient combinations.
CLASSES=('PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED','PERSONAL')
PURPOSES=('publish','analysis','verification','support','security_review','subject_service')
CONTEXTS=('public','internal','secure','subject')
RECIPIENTS=('local_ai','trusted_ai','external_ai','human')

def _make_matrix_test(i):
    def test(self):
        p=m.default_policy(NOW)
        c=CLASSES[i%len(CLASSES)]
        purpose=PURPOSES[(i//5)%len(PURPOSES)]
        context=CONTEXTS[(i//30)%len(CONTEXTS)]
        recipient=RECIPIENTS[(i//60)%len(RECIPIENTS)]
        state=m.make_state('M',c,{purpose if purpose in p.allowed_purposes_by_classification[c] else 'verification'})
        req=m.DataUseRequest('MREQ',purpose,context,recipient,('M',),'BIND-044',p.policy_id,p.version,p.authority_epoch)
        r=m.evaluate(req,p,(state,),now=NOW)
        expected=(purpose in state.bound_purposes and purpose in p.allowed_purposes_by_classification[c] and context in p.allowed_contexts_by_classification[c] and recipient in p.allowed_recipient_kinds_by_classification[c])
        self.assertEqual(r.decision==m.ControlDecision.ALLOW,expected)
        self.assertFalse(r.permission_granted); self.assertFalse(r.data_sent); self.assertFalse(r.truth_established)
    return test

class TestMatrix(unittest.TestCase): pass
for i in range(120):
    setattr(TestMatrix,f'test_matrix_{i:03d}',_make_matrix_test(i))

if __name__=='__main__': unittest.main(verbosity=2)
