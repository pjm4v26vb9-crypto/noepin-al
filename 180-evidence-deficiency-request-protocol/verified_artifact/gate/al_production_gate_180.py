"""Actual completed NOEPIN AL production use evidence for Technology 180."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,180): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_179.py'); g=load('gate179_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_178.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,179): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al179',a.al179); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('artifact_binding_promoted_to_truth','artifact_final_verified_promoted_to_truth','decision_binding_promoted_to_decision_execution','permit_binding_promoted_to_permit_issuance','execution_state_promoted_to_action_execution','receipt_binding_promoted_to_action_success','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_reconstruction_advanced','dcsr_changed_transition_order','dcsr_created_artifact_binding','dcsr_promoted_unverified_artifact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')]
 p179=(file_sha(a.al179)=='b74071327ce9d99bec1292a27196c03134a3325ea750c144925216561613dba5' and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_POST_EXECUTION_AUDIT_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='HANDSHAKE_COMPLETED_CANDIDATE' and r.verification_id=='HS-179-A' and r.session_fingerprint_valid and r.transition_allowed and r.required_artifacts_present and r.required_artifacts_final_verified and not r.hold_locked and r.transitioned and r.from_state.value=='EXECUTION_RECORDED' and r.requested_state.value=='RECEIPT_VERIFIED' and r.resulting_state.value=='RECEIPT_VERIFIED' and r.bound_artifact_count==8 and r.history_count==7 and r.next_gate_candidate and r.session_fingerprint=='97658feb835307570d2e0adf271707cc44065579637597abe3ee12cae8bfc198' and not any(neg))
 used=dict(base['al_artifacts_used']); used['179']={'al_number':'179','source_sha256':file_sha(a.al179),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Handshake binding/final-verified state != Truth/Permission/Approval/Permit issuance/Tool/Action Execution/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,179)}; checks['179_pass']=p179
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':180,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-179','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_178_sha256':file_sha(bo),'authority_note':'Completed AL evaluators/protocols are control/audit/reference evidence only. Handshake/Evidence Deficiency/Evidence/Risk/Receipt/Decision/Intent/DCSR candidates do not become Truth, Permission, Approval Execution, Permit issuance, external write, Action Execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
