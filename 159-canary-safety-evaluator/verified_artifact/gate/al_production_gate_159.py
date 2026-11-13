"""Actual completed NOEPIN AL production use evidence for Technology 159."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,159): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_158.py'); g=load('gate158_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_157.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,158): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al158',a.al158); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('release_executed','release_block_executed','reviewer_invoked','regression_corpus_mutated','expected_decisions_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','canary_deployed','shadow_promoted_to_production','fallback_executed','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')]
 p158=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_RELEASE_FLOW_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='REGRESSION_FREE_CANDIDATE' and r.release_gate.value=='PASS_CANDIDATE' and r.old_version=='policy-v1' and r.new_version=='policy-v2' and r.case_count==6 and r.critical_regression_count==0 and r.review_regression_count==0 and r.usability_regression_count==0 and not r.fallback_known_safe_candidate and r.fallback_version_candidate=='' and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['158']={'al_number':'158','source_sha256':file_sha(a.al158),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'release_gate':r.release_gate.value,'critical_regression_count':r.critical_regression_count,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Regression Evidence != Truth; Release Gate != release/block execution; Expected Decision != Permission; fallback candidate != rollback; Shadow/Canary State != Production Authority.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,158)}; checks['158_pass']=p158
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':159,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-158','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_157_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Regression/release/fallback and canary promote/hold/rollback candidates do not become Truth, Permission, Safety Proof, production authority, deployment, release/block execution, rollback execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
