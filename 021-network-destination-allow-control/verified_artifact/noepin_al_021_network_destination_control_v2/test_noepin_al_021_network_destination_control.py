import unittest, hashlib, json
from noepin_al_021_network_destination_control import *

def permit(**kw):
 d=dict(permit_id='p',agent_id='a',allowed_kinds=(DestinationKind.DOMAIN,DestinationKind.API,DestinationKind.IP,DestinationKind.NETWORK),allowed_destinations=('api.example.com','1.2.3.4','10.0.0.0/24'),allowed_purposes=('fetch','post'),allowed_environments=(Environment.DEV,Environment.STAGING,Environment.PROD),version=1,expires_epoch_s=9999999999,revoked=False,issuer_ref='issuer')
 d.update(kw); return NetworkPermit(**d)
def req(**kw):
 d=dict(request_id='r',agent_id='a',destination_kind=DestinationKind.DOMAIN,destination='api.example.com',purpose='fetch',environment=Environment.DEV,now_epoch_s=100,permit=permit(),dns_resolved_ip='1.2.3.4',dns_verified=True,tls_required=True,tls_verified=True,private_network=False,unknown_destination=False,external_side_effect=False,high_risk=False,human_approved=False,approval_ref=None,schema_version='1',context={})
 d.update(kw); return NetworkRequest(**d)
