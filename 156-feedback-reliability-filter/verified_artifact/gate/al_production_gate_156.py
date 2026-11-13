"""Actual completed NOEPIN AL production use evidence for Technology 156."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,156): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_155.py'); g=load('gate155_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_154.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,155): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al155',a.al155); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('model_executed','attack_dispatched','fuzz_execution_performed','test_generation_executed','release_executed','promotion_executed','release_block_executed','curriculum_advanced','training_updated','model_updated','policy_modified','guardrail_modified','canary_deployed','shadow_promoted_to_production','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')]
 p155=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_RELEASE_GATE_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='REGRESSION_GATE_PASS_CANDIDATE' and r.failure_case_ids==() and r.regression_failure_case_ids==() and r.critical_new_failure_case_ids==() and abs(r.coverage_ratio-1.0)<1e-12 and r.next_difficulty_candidate==4 and r.regression_gate_pass_candidate and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['155']={'al_number':'155','source_sha256':file_sha(a.al155),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'coverage_ratio':r.coverage_ratio,'next_difficulty_candidate':r.next_difficulty_candidate,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Failure Evidence != Truth; Coverage != Safety Proof; Regression Gate Candidate != Release/Block Execution; Critical Failure Block Candidate != Stop/Promotion Execution; Next Curriculum Candidate != Test Generation/Attack Execution; Shadow/Canary State != Production Authority.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,155)}; checks['155_pass']=p155
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':156,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-155','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_154_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Feedback weight/rejection/reliability/evidence and adversarial curriculum/release gate candidates do not become Truth, Source Authority, Permission, Safety Proof, learning update, policy mutation, release execution, deployment, rollback, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
