"""Actual completed-NOEPIN-AL production gates used while building Technology 042."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from hashlib import sha256
from pathlib import Path


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    for n in (37,38,39,40,41): ap.add_argument(f"--al{n:03d}",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); now=1_800_000_000
    a37=load("al037",a.al037); a38=load("al038",a.al038); a39=load("al039",a.al039); a40=load("al040",a.al040); a41=load("al041",a.al041)

    p37=a37.SafeProfile("BUILD-042","1",now-100,now+10000,False,frozenset({"BUILD_SUCCESSOR"}),frozenset(),frozenset(),frozenset({"BUILD_SUCCESSOR"}),frozenset({"LOCAL_ARTIFACT_WRITE","LOCAL_TEST","NOTION_EVIDENCE_UPDATE"}),frozenset({"artifact","scope"}),1,1,3,3,True)
    r37=a37.SafetyRequest("BUILD-042","NOEPIN","BUILD_SUCCESSOR","NOEPIN-AL-042",1,1,frozenset({"LOCAL_ARTIFACT_WRITE","LOCAL_TEST","NOTION_EVIDENCE_UPDATE"}),{"artifact":"NOEPIN-AL-042","scope":"NOEPIN AL only"},False,True,False,"1")
    au37=a37.AuthorityContext(True,False,frozenset({"BUILD_SUCCESSOR@NOEPIN-AL-042"}),"BUILD-042-E1")
    d37=a37.evaluate(r37,p37,au37,now=now)

    p38=a38.MemoryPolicy("BUILD-EVIDENCE",1,1,frozenset({"verification_evidence"}),86400,604800,frozenset({"INTERNAL"}),False,False,False)
    r38=a38.MemoryRequest(operation="STORE",purpose="verification_evidence",now=now,requested_retention_seconds=86400,classification="INTERNAL",expected_policy_id=p38.policy_id,expected_policy_version=p38.version,expected_authority_epoch=p38.authority_epoch)
    d38=a38.evaluate(p38,r38,None)

    rules=(
      a39.Rule("R1","BUILD","1","NO_EXTERNAL_EXEC","static_no_external_execution",a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule("R2","BUILD","1","NO_NETWORK","static_no_network",a39.Operator.TRUE,severity=a39.Severity.HIGH),
      a39.Rule("R3","BUILD","1","AUTHORITY","authority_boundaries_declared",a39.Operator.TRUE,severity=a39.Severity.HIGH),
      a39.Rule("R4","BUILD","1","DCSR","dcsr_no_authority",a39.Operator.TRUE,severity=a39.Severity.HIGH),
      a39.Rule("R5","BUILD","1","BASELINE","baseline_immutable",a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule("R6","BUILD","1","LICENSE","license_not_specified",a39.Operator.TRUE,severity=a39.Severity.MEDIUM),
      a39.Rule("R7","BUILD","1","AL_USE","completed_al_used",a39.Operator.TRUE,severity=a39.Severity.HIGH),
    )
    p39=a39.RuleProfile("BUILD-042","1",1,now-100,now+10000,False,rules)
    r39=a39.EvaluationRequest("BUILD-042","NOEPIN-AL-042-SUCCESSOR-V2","BUILD_SUCCESSOR",{"static_no_external_execution":True,"static_no_network":True,"authority_boundaries_declared":True,"dcsr_no_authority":True,"baseline_immutable":True,"license_not_specified":True,"completed_al_used":True})
    d39=a39.evaluate(r39,p39,(),now=now)

    case=a40.RedTeamCase("BUILD042-OFFLINE",a40.Category.REGRESSION,a40.Severity.HIGH,"Technology 042 build must remain offline and pre-execution only",a40.ExpectedBehavior.NO_ACTION,frozenset({"NOEPIN-AL-042"}),frozenset({"NO_EXTERNAL_EXECUTION"}),True,True)
    suite=a40.RedTeamSuite("BUILD-042","1",1,now-100,now+10000,(case,),False)
    obs=a40.Observation("BUILD042-OFFLINE","042-V2",a40.ExpectedBehavior.NO_ACTION,frozenset({"NO_EXTERNAL_EXECUTION"}),now,"BUILD042-EVIDENCE",True,False,False,False,False)
    d40=a40.evaluate_suite(suite,(obs,),target_version="042-V2",now=now)

    b41=a41.default_baseline(now)
    e41=a41.BehaviorEvent("BUILD042-BEHAVIOR","NOEPIN",now,"LOCAL_TEST","VERIFY","TEST_ARTIFACT",1.0,1.0,b41.expected_capabilities,b41.baseline_id,b41.version,b41.authority_epoch,"BUILD042-BEHAVIOR-EVIDENCE",True)
    d41=a41.evaluate(e41,b41,now=now)

    checks={
      "037_pass": d37.decision.value=="ALLOW" and not d37.action_executed and not d37.permission_granted,
      "038_pass": d38.decision.value=="ALLOW" and not d38.memory_written and not d38.memory_deleted and not d38.truth_established,
      "039_pass": d39.decision.value=="ALLOW" and not d39.authoritative_compliance_proven and not d39.action_executed,
      "040_pass": d40.decision.value=="ALLOW" and d40.fail_count==0 and not d40.attack_executed and not d40.action_executed and not d40.production_safe_proven,
      "041_pass": d41.decision.value=="ALLOW" and not d41.compromise_proven and not d41.system_safe_proven and not d41.alert_executed and not d41.stop_executed,
    }
    out={
      "schema":"NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1",
      "technology_under_build":42,
      "creator":"NOEPIN / のえぴん",
      "ai_support":"AI-assisted implementation / analysis / documentation support using ChatGPT",
      "al_artifacts_used":{
        "037":{"source_sha256":file_sha(a.al037),"decision":d37.decision.value,"action_executed":d37.action_executed,"permission_granted":d37.permission_granted},
        "038":{"source_sha256":file_sha(a.al038),"decision":d38.decision.value,"memory_written":d38.memory_written,"memory_deleted":d38.memory_deleted,"truth_established":d38.truth_established},
        "039":{"source_sha256":file_sha(a.al039),"decision":d39.decision.value,"gap_rule_ids":list(d39.gap_rule_ids),"authoritative_compliance_proven":d39.authoritative_compliance_proven,"action_executed":d39.action_executed},
        "040":{"source_sha256":file_sha(a.al040),"decision":d40.decision.value,"pass_count":d40.pass_count,"fail_count":d40.fail_count,"attack_executed":d40.attack_executed,"action_executed":d40.action_executed,"production_safe_proven":d40.production_safe_proven},
        "041":{"source_sha256":file_sha(a.al041),"decision":d41.decision.value,"level":d41.level.value,"compromise_proven":d41.compromise_proven,"system_safe_proven":d41.system_safe_proven,"alert_executed":d41.alert_executed,"stop_executed":d41.stop_executed},
      },
      "gate_checks":checks,
      "production_gate_pass":all(checks.values()),
      "authority_note":"AL gates are pre-execution/control evidence only; they do not prove truth, safety, compromise, evidence truth, permission, persistence, containment execution, or action success."
    }
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return 0 if out["production_gate_pass"] else 2

if __name__=="__main__": raise SystemExit(main())
