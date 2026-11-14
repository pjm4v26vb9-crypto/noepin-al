"""Actual completed NOEPIN AL production use evidence for Technology 174."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,174): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_173.py'); g=load('gate173_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_172.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,173): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al173',a.al173); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('source_components_mutated','manifest_persisted','reconstruction_executed','decompression_executed','residual_applied','transfer_executed','plan_committed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')]
 p173=(r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_RESTORATION_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='INTEGRITY_VERIFIED_CANDIDATE' and r.request_id=='CRIM-173-A' and r.manifest_hash_valid and r.target_match and r.version_match and r.metadata_match and r.component_set_match and r.component_hashes_match and r.required_components_available and r.checked_component_count==5 and r.matched_component_count==5 and r.next_gate_candidate and not any(neg))
 used=dict(base['al_artifacts_used']); used['173']={'al_number':'173','source_sha256':file_sha(a.al173),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Manifest / component hash / target/version integrity match != Truth/Permission/Safety Proof/Authoritative State/Restoration Execution/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,173)}; checks['173_pass']=p173
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':174,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-173','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_172_sha256':file_sha(bo),'authority_note':'Completed AL evaluators are control/audit/reference evidence only. Integrity manifests, intent contracts, DCSR state, confidence, or ALLOW candidates do not become Truth, Permission, Consent Execution, Safety Proof, Authoritative State, external write, action execution, or Action Success.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
