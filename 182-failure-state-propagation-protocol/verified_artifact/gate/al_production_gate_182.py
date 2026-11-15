"""Actual completed NOEPIN AL production use evidence for Technology 182."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,182): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_181.py'); g=load('gate181_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_180.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,181): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al181',a.al181); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('human_approval_executed','approval_executed','permission_granted','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_nonce_reused','cached_approval_response_reused','dcsr_substituted_human_approval','dcsr_created_approval_response','dcsr_changed_action_digest','dcsr_changed_risk_digest','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')]
 p181=(file_sha(a.al181)=='ab95dadba5679904464c40a88162a892e9efd776e8fc52c32559edad9ac01440' and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_PERMIT_HANDSHAKE_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='HUMAN_APPROVAL_RESPONSE_VERIFIED_CANDIDATE' and r.verification_id=='HACR-181-A' and r.challenge_fingerprint_valid and r.nonce_match and r.action_digest_match and r.risk_digest_match and r.within_validity_window and r.human_decision.value=='APPROVE' and r.approval_response_verified and r.human_approval_evidence_verified and r.challenge_fingerprint=='ce72c3acb7356a0fa4e16ce5fad6a8e87c1959365f7b4e951ab444a46811fe73' and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['181']={'al_number':'181','source_sha256':file_sha(a.al181),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'permit_issued':r.permit_issued,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Verified Human Approval Response evidence != Permission/Permit issuance/Tool invocation/Action Execution/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,181)}; checks['181_pass']=p181
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':182,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-181','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_180_sha256':file_sha(bo),'authority_note':'Completed AL evaluators/protocols are control/audit/reference evidence only. Failure-state propagation candidates do not become Truth, Permission, Recovery execution, Tool invocation, Action Execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
