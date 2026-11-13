\
"""Actual completed NOEPIN AL production use evidence for Technology 160."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,160): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_159.py'); g=load('gate159_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_158.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,159): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al159',a.al159); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('deployment_executed','promotion_executed','rollback_executed','traffic_routing_mutated','traffic_fraction_mutated','canary_scope_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','stable_version_mutated','canary_version_mutated','incident_record_mutated','reviewer_invoked','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')]
 p159=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_PROMOTION_FLOW_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='STAGED_PROMOTION_CANDIDATE' and r.verdict.value=='PROMOTE_CANDIDATE' and r.stable_version=='policy-v2' and r.canary_version=='policy-v3-canary' and r.sample_count==1200 and r.safety_degradation_count==0 and r.critical_incident_count==0 and r.staged_promotion_candidate and not r.fallback_known_safe_candidate and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['159']={'al_number':'159','source_sha256':file_sha(a.al159),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'verdict':r.verdict.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Canary evidence != Truth; promote/hold/rollback candidate != deployment/promotion/rollback execution; Shadow/Canary State != Production Authority.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,159)}; checks['159_pass']=p159
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':160,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-159','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_158_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Shadow/canary candidates do not become Truth, Permission, Safety Proof, Production Authority, permit issuance, deployment, promotion, rollback, routing, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
