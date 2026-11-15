"""Actual completed NOEPIN AL production use evidence for Technology 181."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,181): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_180.py'); g=load('gate180_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_179.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,180): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al180',a.al180); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('evidence_promoted_to_truth','accepted_response_promoted_to_truth','allowed_source_promoted_to_trust','allowed_source_promoted_to_authority','evidence_id_promoted_to_provenance_validity','closed_request_promoted_to_parent_decision_allow','closed_request_promoted_to_hold_release','dcsr_invented_evidence','dcsr_widened_allowed_sources','dcsr_closed_unresolved_claim','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')]
 p180=(file_sha(a.al180)=='2fd64c3e20092143da91c9966b13d8aa0d2fddf9ff4831cbf813afa10d13d9ef' and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_PARENT_REVALIDATION_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='EVIDENCE_DEFICIENCY_CLOSED_CANDIDATE' and r.verification_id=='EDR-180-A' and r.request_fingerprint_valid and r.response_accepted and r.closed and r.pending_count==0 and r.accepted_count==3 and r.resulting_request_fingerprint=='8bdbcf4924827502215578cd86ec2d2ad045575a677bf68d40e2119d3abadf0b' and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['180']={'al_number':'180','source_sha256':file_sha(a.al180),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Evidence deficiency request close != Truth/Parent Decision ALLOW/HOLD release/Permission/Approval/Permit/Tool/Action Execution/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,180)}; checks['180_pass']=p180
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':181,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-180','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_179_sha256':file_sha(bo),'authority_note':'Completed AL evaluators/protocols are control/audit/reference evidence only. Human Approval challenge/response candidates do not become Truth, Permission, Permit issuance, Tool invocation, Action Execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
