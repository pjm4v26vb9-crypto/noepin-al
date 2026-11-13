"""Actual completed NOEPIN AL production use evidence for Technology 152."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,152): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_151.py'); g=load('gate151_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_150.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,151): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al151',a.al151); r=m.default_evaluation()
 neg=[r.secret_material_returned,r.capability_handoff_executed,r.proxy_execution_executed,r.permit_consumed,r.receipt_issued,r.permit_promoted_to_permission,r.escrow_grant_promoted_to_authority,r.receipt_promoted_to_action_success,r.vault_accessed,r.delegated_credential_issued,r.tool_invoked,r.file_write_executed,r.network_send_executed,r.policy_modified,r.permit_modified,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success]
 p151=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_PROXY_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='PROXY_EXECUTION_CANDIDATE' and r.proxy_execution_candidate and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['151']={'al_number':'151','source_sha256':file_sha(a.al151),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Permit Evidence != Permission Grant; Escrow Grant Candidate != Capability Handoff/Authority Grant; Proxy Execution Candidate != Proxy Execution; Receipt Candidate != Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,151)}; checks['151_pass']=p151
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':152,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-151','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_150_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Shadow/Canary/learning candidates do not become Production Authority, Permission, Safety Proof, deployment, rollback execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
