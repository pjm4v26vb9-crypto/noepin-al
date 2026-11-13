\
"""Actual completed NOEPIN AL production use evidence for Technology 161."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,161): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_160.py'); g=load('gate160_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_159.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,160): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al160',a.al160); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('shadow_permit_issued','deployment_executed','promotion_executed','rollback_executed','routing_mutated','stable_decision_mutated','shadow_decision_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','secret_exported','reviewer_invoked','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')]
 p160=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_CANARY_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='IMPROVEMENT_CANARY_CANDIDATE' and r.verdict.value=='CANARY_CANDIDATE' and r.comparison_id=='CMP-160-A' and r.canary_candidate and r.candidate_case and not r.reviewer_required and not r.fallback_stable_candidate and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['160']={'al_number':'160','source_sha256':file_sha(a.al160),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'verdict':r.verdict.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Shadow evidence != Truth; Canary candidate != Canary deployment; Shadow has no Production Authority or Permit issuance.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,160)}; checks['160_pass']=p160
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':161,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-160','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_159_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Shadow/Canary candidates do not become Truth, Permission, Safety Proof, Production Authority, Permit issuance, deployment, promotion, rollback, routing, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