class T(unittest.TestCase):
 def setUp(self): self.c=NetworkDestinationControl('v2')
 def check(self,r,d):
  x=self.c.evaluate(r); self.assertEqual(x.decision,d); self.assertFalse(x.authoritative); self.assertFalse(x.network_connected); self.assertFalse(x.data_sent); self.assertFalse(x.action_succeeded); return x
 def test_01_allow(self): self.check(req(),NetDecision.ALLOW_PREPARE)
 def test_02_missing_request(self): self.check(req(request_id=''),NetDecision.HOLD)
 def test_03_missing_agent(self): self.check(req(agent_id=''),NetDecision.HOLD)
 def test_04_missing_dest(self): self.check(req(destination=''),NetDecision.HOLD)
 def test_05_missing_purpose(self): self.check(req(purpose=''),NetDecision.HOLD)
 def test_06_bad_time(self): self.check(req(now_epoch_s=-1),NetDecision.HOLD)
 def test_07_no_permit(self): self.check(req(permit=None),NetDecision.DENY)
 def test_08_bad_permit(self): self.check(req(permit=permit(permit_id='')),NetDecision.HOLD)
 def test_09_revoked(self): self.check(req(permit=permit(revoked=True)),NetDecision.DENY)
 def test_10_expired(self): self.check(req(permit=permit(expires_epoch_s=100)),NetDecision.DENY)
 def test_11_agent_mismatch(self): self.check(req(permit=permit(agent_id='b')),NetDecision.DENY)
 def test_12_kind_denied(self): self.check(req(destination_kind=DestinationKind.API,permit=permit(allowed_kinds=(DestinationKind.DOMAIN,))),NetDecision.DENY)
 def test_13_dest_denied(self): self.check(req(destination='evil.example'),NetDecision.DENY)
 def test_14_purpose_denied(self): self.check(req(purpose='delete'),NetDecision.DENY)
 def test_15_env_denied(self): self.check(req(environment=Environment.PROD,permit=permit(allowed_environments=(Environment.DEV,))),NetDecision.DENY)
 def test_16_unknown(self): self.check(req(unknown_destination=True),NetDecision.DENY)
 def test_17_bad_ip(self): self.check(req(dns_resolved_ip='bad'),NetDecision.HOLD)
 def test_18_dns_not_verified(self): self.check(req(dns_verified=False),NetDecision.HOLD)
 def test_19_tls_required(self): self.check(req(tls_verified=False),NetDecision.HOLD)
 def test_20_tls_optional(self): self.check(req(tls_required=False,tls_verified=False),NetDecision.ALLOW_PREPARE)
 def test_21_prod_risk(self): self.check(req(environment=Environment.PROD,high_risk=True),NetDecision.HUMAN_CONFIRM)
 def test_22_prod_side_effect(self): self.check(req(environment=Environment.PROD,external_side_effect=True),NetDecision.HUMAN_CONFIRM)
 def test_23_prod_approved(self): self.check(req(environment=Environment.PROD,high_risk=True,human_approved=True,approval_ref='H'),NetDecision.ALLOW_PREPARE)
 def test_24_approval_bool_only(self): self.check(req(environment=Environment.PROD,high_risk=True,human_approved=True),NetDecision.HUMAN_CONFIRM)
 def test_25_domain_normalize(self): self.check(req(destination='API.EXAMPLE.COM.'),NetDecision.ALLOW_PREPARE)
 def test_26_ip_allow(self): self.check(req(destination_kind=DestinationKind.IP,destination='1.2.3.4',dns_resolved_ip=None),NetDecision.ALLOW_PREPARE)
 def test_27_ip_deny(self): self.check(req(destination_kind=DestinationKind.IP,destination='1.2.3.5',dns_resolved_ip=None),NetDecision.DENY)
 def test_28_network_allow(self): self.check(req(destination_kind=DestinationKind.NETWORK,destination='10.0.0.1/24',dns_resolved_ip=None),NetDecision.ALLOW_PREPARE)
 def test_29_network_deny(self): self.check(req(destination_kind=DestinationKind.NETWORK,destination='10.0.1.0/24',dns_resolved_ip=None),NetDecision.DENY)
 def test_30_api_allow(self): self.check(req(destination_kind=DestinationKind.API,destination='api.example.com'),NetDecision.ALLOW_PREPARE)
 def test_31_cache_exact(self):
  r=req(); a=self.c.evaluate(r); b=self.c.evaluate(r); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
 def test_32_cache_no_authority(self):
  r=req(); self.c.evaluate(r); self.assertFalse(self.c.evaluate(r).authoritative)
 def test_33_cache_no_connect(self):
  r=req(); self.c.evaluate(r); self.assertFalse(self.c.evaluate(r).network_connected)
 def test_34_cache_no_send(self):
  r=req(); self.c.evaluate(r); self.assertFalse(self.c.evaluate(r).data_sent)
 def test_35_fingerprint_dest(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(destination='x')))
 def test_36_fingerprint_purpose(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(purpose='post')))
 def test_37_fingerprint_env(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(environment=Environment.STAGING)))
 def test_38_fingerprint_permit_version(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(permit=permit(version=2))))
 def test_39_fingerprint_revocation(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(permit=permit(revoked=True))))
 def test_40_fingerprint_expiry(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(permit=permit(expires_epoch_s=200))))
 def test_41_fingerprint_dns(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(dns_verified=False)))
 def test_42_fingerprint_tls(self): self.assertNotEqual(self.c.fingerprint(req()),self.c.fingerprint(req(tls_verified=False)))
 def test_43_fingerprint_context_order(self): self.assertEqual(self.c.fingerprint(req(context={'b':2,'a':1})),self.c.fingerprint(req(context={'a':1,'b':2})))
 def test_44_clear_cache(self): self.c.evaluate(req()); self.assertGreater(self.c.cache_size(),0); self.c.clear_cache(); self.assertEqual(self.c.cache_size(),0)
 def test_45_allow_not_success(self): self.assertFalse(self.check(req(),NetDecision.ALLOW_PREPARE).action_succeeded)
 def test_46_allow_not_connect(self): self.assertFalse(self.check(req(),NetDecision.ALLOW_PREPARE).network_connected)
 def test_47_allow_not_send(self): self.assertFalse(self.check(req(),NetDecision.ALLOW_PREPARE).data_sent)
 def test_48_permit_presence_not_enough(self): self.check(req(destination='evil.example'),NetDecision.DENY)
 def test_49_dns_match_not_purpose(self): self.check(req(purpose='x'),NetDecision.DENY)
 def test_50_allowlist_not_env(self): self.check(req(environment=Environment.PROD,permit=permit(allowed_environments=(Environment.DEV,))),NetDecision.DENY)
 def test_51_prod_approval_not_success(self): self.assertFalse(self.check(req(environment=Environment.PROD,high_risk=True,human_approved=True,approval_ref='H'),NetDecision.ALLOW_PREPARE).action_succeeded)
 def test_52_private_network_still_policy(self): self.check(req(private_network=True),NetDecision.ALLOW_PREPARE)

def replay_fingerprint():
 c=NetworkDestinationControl('v2'); out=[]
 for i in range(1000):
  r=req(request_id=f'r{i}',purpose='fetch' if i%5 else 'post',environment=(Environment.DEV,Environment.STAGING,Environment.PROD)[i%3],high_risk=(i%17==0),human_approved=(i%17==0),approval_ref='H' if i%17==0 else None,context={'i':i%11})
  out.append(c.evaluate(r).stable_payload())
 raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode(); return hashlib.sha256(raw).hexdigest()
if __name__=='__main__': unittest.main()
