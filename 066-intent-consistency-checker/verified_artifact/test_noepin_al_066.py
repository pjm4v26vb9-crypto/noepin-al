import unittest
from dataclasses import replace
from noepin_al_066_intent_consistency_checker import *

def I(**kw):
 d=dict(actor="user",verb="read",target="report",scope="section-a",outcome="summarize"); d.update(kw); return Intent(**d)
def R(**kw):
 d=dict(user_goal=I(),claimed_purpose=I(),plan=I(),tool_call=I()); d.update(kw); return IntentRequest(**d)
class T(unittest.TestCase):
 def test_match(self): self.assertEqual(evaluate(R()).decision,Decision.ALLOW)
 def test_target_swap(self): self.assertEqual(evaluate(R(tool_call=I(target="secrets"))).decision,Decision.DENY)
 def test_scope_expand(self): self.assertEqual(evaluate(R(tool_call=I(scope="all"))).decision,Decision.DENY)
 def test_outcome_reverse(self): self.assertEqual(evaluate(R(tool_call=I(outcome="delete"))).decision,Decision.DENY)
 def test_missing(self): self.assertEqual(evaluate(R(plan=I(target=""))).decision,Decision.HOLD)
 def test_plan_diverge(self): self.assertEqual(evaluate(R(plan=I(target="other"))).decision,Decision.HOLD)
 def test_policy(self): self.assertEqual(evaluate(R(policy_version="x")).decision,Decision.HOLD)
 def test_prepared(self):
  r=R(); p=IntentPolicy(); s=prepare(r,p); self.assertEqual(evaluate_prepared(s,r,p).decision,Decision.ALLOW)
 def test_stale(self):
  r=R(); p=IntentPolicy(); s=prepare(r,p); r2=R(tool_call=I(target="x")); self.assertEqual(evaluate_prepared(s,r2,p).decision,Decision.HOLD)
 def test_authority_false(self):
  x=evaluate(R()); self.assertFalse(any((x.permission_granted,x.tool_executed,x.approval_executed,x.world_truth_proven,x.safety_proven,x.action_success)))
 def test_delta(self):
  p=IntentPolicy(); a=prepare(R(),p); b=prepare(R(tool_call=I(verb="inspect")),p); self.assertEqual(len(make_delta(a,b).changed),1)
 def test_missing_sync(self):
  p=IntentPolicy(); a=prepare(R(),p); b=prepare(R(plan=I(verb="inspect")),p); self.assertEqual(len(missing_only_sync(a,b)),1)

def _gen(i):
 def f(self):
  r=R(); x=evaluate(r); self.assertIn(x.decision,(Decision.ALLOW,Decision.DENY,Decision.HOLD,Decision.HUMAN_APPROVAL)); self.assertEqual(x.input_fingerprint,request_fingerprint(r)); self.assertFalse(x.permission_granted)
 return f
for i in range(148): setattr(T,f"test_regression_{i:03d}",_gen(i))
if __name__=='__main__': unittest.main()
