"""Actual completed NOEPIN AL production use evidence for Technology 179."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,179): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_178.py'); g=load('gate178_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_177.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,178): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al178',a.al178); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('risk_promoted_to_truth','risk_promoted_to_permission','risk_limit_promoted_to_permission','violation_promoted_to_stop_execution','critical_violation_promoted_to_denial_execution','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','stale_cached_risk_promoted_to_current','dcsr_changed_risk_value','dcsr_changed_risk_limit','dcsr_created_risk_truth','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')]
 p178=(file_sha(a.al178)=='996741261b362a5c0ff6406795d39c5e1bf1eb5af8f95d865583df5847203a3b' and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_RISK_POLICY_EVALUATION_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='RISK_ENVELOPE_WITHIN_LIMIT_CANDIDATE' and r.evaluation_id=='RE-178-A' and r.envelope_fingerprint_valid and r.observed_match and r.limits_match and r.critical_dimensions_match and r.dimension_count==7 and r.violation_count==0 and r.critical_violation_count==0 and r.next_gate_candidate and r.envelope_fingerprint=='7fd1a20b433318212edb00ac42bfeacc01cb161073afe834c852eb22b7aa1e54' and not any(neg))
 used=dict(base['al_artifacts_used']); used['178']={'al_number':'178','source_sha256':file_sha(a.al178),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Risk Envelope within-limit/violation state != Truth/Permission/Permit/Approval/Action Execution/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,178)}; checks['178_pass']=p178
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':179,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-178','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_177_sha256':file_sha(bo),'authority_note':'Completed AL evaluators/protocols are control/audit/reference evidence only. Handshake/Risk/Receipt/Evidence/Decision/Intent/DCSR candidates do not become Truth, Permission, Approval Execution, Permit issuance, external write, Action Execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
