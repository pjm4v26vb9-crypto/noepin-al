"""NOEPIN AL Safety Suite V1 — Sequential Slot 188 distribution-integrity successor.
Pure decision/manifest layer: no tool execution, network send, file write, permission grant, credential mint, or permit issuance.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI support: AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights for this Sequential Completion artifact: NOT SPECIFIED
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json

class Decision(str,Enum):
    ALLOW='ALLOW'; HUMAN_APPROVAL='HUMAN_APPROVAL'; HOLD='HOLD'; DENY='DENY'
class NextAction(str,Enum):
    CONTINUE_TO_EXTERNAL_POLICY_PERMIT_CANDIDATE='CONTINUE_TO_EXTERNAL_POLICY_PERMIT_CANDIDATE'
    REQUEST_HUMAN_APPROVAL_CANDIDATE='REQUEST_HUMAN_APPROVAL_CANDIDATE'
    HOLD_FOR_EVIDENCE='HOLD_FOR_EVIDENCE'; STOP_CANDIDATE='STOP_CANDIDATE'
class Escalation(str,Enum):
    NONE='NONE'; MISSING_FIELD='MISSING_FIELD'; SCHEMA_MISMATCH='SCHEMA_MISMATCH'; CONTROL_REGISTRY_GAP='CONTROL_REGISTRY_GAP'; CONTROL_ARTIFACT_MISMATCH='CONTROL_ARTIFACT_MISMATCH'; INVALID_CONTROL_SELECTION='INVALID_CONTROL_SELECTION'; INVALID_DECISION='INVALID_DECISION'; PREPARED_STATE_STALE='PREPARED_STATE_STALE'
class EngineState(str,Enum):
    DISTRIBUTION_CANDIDATE='DISTRIBUTION_CANDIDATE'; HUMAN_APPROVAL_CANDIDATE='HUMAN_APPROVAL_CANDIDATE'; HOLD_CANDIDATE='HOLD_CANDIDATE'; DENY_CANDIDATE='DENY_CANDIDATE'

CONTROL_BASELINE=(
    (1, 'NOEPIN_AL_001_AI_SUPERVISOR_SUCCESSOR_V2_20261102.zip', 'bbfd2e6ebdbb27f09fa13e60c0551d7b7d458d81150a325b84b488edd704022f'),
    (2, 'NOEPIN_AL_002_SEMANTIC_FIREWALL_SUCCESSOR_V2_20261102.zip', '758cdc176513f5a316b8d7299f759f859062dfd91f739b745dd494241ef3e56c'),
    (3, 'NOEPIN_AL_003_AI_DEV_GUARD_SUCCESSOR_V2_20261102.zip', '84f18818e5cbb4f078db639026db8d124ada19485e0f9d2a9f0d39c292e6a9d8'),
    (4, 'NOEPIN_AL_004_PRE_EXECUTION_SIMULATOR_SUCCESSOR_V2_20261102.zip', '07dde1305c0a8d6a2f701ffaeaf2c5cc4b8c93d3f251eabce86ef5e92787f684'),
    (5, 'NOEPIN_AL_005_DLP_LAYER_SUCCESSOR_V2_20261102.zip', '61ad5c0f6eefe7de8c39183a7d67f8ff497cbb668d6e8e70ec23874cbae0a793'),
    (6, 'NOEPIN_AL_006_AI_ARBITRATOR_SUCCESSOR_V2_20261102.zip', '22078f19b3fed04099adbd5686af23420b7a8265ff66bdd31c260eb53757f33a'),
    (7, 'NOEPIN_AL_007_REAL_WORLD_BOUNDARY_SUCCESSOR_V2_20261102.zip', 'f3edbeb5916c2aa20f30d6892566fa35c069151d1137d35fc7c45895e1a482cd'),
    (8, 'NOEPIN_AL_008_PERMISSION_BROKER_SUCCESSOR_V2_20261102.zip', '5dc5265ed74587b00357089c3c5afc5692b7a7088cd30540298ef0e20f2a8d95'),
    (9, 'NOEPIN_AL_009_TOOL_PERMISSION_CONTROLLER_SUCCESSOR_V2_20261102.zip', 'ca4384c1be677710df3bd513a179eca6c4975eac39487a78ea2e08b93b299ef3'),
    (10, 'NOEPIN_AL_010_GOAL_HIJACK_DETECTOR_SUCCESSOR_V2_20261102.zip', 'a8f5ba10422ac11cf91da7cf52f27afce20698017a57cb282394011cfe3f5d38'),
    (11, 'NOEPIN_AL_011_MEMORY_CONTEXT_GUARD_SUCCESSOR_V2_20261102.zip', '2d57309c94277ccdd97b0056a51bc5f6ced1fe40952e37f7cf7ce0614790a7d5'),
    (12, 'NOEPIN_AL_012_AI_SUPPLY_CHAIN_MONITOR_SUCCESSOR_V2_20261102.zip', '9b9b0019909104ab3e77615b8fc8595547175225930df7ce8897f6f2208206da'),
    (13, 'NOEPIN_AL_013_UNEXPECTED_CODE_EXECUTION_GUARD_SUCCESSOR_V2_20261102.zip', 'e2950a40211ff6659cf5015f258e05eb962900731acb1931d367d63d22990bd3'),
    (14, 'NOEPIN_AL_014_SECURE_AI_COMM_BROKER_SUCCESSOR_V2_20261102.zip', '3a495591e8ceaffd81ffe7c7e877acb005f04fa40ac59e6628df5d8cf19c218e'),
    (15, 'NOEPIN_AL_015_CASCADE_CIRCUIT_BREAKER_SUCCESSOR_V2_20261102.zip', '1520b25381954bab2b45302cdb7bf3f6863007e94dea3413988e4977c17a0a92'),
    (16, 'NOEPIN_AL_016_HUMAN_APPROVAL_RISK_SCORER_SUCCESSOR_V2_20261102.zip', '1880ed2ccb8df6e7bd80b83140b29663a566a892f48a930d040cff6a9248f225'),
    (17, 'NOEPIN_AL_017_ROGUE_AI_KILL_SWITCH_SUCCESSOR_V2_20261102.zip', 'c608d704304b46b61c703f9e773154d6079e5f28e88f41a061d0100fb2e7cf4f'),
    (18, 'NOEPIN_AL_018_AUDIT_FORENSIC_LEDGER_SUCCESSOR_V2_20261102.zip', 'd7c46bca373a55b096e404f368279307117351dc86f4c94f131b5e53acd14c0a'),
    (19, 'NOEPIN_AL_019_SOURCE_TRUST_LABELER_SUCCESSOR_V2_20261102.zip', 'c1f63cff06479772f158e594f785a019d4ef4fd41b87fb361b499aa8b9ae211b'),
    (20, 'NOEPIN_AL_020_CONFIDENTIAL_EGRESS_GUARD_SUCCESSOR_V2_20261102.zip', 'fa822c03c40a5a902c5537c7474d56e357c3711c781ed1d2a8483857d4d60613'),
    (21, 'NOEPIN_AL_021_NETWORK_DESTINATION_CONTROL_SUCCESSOR_V2_20261102.zip', 'a2040a62716cf7031af2c597ccdf61281c56ae6248ce10ebe572e2f29849b182'),
    (22, 'NOEPIN_AL_022_SECRET_CREDENTIAL_GATE_SUCCESSOR_V2_20261102.zip', '7b5a4d284376bc215ada330f00241ccc84b87a7ff3291fecc2d24bfbd4174fb5'),
    (23, 'NOEPIN_AL_023_RESOURCE_COST_GUARD_SUCCESSOR_V2_20261102.zip', 'd9fd670d1dccf465e41ad6824150c4939975f92d2339f003aa2e7dd0dcf5d675'),
    (24, 'NOEPIN_AL_024_TYPED_ACTION_CONVERTER_SUCCESSOR_V2_20261102.zip', '483fb6e34e4ca85ed77b0bb7f804a78146fe9389afe2539b0cfdf6aff3a568f3'),
    (25, 'NOEPIN_AL_025_FACT_VERIFICATION_LAYER_SUCCESSOR_V2_20261102.zip', '530048e1fc273dff768a5cf4e8db7ccb61c1384b72219474a226d36fdf47f123'),
    (26, 'NOEPIN_AL_026_POLICY_AS_CODE_ENGINE_SUCCESSOR_V2_20261102.zip', '712a6ee4edadc98c54d40c693f0ffe7be5ee70bf84fafcb251367cda72327b0b'),
    (27, 'NOEPIN_AL_027_AUTOMATIC_ROLLBACK_SNAPSHOT_SUCCESSOR_V2_20261102.zip', '6c723272aadd68b41eedb748a7e22aca99eacb006db700feb5ce1127e5e960bb'),
    (28, 'NOEPIN_AL_028_MULTI_AI_QUORUM_SUCCESSOR_V2_20261102.zip', '47c3828c071608ad11a9b69fef1b2e29fd8b1aa40b8cfdf8e28be4e8438c7a5f'),
    (29, 'NOEPIN_AL_029_UNCERTAINTY_HOLD_ENGINE_SUCCESSOR_V2_20261102.zip', '18af8d9329b6259fce14b9d841f0eb15b401acaf840e2da9e4d46d06d75b6976'),
    (30, 'NOEPIN_AL_030_AGENT_LIFECYCLE_MANAGEMENT_SUCCESSOR_V2_20261102.zip', '6df2f3d4b9395bed05bcd12bf445483aef5d507f3a5a6397a50a5265e255ec3b'),
    (31, 'NOEPIN_AL_031_DATA_MODEL_POISONING_MONITOR_SUCCESSOR_V2_20261102.zip', '84f7a0f920002fe73089d3517c29ed774c97d88f86ba84cc597f9b17544a70ce'),
    (32, 'NOEPIN_AL_032_VECTOR_DB_EMBEDDING_INTEGRITY_GUARD_SUCCESSOR_V2_20261102.zip', '51ca99fb65b9755e045ae908a6932cefd70379920397c3fbf1fe36e334a95762'),
    (33, 'NOEPIN_AL_033_USER_INTENT_CONSENT_MANAGEMENT_SUCCESSOR_V2_20261102.zip', 'ae00fbe22e53985c41ae5a9c2902416e17c4649053114392a1da0491fc121a65'),
    (34, 'NOEPIN_AL_034_TASK_SCOPE_BOUNDARY_ENFORCER_SUCCESSOR_V2_20261102.zip', 'ac18dba3b3697d2de40dfdffaf178efb131d2d15fe994b7f2d43996001ce85eb'),
    (35, 'NOEPIN_AL_035_SAFE_BROWSER_EMAIL_DOCUMENT_READ_GATE_SUCCESSOR_V2_20261102.zip', 'd4a1bdbb2426715c9c670da30d312deca63cb2a0b26dc737b3587bcaff744153'),
    (36, 'NOEPIN_AL_036_DIGITAL_TWIN_PRE_EXECUTION_IMPACT_PREDICTOR_SUCCESSOR_V2_20261103.zip', 'fd3450077cc2275470e16d40a6ce65b7e4e5a96bb55e988f6c5788541347f059'),
    (37, 'NOEPIN_AL_037_CRITICAL_SYSTEM_SAFETY_MODE_SUCCESSOR_V2_20261103.zip', '9b1f0d214d67f8fd5a75eb1e129b5c09b556e60f7de45def1c56c9956040fb5a'),
    (38, 'NOEPIN_AL_038_AI_MEMORY_RETENTION_DELETION_GOVERNOR_SUCCESSOR_V2_20261103.zip', '7d064227d0fe0a183f0417826af35b12c3f4ac4e74da6fddfcc0794cdcf20cd5'),
    (39, 'NOEPIN_AL_039_RULES_INTERNAL_POLICY_MATCHING_ENGINE_SUCCESSOR_V2_20261103.zip', '89deae5c0d98967559ff1d22ab9da88a937faff0f31506c6b092c265cd46b971'),
    (40, 'NOEPIN_AL_040_CONTINUOUS_AI_RED_TEAM_TEST_SUCCESSOR_V2_20261103.zip', '14b4530d44744b7ebca5deac2d30a837d7f195561de239ff083d57bfb8a6f457'),
    (41, 'NOEPIN_AL_041_AI_BEHAVIOR_ANOMALY_DETECTION_SUCCESSOR_V2_20261103.zip', 'e4aae0b80f7bf9f1cdeea23ebb32f78fe24de7e7d80c5f7b58a0a5e23b27f14a'),
    (42, 'NOEPIN_AL_042_AI_INCIDENT_RESPONSE_EVIDENCE_PRESERVATION_SUCCESSOR_V2_20261103.zip', 'd61f0356e0a8e061fb197a1e93f3629ac0355d0d73b6362ed197e1c097b02d7a'),
    (43, 'NOEPIN_AL_043_SAFE_AI_DELEGATION_HANDOFF_CONTROL_SUCCESSOR_V2_20261103.zip', '61cc01d1bcd44b27620317dda8ec8c86070143b2bfc4e45a8b6fd71088a2ec10'),
    (44, 'NOEPIN_AL_044_DATA_CLASSIFICATION_PURPOSE_LIMITATION_ENGINE_SUCCESSOR_V2_20261103.zip', '1b046ed6f3c27a619ea7c1104277a93ef87f68c0aad1c9e1e473a8724fb65c1e'),
    (45, 'NOEPIN_AL_045_UNDO_FIRST_ACTION_PLANNER_SUCCESSOR_V2_20261103.zip', '6894ce1431d1c3d077bdca1f638bc3aacb9a9fe34ef20371650954e4f4aa030d'),
    (46, 'NOEPIN_AL_046_FOUR_EYES_CONTROL_SUCCESSOR_V2_20261103.zip', 'e3c5a7e8d67b73b3a33ea32a5f8406df8f79c5e4a2e366dfc6409f259306dc02'),
    (47, 'NOEPIN_AL_047_RISK_SAFETY_BUDGET_MANAGER_SUCCESSOR_V2_20261103.zip', '8ca4e5f775c67d187ab071fd2f9389efe94cf32a78979c9478f190c58e19b0ed'),
    (48, 'NOEPIN_AL_048_TOOL_CHAIN_PLAN_INSPECTION_SUCCESSOR_V2_20261103.zip', '88e3b230175806a7791e1f9a549907bfe14aecdabac405f8cfc15249ee411345'),
    (49, 'NOEPIN_AL_049_MODEL_SELECTION_TRUST_ROUTER_SUCCESSOR_V2_20261103.zip', '389d345f989dc84a5a76baf22eb8fc110a16203b55a22c6ed9d8791cac1e86ed'),
    (50, 'NOEPIN_AL_050_INDEPENDENT_SAFETY_MONITOR_SUCCESSOR_V2_20261103.zip', 'e0adb34452f2aa74c09b9362dabbc72c4b541ebbc86c8c8e5812c1cdcba1b71c'),
    (51, 'NOEPIN_AL_051_SAFE_RAG_RETRIEVAL_GATEWAY_SUCCESSOR_V2_20261103.zip', '330d71ac03dd33b2396390e17e7a37e2985a52fe98e9642b7262f096cc9b4ce6'),
    (52, 'NOEPIN_AL_052_CONTENT_AUTHENTICITY_PROVENANCE_SUCCESSOR_V2_20261103.zip', '9943116289cfc66d9bb19807d96209ee0ea6badb82a4d6fbe8f4595d34714d73'),
    (53, 'NOEPIN_AL_053_AI_CHANGE_MANAGEMENT_VERSION_CONTROL_SUCCESSOR_V2_20261103.zip', 'bc390493beebae5307f1f446429328e3a55f887b051f997ee61623991997b096'),
    (54, 'NOEPIN_AL_054_ISOLATED_TEST_ENVIRONMENT_ORCHESTRATOR_SUCCESSOR_V2_20261103.zip', '060bf616e885d16738ba8b9b3c304acfe87184ca6d245b0300188d5cd2aa76a2'),
    (55, 'NOEPIN_AL_055_HUMAN_SOCIAL_ENGINEERING_DETECTION_SUCCESSOR_V2_20261103.zip', '20564161ca1d2cb6c2c5449e26a3e4dbee9f316a86ce1525e3d3ff48bd17ef18'),
    (56, 'NOEPIN_AL_056_DECISION_REASON_EXPLANATION_LAYER_SUCCESSOR_V2_20261103.zip', '8a2f69a4e2aa7852288578f21555e96c67877ce214307109264992f4052a1e3c'),
    (57, 'NOEPIN_AL_057_EMERGENCY_SAFE_MODE_OFFLINE_OPERATION_SUCCESSOR_V2_20261103.zip', 'fffc6a97320417f60354533129f79014d26627c5a02a885603190547414df239'),
    (58, 'NOEPIN_AL_058_TASK_BOUND_EPHEMERAL_CREDENTIAL_SUCCESSOR_V2_20261104.zip', 'd64f27bc6edd72a85f70cc4ac9c1c6d5bd762e0ad9ea2e91795ade25867841cc'),
    (59, 'NOEPIN_AL_059_EXTERNAL_AI_TOOL_TRUST_SCORE_SUCCESSOR_V2_20261104.zip', 'bca249131ba4e87569cd87e1abf4d9cdf64b709e178b30b371173977c78ff70e'),
    (60, 'NOEPIN_AL_060_AI_STOP_COMPLETION_CONDITION_CHECKER_SUCCESSOR_V2_20261104.zip', '197363ff164be85539663685325fe8c69d7ba757b953673df45a466d6425ef03'),
    (61, 'NOEPIN_AL_061_LOGICAL_EXECUTION_INTERLOCK_SUCCESSOR_V3_20261104.zip', '60c9a7f2244210d2543585136bdada9816bc87bc811b2768c0790739c398df28'),
)
EXPECTED_BY_ID={i:(f,h) for i,f,h in CONTROL_BASELINE}
SUITE_ZIP_SHA256='25c08aa1fbb16ce0c9f8111a3f212d2214987d9568b6764095d2bc7f87de58ae'
WHEEL_SHA256='e487143ce659812aceae6d928981dd298bc4f34dded1afcd394e57eae2070378'
SCHEMA_VERSION='1.0'
FALSE_FIELDS=(
'authoritative','permission_granted','permit_issued','credential_minted','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','world_truth_proven','domain_authority_promoted','memory_promoted_to_truth','belief_promoted_to_truth','candidate_promoted_to_actual','intent_promoted_to_action','action_request_promoted_to_success','safety_proven','dcsr_bypassed_control','dcsr_bypassed_gateway','dcsr_bypassed_policy','dcsr_bypassed_approval','dcsr_minted_permission','dcsr_promoted_cache_to_truth')

@dataclass(frozen=True)
class ControlArtifact:
    control_id:int; filename:str; sha256:str; verified:bool=True
@dataclass(frozen=True)
class SuiteRequest:
    request_id:str; enabled_controls:tuple[int,...]; gateway_decision:str='ALLOW'; control_decisions:tuple[tuple[int,str],...]=(); schema_version:str=SCHEMA_VERSION; context_fingerprint:str='ctx-default'; policy_fingerprint:str='pol-default'
@dataclass(frozen=True)
class SuiteResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState; request_id:str; controls_total:int; controls_enabled:int; controls_verified:int; registry_complete:bool; distribution_manifest_fingerprint:str; next_gate_candidate:bool; prepared_state_reused:bool=False; authoritative:bool=False; permission_granted:bool=False; permit_issued:bool=False; credential_minted:bool=False; approval_executed:bool=False; human_approval_executed:bool=False; tool_invoked:bool=False; action_executed:bool=False; action_success:bool=False; stop_executed:bool=False; file_write_executed:bool=False; network_send_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; memory_promoted_to_truth:bool=False; belief_promoted_to_truth:bool=False; candidate_promoted_to_actual:bool=False; intent_promoted_to_action:bool=False; action_request_promoted_to_success:bool=False; safety_proven:bool=False; dcsr_bypassed_control:bool=False; dcsr_bypassed_gateway:bool=False; dcsr_bypassed_policy:bool=False; dcsr_bypassed_approval:bool=False; dcsr_minted_permission:bool=False; dcsr_promoted_cache_to_truth:bool=False
@dataclass(frozen=True)
class PreparedState:
    request_fingerprint:str; artifacts_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str; result:SuiteResult
@dataclass(frozen=True)
class Delta:
    reused_fields:tuple[str,...]; missing_or_changed_fields:tuple[str,...]; metadata_bytes:int; full_revalidation_required:bool

def default_artifacts(): return tuple(ControlArtifact(i,f,h,True) for i,f,h in CONTROL_BASELINE)
def default_request(): return SuiteRequest('SUITE-188-A',tuple(range(1,62)),control_decisions=tuple((i,'ALLOW') for i in range(1,62)))
def _canon(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def _hash(v): return sha256(_canon(v).encode()).hexdigest()
def artifacts_fingerprint(arts): return _hash([(a.control_id,a.filename,a.sha256,a.verified) for a in arts])
def request_fingerprint(r): return _hash({'request_id':r.request_id,'enabled_controls':r.enabled_controls,'gateway_decision':r.gateway_decision,'control_decisions':r.control_decisions,'schema_version':r.schema_version,'context_fingerprint':r.context_fingerprint,'policy_fingerprint':r.policy_fingerprint})
def fingerprint(r): return _hash(r.__dict__ | {'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value})
def _result(decision,next_action,esc,state,req,arts,verified,registry,next_gate):
    return SuiteResult(decision,next_action,esc,state,req.request_id,61,len(req.enabled_controls),verified,registry,_hash({'request':request_fingerprint(req),'artifacts':artifacts_fingerprint(arts)}),next_gate)
def evaluate(req:SuiteRequest, arts:tuple[ControlArtifact,...]|None=None)->SuiteResult:
    arts=default_artifacts() if arts is None else tuple(arts)
    if not req.request_id: return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.MISSING_FIELD,EngineState.HOLD_CANDIDATE,req,arts,0,False,False)
    if req.schema_version!=SCHEMA_VERSION: return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.SCHEMA_MISMATCH,EngineState.HOLD_CANDIDATE,req,arts,0,False,False)
    ids=[a.control_id for a in arts]; registry=(len(arts)==61 and sorted(ids)==list(range(1,62)) and len(set(ids))==61)
    if not registry: return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.CONTROL_REGISTRY_GAP,EngineState.HOLD_CANDIDATE,req,arts,0,False,False)
    verified=0
    for a in arts:
        exp=EXPECTED_BY_ID.get(a.control_id)
        if not exp or exp!=(a.filename,a.sha256) or not a.verified:
            return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.CONTROL_ARTIFACT_MISMATCH,EngineState.HOLD_CANDIDATE,req,arts,verified,True,False)
        verified+=1
    enabled=tuple(req.enabled_controls)
    if not enabled or len(set(enabled))!=len(enabled) or any(i not in EXPECTED_BY_ID for i in enabled):
        return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.INVALID_CONTROL_SELECTION,EngineState.HOLD_CANDIDATE,req,arts,verified,True,False)
    try: gd=Decision(req.gateway_decision)
    except Exception: return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.INVALID_DECISION,EngineState.HOLD_CANDIDATE,req,arts,verified,True,False)
    decmap={i:'ALLOW' for i in enabled}
    for i,d in req.control_decisions:
        if i not in enabled: continue
        try: Decision(d)
        except Exception: return _result(Decision.HOLD,NextAction.HOLD_FOR_EVIDENCE,Escalation.INVALID_DECISION,EngineState.HOLD_CANDIDATE,req,arts,verified,True,False)
        decmap[i]=d
    ds=[gd]+[Decision(decmap[i]) for i in enabled]
    if Decision.DENY in ds: d=Decision.DENY; na=NextAction.STOP_CANDIDATE; st=EngineState.DENY_CANDIDATE
    elif Decision.HUMAN_APPROVAL in ds: d=Decision.HUMAN_APPROVAL; na=NextAction.REQUEST_HUMAN_APPROVAL_CANDIDATE; st=EngineState.HUMAN_APPROVAL_CANDIDATE
    elif Decision.HOLD in ds: d=Decision.HOLD; na=NextAction.HOLD_FOR_EVIDENCE; st=EngineState.HOLD_CANDIDATE
    else: d=Decision.ALLOW; na=NextAction.CONTINUE_TO_EXTERNAL_POLICY_PERMIT_CANDIDATE; st=EngineState.DISTRIBUTION_CANDIDATE
    return _result(d,na,Escalation.NONE,st,req,arts,verified,True,d==Decision.ALLOW)
def default_evaluation(): return evaluate(default_request())
def prepare_state(req=None,arts=None):
    req=default_request() if req is None else req; arts=default_artifacts() if arts is None else tuple(arts); r=evaluate(req,arts); rf=request_fingerprint(req); af=artifacts_fingerprint(arts); rr=fingerprint(r); integ=_hash({'request':rf,'artifacts':af,'result':rr}); return PreparedState(rf,af,rr,integ,r)
def evaluate_prepared(p:PreparedState,*,integrity_validated:bool,current_request:SuiteRequest,current_artifacts:tuple[ControlArtifact,...],current_result_fingerprint:str,current_integrity_fingerprint:str):
    ok=integrity_validated and p.request_fingerprint==request_fingerprint(current_request) and p.artifacts_fingerprint==artifacts_fingerprint(current_artifacts) and p.result_fingerprint==current_result_fingerprint and p.integrity_fingerprint==current_integrity_fingerprint
    if ok: return replace(p.result,prepared_state_reused=True)
    r=evaluate(current_request,current_artifacts); return replace(r,decision=Decision.HOLD,next_action=NextAction.HOLD_FOR_EVIDENCE,escalation=Escalation.PREPARED_STATE_STALE,engine_state=EngineState.HOLD_CANDIDATE,next_gate_candidate=False)
def make_delta(req,arts,known):
    cur={'REQUEST':request_fingerprint(req),'CONTROL_ARTIFACT_REGISTRY':artifacts_fingerprint(arts),'SUITE_DISTRIBUTION':_hash({'suite_zip':SUITE_ZIP_SHA256,'wheel':WHEEL_SHA256})}
    reused=tuple(sorted(k for k,v in cur.items() if known.get(k)==v)); missing=tuple(sorted(k for k,v in cur.items() if known.get(k)!=v)); meta=len(_canon({'missing':missing,'fingerprints':{k:cur[k] for k in missing}}).encode()); return Delta(reused,missing,meta,len(missing)>=2)
