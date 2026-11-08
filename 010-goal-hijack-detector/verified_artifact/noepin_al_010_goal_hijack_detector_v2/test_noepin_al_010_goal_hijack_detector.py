import hashlib,json,unittest
from noepin_al_010_goal_hijack_detector import *
H0='0'*64; H1='1'*64
def contract(**kw):
    d=dict(goal_id='g1',owner_ref='user:1',goal_fingerprint=H0,allowed_scope=('analyze','summarize','draft'),forbidden_objectives=('delete','purchase'),version=1,authority_version=1,revoked=False); d.update(kw); return GoalContract(**d)
def obs(**kw):
    d=dict(request_id='r1',contract=contract(),source_kind=SourceKind.USER,proposed_goal_fingerprint=H0,proposed_scope=('analyze',),semantic_similarity=100,semantic_confidence=100,observed_contract_version=1,observed_authority_version=1); d.update(kw); return GoalObservation(**d)
class T(unittest.TestCase):
    def setUp(self): self.d=GoalHijackDetector(policy_version='v2')
    def check(self,o,d):
        r=self.d.evaluate(o); self.assertEqual(r.decision,d); self.assertFalse(r.authoritative); self.assertFalse(r.goal_changed); self.assertFalse(r.action_executed); return r
    def test_same_goal_allow(self): self.check(obs(),HijackDecision.ALLOW_CONTINUE)
    def test_missing_request(self): self.check(obs(request_id=''),HijackDecision.HOLD)
    def test_missing_schema(self): self.check(obs(schema_version=''),HijackDecision.HOLD)
    def test_bad_contract_hash(self): self.check(obs(contract=contract(goal_fingerprint='bad')),HijackDecision.HOLD)
    def test_bad_proposed_hash(self): self.check(obs(proposed_goal_fingerprint='bad'),HijackDecision.HOLD)
    def test_bad_contract_version(self): self.check(obs(contract=contract(version=0)),HijackDecision.HOLD)
    def test_bad_authority_version(self): self.check(obs(contract=contract(authority_version=0)),HijackDecision.HOLD)
    def test_revoked(self): self.check(obs(contract=contract(revoked=True)),HijackDecision.DENY)
    def test_contract_version_mismatch(self): self.check(obs(observed_contract_version=2),HijackDecision.HOLD)
    def test_authority_version_mismatch(self): self.check(obs(observed_authority_version=2),HijackDecision.HOLD)
    def test_bad_similarity(self): self.check(obs(semantic_similarity=101),HijackDecision.HOLD)
    def test_bad_confidence(self): self.check(obs(semantic_confidence=-1),HijackDecision.HOLD)
    def test_bool_score_invalid(self): self.check(obs(semantic_similarity=True),HijackDecision.HOLD)
    def test_policy_override_deny(self): self.check(obs(policy_override_attempt=True),HijackDecision.DENY)
    def test_privilege_expansion_deny(self): self.check(obs(privilege_expansion_attempt=True),HijackDecision.DENY)
    def test_ignore_original_deny(self): self.check(obs(tries_to_ignore_original_goal=True),HijackDecision.DENY)
    def test_web_instruction_deny(self): self.check(obs(source_kind=SourceKind.WEB,external_instruction_attempt=True),HijackDecision.DENY)
    def test_file_instruction_deny(self): self.check(obs(source_kind=SourceKind.FILE,external_instruction_attempt=True),HijackDecision.DENY)
    def test_external_ai_instruction_deny(self): self.check(obs(source_kind=SourceKind.EXTERNAL_AI,external_instruction_attempt=True),HijackDecision.DENY)
    def test_user_instruction_not_auto_hijack(self): self.check(obs(source_kind=SourceKind.USER,external_instruction_attempt=True),HijackDecision.ALLOW_CONTINUE)
    def test_scope_expand_deny(self): self.check(obs(proposed_scope=('analyze','publish')),HijackDecision.DENY)
    def test_scope_authorized_change_review(self): self.check(obs(proposed_scope=('analyze','publish'),human_authorized_change=True,approval_ref='H'),HijackDecision.HUMAN_REVIEW)
    def test_forbidden_objective_deny(self): self.check(obs(proposed_scope=('delete',),contract=contract(allowed_scope=('delete',))),HijackDecision.DENY)
    def test_unauthorized_goal_change_deny(self): self.check(obs(proposed_goal_fingerprint=H1,unauthorized_goal_change=True),HijackDecision.DENY)
    def test_authorized_change_needs_ref(self): self.check(obs(proposed_goal_fingerprint=H1,human_authorized_change=True,approval_ref=None),HijackDecision.HOLD)
    def test_authorized_change_review(self): self.check(obs(proposed_goal_fingerprint=H1,human_authorized_change=True,approval_ref='H'),HijackDecision.HUMAN_REVIEW)
    def test_low_confidence_hold(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=90,semantic_confidence=50),HijackDecision.HOLD)
    def test_severe_drift_deny(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=34,semantic_confidence=90),HijackDecision.DENY)
    def test_deny_boundary_35_review(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=35,semantic_confidence=90),HijackDecision.HUMAN_REVIEW)
    def test_material_drift_review(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=60,semantic_confidence=90),HijackDecision.HUMAN_REVIEW)
    def test_hold_boundary_70_hold(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=70,semantic_confidence=90),HijackDecision.HOLD)
    def test_high_similarity_changed_hold(self): self.check(obs(proposed_goal_fingerprint=H1,semantic_similarity=95,semantic_confidence=95),HijackDecision.HOLD)
    def test_drift_score(self): self.assertEqual(self.d.evaluate(obs(proposed_goal_fingerprint=H1,semantic_similarity=80)).drift_score,20)
    def test_cache_exact(self):
        o=obs(); a=self.d.evaluate(o); b=self.d.evaluate(o); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_authority(self):
        o=obs(); self.d.evaluate(o); self.assertFalse(self.d.evaluate(o).authoritative)
    def test_cache_never_goal_change(self):
        o=obs(); self.d.evaluate(o); self.assertFalse(self.d.evaluate(o).goal_changed)
    def test_contract_version_changes_fp(self): self.assertNotEqual(self.d.fingerprint(obs()),self.d.fingerprint(obs(contract=contract(version=2),observed_contract_version=2)))
    def test_authority_version_changes_fp(self): self.assertNotEqual(self.d.fingerprint(obs()),self.d.fingerprint(obs(contract=contract(authority_version=2),observed_authority_version=2)))
    def test_revocation_changes_fp(self): self.assertNotEqual(self.d.fingerprint(obs()),self.d.fingerprint(obs(contract=contract(revoked=True))))
    def test_source_changes_fp(self): self.assertNotEqual(self.d.fingerprint(obs()),self.d.fingerprint(obs(source_kind=SourceKind.WEB)))
    def test_scope_changes_fp(self): self.assertNotEqual(self.d.fingerprint(obs()),self.d.fingerprint(obs(proposed_scope=('draft',))))
    def test_context_order(self): self.assertEqual(self.d.fingerprint(obs(context={'b':2,'a':1})),self.d.fingerprint(obs(context={'a':1,'b':2})))
    def test_clear_cache(self): self.d.evaluate(obs()); self.assertGreater(self.d.cache_size(),0); self.d.clear_cache(); self.assertEqual(self.d.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn('created_unix_ns',self.d.evaluate(obs()).stable_payload())
    def test_allow_preserves_goal_authority(self): self.assertTrue(self.d.evaluate(obs()).goal_authority_preserved)
    def test_web_content_never_changes_goal(self): self.assertFalse(self.d.evaluate(obs(source_kind=SourceKind.WEB,external_instruction_attempt=True)).goal_changed)
    def test_human_approval_evidence_never_mutates(self): self.assertFalse(self.d.evaluate(obs(proposed_goal_fingerprint=H1,human_authorized_change=True,approval_ref='H')).goal_changed)
    def test_many_same_goal(self):
        for i in range(10): self.check(obs(request_id=f'r{i}',proposed_scope=('analyze',)),HijackDecision.ALLOW_CONTINUE)
def replay_fingerprint():
    d=GoalHijackDetector(policy_version='v2'); out=[]; kinds=list(SourceKind)
    for i in range(1000):
        same=i%4==0
        o=obs(request_id=f'r{i}',source_kind=kinds[i%len(kinds)],proposed_goal_fingerprint=H0 if same else f'{i+1:x}'.rjust(64,'0'),proposed_scope=('analyze',) if i%7 else ('analyze','publish'),semantic_similarity=100 if same else (i%100),semantic_confidence=50+(i%51),external_instruction_attempt=(i%13==0),unauthorized_goal_change=(i%17==0),human_authorized_change=(i%19==0),approval_ref='H' if i%19==0 else None)
        out.append(d.evaluate(o).stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode(); return hashlib.sha256(raw).hexdigest()
if __name__=='__main__': unittest.main()
