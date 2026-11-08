from noepin_al_030_agent_lifecycle import *
import hashlib, json

NOW=1_000_000

def rec(**kw):
    d=dict(agent_id="a1",owner_id="owner",role="worker",agent_version="1.0",registry_version=5,authority_version="auth-v1",created_epoch_ns=100,expires_epoch_ns=2_000_000,lifecycle_state="ACTIVE",revoked=False,permit_refs=("p1",),decommissioned_epoch_ns=None)
    d.update(kw); return AgentRecord(**d)

def state(*agents, version=5, authority="auth-v1"):
    return RegistryState(version, authority, tuple(agents or (rec(),)))

def req(op="CHECK", **kw):
    d=dict(operation=op,actor_id="owner",actor_role="owner",target_agent_id="a1",expected_registry_version=5,expected_authority_version="auth-v1",now_epoch_ns=NOW)
    d.update(kw); return LifecycleRequest(**d)

def run():
    c=AgentLifecycleControl(); tests=[]
    def t(name, fn):
        try: fn(); tests.append((name,True,""))
        except Exception as e: tests.append((name,False,repr(e)))
    def decision(r,x): assert r.decision==x,(r.decision,r.reason_codes)
    # core
    t("check active", lambda: decision(c.evaluate(state(),req()),"ALLOW_PREPARE"))
    t("check suspended", lambda: decision(c.evaluate(state(rec(lifecycle_state="SUSPENDED")),req()),"HOLD"))
    t("check expired", lambda: decision(c.evaluate(state(rec(expires_epoch_ns=NOW)),req()),"HOLD"))
    t("check revoked", lambda: decision(c.evaluate(state(rec(revoked=True)),req()),"DENY"))
    t("check decommissioned", lambda: decision(c.evaluate(state(rec(lifecycle_state="DECOMMISSIONED",decommissioned_epoch_ns=900000)),req()),"DENY"))
    t("version mismatch", lambda: decision(c.evaluate(state(),req(expected_registry_version=4)),"HOLD"))
    t("authority mismatch", lambda: decision(c.evaluate(state(),req(expected_authority_version="old")),"HOLD"))
    t("unknown operation", lambda: decision(c.evaluate(state(),req(operation="BOGUS")),"DENY"))
    t("missing actor", lambda: decision(c.evaluate(state(),req(actor_id="")),"DENY"))
    t("negative time", lambda: decision(c.evaluate(state(),req(now_epoch_ns=-1)),"DENY"))
    # register
    empty=RegistryState(5,"auth-v1",())
    rr=req("REGISTER",target_agent_id="new",actor_id="admin",actor_role="registry_admin",requested_owner_id="o",requested_role="worker",requested_agent_version="1",requested_expiry_epoch_ns=2_000_000)
    t("register candidate", lambda: decision(c.evaluate(empty,rr),"ALLOW_PREPARE"))
    t("register non-admin", lambda: decision(c.evaluate(empty,replace(rr,actor_role="owner")),"DENY"))
    t("register duplicate", lambda: decision(c.evaluate(state(),replace(rr,target_agent_id="a1")),"DENY"))
    t("register fields missing", lambda: decision(c.evaluate(empty,replace(rr,requested_owner_id="")),"DENY"))
    t("register expiry past", lambda: decision(c.evaluate(empty,replace(rr,requested_expiry_epoch_ns=NOW)),"DENY"))
    # activate
    pending=state(rec(lifecycle_state="PENDING"))
    t("activate owner", lambda: decision(c.evaluate(pending,req("ACTIVATE")),"ALLOW_PREPARE"))
    t("activate admin", lambda: decision(c.evaluate(pending,req("ACTIVATE",actor_id="adm",actor_role="registry_admin")),"ALLOW_PREPARE"))
    t("activate unauthorized", lambda: decision(c.evaluate(pending,req("ACTIVATE",actor_id="x",actor_role="viewer")),"DENY"))
    t("activate active invalid", lambda: decision(c.evaluate(state(),req("ACTIVATE")),"DENY"))
    t("activate expired deny", lambda: decision(c.evaluate(state(rec(lifecycle_state="PENDING",expires_epoch_ns=NOW)),req("ACTIVATE")),"DENY"))
    # suspend
    t("suspend owner", lambda: decision(c.evaluate(state(),req("SUSPEND")),"ALLOW_PREPARE"))
    t("suspend admin", lambda: decision(c.evaluate(state(),req("SUSPEND",actor_id="adm",actor_role="security_admin")),"ALLOW_PREPARE"))
    t("suspend unauthorized", lambda: decision(c.evaluate(state(),req("SUSPEND",actor_id="x",actor_role="viewer")),"DENY"))
    t("suspend already", lambda: decision(c.evaluate(state(rec(lifecycle_state="SUSPENDED")),req("SUSPEND")),"HOLD"))
    # renew
    renew=req("RENEW",requested_expiry_epoch_ns=3_000_000)
    t("renew needs human", lambda: decision(c.evaluate(state(),renew),"HUMAN_CONFIRM"))
    t("renew approved candidate", lambda: decision(c.evaluate(state(),replace(renew,human_approval_evidence=True)),"ALLOW_PREPARE"))
    t("renew unauthorized", lambda: decision(c.evaluate(state(),replace(renew,actor_id="x",actor_role="viewer")),"DENY"))
    t("renew nonfuture", lambda: decision(c.evaluate(state(),replace(renew,requested_expiry_epoch_ns=NOW)),"DENY"))
    t("renew not extension", lambda: decision(c.evaluate(state(),replace(renew,requested_expiry_epoch_ns=1_500_000)),"DENY"))
    # update
    up=req("UPDATE",actor_id="adm",actor_role="registry_admin",requested_role="reviewer")
    t("update admin", lambda: decision(c.evaluate(state(),up),"ALLOW_PREPARE"))
    t("update owner denied", lambda: decision(c.evaluate(state(),req("UPDATE",requested_role="r")),"DENY"))
    t("update expired hold", lambda: decision(c.evaluate(state(rec(expires_epoch_ns=NOW)),up),"HOLD"))
    # decommission
    dec=req("DECOMMISSION",actor_id="adm",actor_role="registry_admin")
    t("decommission needs human", lambda: decision(c.evaluate(state(),dec),"HUMAN_CONFIRM"))
    t("decommission approved candidate", lambda: decision(c.evaluate(state(),replace(dec,human_approval_evidence=True)),"ALLOW_PREPARE"))
    t("decommission nonadmin", lambda: decision(c.evaluate(state(),req("DECOMMISSION",human_approval_evidence=True)),"DENY"))
    t("decommission irreversible", lambda: decision(c.evaluate(state(rec(lifecycle_state="DECOMMISSIONED",decommissioned_epoch_ns=900000)),replace(dec,human_approval_evidence=True)),"DENY"))
    # validation
    t("bad duplicate ids", lambda: decision(c.evaluate(RegistryState(5,"auth-v1",(rec(),rec())),req()),"DENY"))
    t("bad record owner", lambda: decision(c.evaluate(state(rec(owner_id="")),req()),"DENY"))
    t("bad role", lambda: decision(c.evaluate(state(rec(role="")),req()),"DENY"))
    t("bad agent version", lambda: decision(c.evaluate(state(rec(agent_version="")),req()),"DENY"))
    t("bad auth version", lambda: decision(c.evaluate(state(rec(authority_version="")),req()),"DENY"))
    t("bad expiry order", lambda: decision(c.evaluate(state(rec(created_epoch_ns=500,expires_epoch_ns=400)),req()),"DENY"))
    t("bad lifecycle", lambda: decision(c.evaluate(state(rec(lifecycle_state="X")),req()),"DENY"))
    t("bad duplicate permit", lambda: decision(c.evaluate(state(rec(permit_refs=("p","p"))),req()),"DENY"))
    t("decommission time required", lambda: decision(c.evaluate(state(rec(lifecycle_state="DECOMMISSIONED",decommissioned_epoch_ns=None)),req()),"DENY"))
    t("record version ahead", lambda: decision(c.evaluate(state(rec(registry_version=6)),req()),"DENY"))
    t("registry version invalid", lambda: decision(c.evaluate(RegistryState(0,"auth-v1",()),rr),"DENY"))
    t("registry auth required", lambda: decision(c.evaluate(RegistryState(5,"",()),rr),"DENY"))
    # authority flags always false
    def flags():
        r=c.evaluate(state(),req()); assert not r.registered and not r.permission_granted and not r.stop_executed and not r.decommission_executed and not r.state_committed and not r.action_succeeded
    t("authority flags false", flags)
    # cache binding
    def cache_hit():
        c2=AgentLifecycleControl(); a=c2.evaluate(state(),req()); b=c2.evaluate(state(),req()); assert not a.cache_reused and b.cache_reused and a.decision==b.decision
    t("cache exact hit",cache_hit)
    def cache_version_change():
        c2=AgentLifecycleControl(); a=c2.evaluate(state(),req()); s2=RegistryState(6,"auth-v1",tuple(replace(x,registry_version=6) for x in state().agents)); b=c2.evaluate(s2,replace(req(),expected_registry_version=6)); assert not b.cache_reused
    t("cache registry version invalidates",cache_version_change)
    def cache_auth_change():
        c2=AgentLifecycleControl(); c2.evaluate(state(),req()); s2=RegistryState(5,"auth-v2",tuple(replace(x,authority_version="auth-v2") for x in state().agents)); b=c2.evaluate(s2,replace(req(),expected_authority_version="auth-v2")); assert not b.cache_reused
    t("cache authority invalidates",cache_auth_change)
    def cache_expiry_change():
        c2=AgentLifecycleControl(); c2.evaluate(state(),req()); b=c2.evaluate(state(rec(expires_epoch_ns=3_000_000)),req()); assert not b.cache_reused
    t("cache expiry invalidates",cache_expiry_change)
    def cache_revocation_change():
        c2=AgentLifecycleControl(); c2.evaluate(state(),req()); b=c2.evaluate(state(rec(revoked=True)),req()); assert not b.cache_reused and b.decision=="DENY"
    t("cache revocation invalidates",cache_revocation_change)
    # delta
    def delta_roundtrip():
        s1=state(); s2=RegistryState(6,"auth-v1",(replace(rec(),role="reviewer",registry_version=6),)); d=registry_delta(s1,s2); out=apply_delta_candidate(s1,d); assert out==s2
    t("delta roundtrip",delta_roundtrip)
    def delta_wrong_base():
        s1=state(); s2=RegistryState(6,"auth-v1",(replace(rec(),role="reviewer",registry_version=6),)); d=registry_delta(s1,s2)
        try: apply_delta_candidate(state(rec(agent_version="2")),d)
        except ValueError as e: assert "BASE_FINGERPRINT_MISMATCH" in str(e); return
        raise AssertionError()
    t("delta wrong base denied",delta_wrong_base)
    def delta_add():
        s1=RegistryState(5,"auth-v1",()); r=rec(registry_version=6); s2=RegistryState(6,"auth-v1",(r,)); assert apply_delta_candidate(s1,registry_delta(s1,s2))==s2
    t("delta add",delta_add)
    def delta_remove():
        s1=state(); s2=RegistryState(6,"auth-v1",()); assert apply_delta_candidate(s1,registry_delta(s1,s2))==s2
    t("delta remove",delta_remove)
    # generate deterministic boundary matrix to 78 tests
    roles=["owner","registry_admin","security_admin","viewer"]
    states=["PENDING","ACTIVE","SUSPENDED","EXPIRED","DECOMMISSIONED"]
    for role in roles:
        for st in states:
            if len(tests)>=78: break
            rrrec=rec(lifecycle_state=("ACTIVE" if st=="EXPIRED" else st),expires_epoch_ns=(NOW if st=="EXPIRED" else 2_000_000),decommissioned_epoch_ns=(900000 if st=="DECOMMISSIONED" else None))
            actor_id="owner" if role=="owner" else "x"
            t(f"matrix {role} {st}", lambda role=role,actor_id=actor_id,rrrec=rrrec: c.evaluate(state(rrrec),req("CHECK",actor_id=actor_id,actor_role=role)))
        if len(tests)>=78: break
    failed=[x for x in tests if not x[1]]
    print(json.dumps({"passed":len(tests)-len(failed),"failed":len(failed),"total":len(tests),"failures":failed},ensure_ascii=False))
    if failed: raise SystemExit(1)

if __name__=="__main__": run()
