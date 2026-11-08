"""Actual completed NOEPIN AL production use evidence for Technology 078."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for n in range(37,78): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate77_path=Path(__file__).with_name('al_production_gate_077.py'); gate77=load('gate77_baseline',gate77_path)
    base_out=a.out.with_name('GATE_BASELINE_037_076.json'); old=sys.argv
    try:
        argv=[str(gate77_path)]
        for n in range(37,77): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate77.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al077',a.al077)
    z=m.evaluate(m.default_request(),m.default_policy(),m.default_scopes(),m.default_capabilities())
    negatives=(z.permission_granted,z.signed_delegation_token_issued,z.capability_activated,z.child_agent_created,z.sender_authority_inherited,z.sender_intent_inherited,z.sender_consent_inherited,z.tool_executed,z.transaction_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass77=(z.decision.value=='ALLOW' and z.delegation_permit_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['077']={'al_number':'077','source_sha256':file_sha(a.al077),'decision':z.decision.value,'next_gate_candidate':z.delegation_permit_candidate,'permission_granted':z.permission_granted,'action_executed':z.tool_executed,'action_success':z.action_success,'authority_boundary':'Handoff scope attenuation is control evidence only; no Permission Grant, Signed Delegation Token, Capability Activation, Child-Agent Creation, Sender Authority/Intent/Consent Inheritance, Tool Execution, Transaction Commit, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,77)}; checks['077_pass']=pass77
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':78,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-077','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_076_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No world truth, permission grant, approval execution, delegation execution, external write, transaction commit, tool execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
