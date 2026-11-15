"""Actual completed NOEPIN AL production use evidence for Technology 178."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,178): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_177.py'); g=load('gate177_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_176.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,177): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al177',a.al177); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('receipt_status_promoted_to_world_truth','receipt_status_promoted_to_action_success','result_digest_promoted_to_truth','postcondition_promoted_to_truth','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed_by_artifact','action_success_promoted','rollback_executed','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted_to_success','dcsr_generated_success_receipt','dcsr_changed_receipt_status','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')]
 p177=(r.binding_decision.value=='MATCH' and r.next_action.value=='CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='EXECUTION_RECEIPT_BOUND_CANDIDATE' and r.verification_id=='ER-177-A' and r.receipt_fingerprint_valid and r.request_match and r.permit_match and r.action_match and r.target_match and r.time_order_valid and r.status_rules_valid and r.receipt_status.value=='SUCCEEDED' and r.change_count==2 and r.postcondition_count==2 and not r.rollback_reference_present and r.next_gate_candidate and r.receipt_fingerprint=='eb36e4567b765b98626ba49051747c73f4880591f7ed58d90adc861b5717b552' and not any(neg))
 used=dict(base['al_artifacts_used']); used['177']={'al_number':'177','source_sha256':file_sha(a.al177),'decision':r.binding_decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed_by_artifact,'action_success':r.action_success_promoted,'authority_boundary':'Execution Receipt validity/binding != Permission/Tool Invocation/Action Execution/independent Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,177)}; checks['177_pass']=p177
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':178,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-177','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_176_sha256':file_sha(bo),'authority_note':'Completed AL evaluators and safety artifacts are control/audit/reference evidence only. Execution Receipt/Risk/Evidence/Decision/Intent/DCSR candidates do not become Truth, Permission, Approval Execution, external write, action execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
