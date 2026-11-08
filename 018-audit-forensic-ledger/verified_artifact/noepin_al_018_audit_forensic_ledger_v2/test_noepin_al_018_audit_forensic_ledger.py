import hashlib, json, unittest
from dataclasses import replace
from noepin_al_018_audit_forensic_ledger import *

H0="0"*64
H1="1"*64
H2="2"*64

def ev(i=1, **kw):
    d=dict(
        event_id=f"e{i}", run_id="run1", actor_ref="agent1", event_type=EventType.INPUT,
        observed_epoch_ns=1000+i, payload_fingerprint=H0, source_ref="source",
        decision=None, claimed_outcome=None, approval_ref=None, evidence_refs=(),
        authority_version=1, target_version="v1", metadata={}
    )
    d.update(kw)
    return AuditEvent(**d)

class T(unittest.TestCase):
    def setUp(self):
        self.l=AuditForensicLedger(policy_version="v2")

    def test_empty_valid(self):
        r=self.l.verify(); self.assertTrue(r.valid); self.assertEqual(r.record_count,0); self.assertEqual(r.head_hash,H0)
    def test_append_one(self):
        r=self.l.append(ev(),appended_epoch_ns=2000); self.assertEqual(r.sequence,1); self.assertEqual(r.previous_hash,H0)
    def test_append_two_chain(self):
        a=self.l.append(ev(1),appended_epoch_ns=2000); b=self.l.append(ev(2),appended_epoch_ns=2001); self.assertEqual(b.previous_hash,a.record_hash)
    def test_verify_valid(self):
        self.l.append(ev(),appended_epoch_ns=2000); self.assertTrue(self.l.verify().valid)
    def test_records_tuple(self):
        self.l.append(ev(),appended_epoch_ns=2000); self.assertIsInstance(self.l.records(),tuple)
    def test_head_hash(self):
        r=self.l.append(ev(),appended_epoch_ns=2000); self.assertEqual(self.l.head_hash(),r.record_hash)
    def test_missing_event_id(self):
        with self.assertRaises(ValueError): self.l.append(ev(event_id=""),appended_epoch_ns=2000)
    def test_missing_run(self):
        with self.assertRaises(ValueError): self.l.append(ev(run_id=""),appended_epoch_ns=2000)
    def test_missing_actor(self):
        with self.assertRaises(ValueError): self.l.append(ev(actor_ref=""),appended_epoch_ns=2000)
    def test_missing_source(self):
        with self.assertRaises(ValueError): self.l.append(ev(source_ref=""),appended_epoch_ns=2000)
    def test_bad_observed(self):
        with self.assertRaises(ValueError): self.l.append(ev(observed_epoch_ns=-1),appended_epoch_ns=2000)
    def test_bool_observed(self):
        with self.assertRaises(ValueError): self.l.append(ev(observed_epoch_ns=True),appended_epoch_ns=2000)
    def test_bad_payload_hash(self):
        with self.assertRaises(ValueError): self.l.append(ev(payload_fingerprint="bad"),appended_epoch_ns=2000)
    def test_bad_authority_version(self):
        with self.assertRaises(ValueError): self.l.append(ev(authority_version=0),appended_epoch_ns=2000)
    def test_duplicate_event_id(self):
        self.l.append(ev(),appended_epoch_ns=2000)
        with self.assertRaises(ValueError): self.l.append(ev(),appended_epoch_ns=2001)
    def test_bad_append_time(self):
        with self.assertRaises(ValueError): self.l.append(ev(),appended_epoch_ns=-1)
    def test_append_time_regression_rejected(self):
        self.l.append(ev(1),appended_epoch_ns=2000)
        with self.assertRaises(ValueError): self.l.append(ev(2),appended_epoch_ns=1999)

    def test_search_run(self):
        self.l.append(ev(1,run_id="a"),appended_epoch_ns=2000); self.l.append(ev(2,run_id="b"),appended_epoch_ns=2001)
        self.assertEqual(len(self.l.search(run_id="a")),1)
    def test_search_actor(self):
        self.l.append(ev(1,actor_ref="a"),appended_epoch_ns=2000); self.l.append(ev(2,actor_ref="b"),appended_epoch_ns=2001)
        self.assertEqual(self.l.search(actor_ref="b")[0].event.actor_ref,"b")
    def test_search_type(self):
        self.l.append(ev(1,event_type=EventType.INPUT),appended_epoch_ns=2000); self.l.append(ev(2,event_type=EventType.SECURITY),appended_epoch_ns=2001)
        self.assertEqual(len(self.l.search(event_type=EventType.SECURITY)),1)
    def test_search_approval(self):
        self.l.append(ev(1,approval_ref="H1"),appended_epoch_ns=2000); self.assertEqual(len(self.l.search(approval_ref="H1")),1)
    def test_reconstruct(self):
        self.l.append(ev(1,run_id="r"),appended_epoch_ns=2000); self.assertEqual(len(self.l.reconstruct_run("r")),1)
    def test_reconstruct_empty_id(self):
        with self.assertRaises(ValueError): self.l.reconstruct_run("")

    def test_tamper_event_detected(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        tam=replace(r,event=replace(r.event,claimed_outcome="SUCCESS"))
        v=self.l.verify_records((tam,)); self.assertFalse(v.valid); self.assertIn("RECORD_HASH_MISMATCH:1",v.reason_codes)
    def test_tamper_prev_detected(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        tam=replace(r,previous_hash=H1); self.assertFalse(self.l.verify_records((tam,)).valid)
    def test_tamper_hash_detected(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        tam=replace(r,record_hash=H1); self.assertFalse(self.l.verify_records((tam,)).valid)
    def test_sequence_detected(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        tam=replace(r,sequence=2); self.assertFalse(self.l.verify_records((tam,)).valid)
    def test_time_regression_detected(self):
        a=self.l.append(ev(1),appended_epoch_ns=2000); b=self.l.append(ev(2),appended_epoch_ns=2001)
        b2=replace(b,appended_epoch_ns=1999,record_hash=self.l.compute_record_hash(2,b.event,b.previous_hash,1999))
        self.assertFalse(self.l.verify_records((a,b2)).valid)
    def test_duplicate_id_detected(self):
        a=self.l.append(ev(1),appended_epoch_ns=2000)
        b_event=replace(ev(2),event_id="e1")
        b=LedgerRecord(2,b_event,a.record_hash,self.l.compute_record_hash(2,b_event,a.record_hash,2001),2001)
        self.assertFalse(self.l.verify_records((a,b)).valid)

    def test_recorded_claim_not_truth(self):
        self.l.append(ev(claimed_outcome="SUCCESS"),appended_epoch_ns=2000); self.assertFalse(self.l.verify().truth_established)
    def test_action_result_not_success_authority(self):
        self.l.append(ev(event_type=EventType.ACTION_RESULT,claimed_outcome="SUCCESS"),appended_epoch_ns=2000)
        self.assertFalse(self.l.verify().action_success_established)
    def test_approval_ref_not_authority(self):
        self.l.append(ev(approval_ref="H"),appended_epoch_ns=2000); self.assertFalse(self.l.verify().authoritative)
    def test_hash_integrity_not_truth(self):
        self.l.append(ev(),appended_epoch_ns=2000); v=self.l.verify(); self.assertTrue(v.valid); self.assertFalse(v.truth_established)
    def test_snapshot_no_authority(self):
        self.l.append(ev(),appended_epoch_ns=2000); s=self.l.export_snapshot(); self.assertFalse(s["authoritative"]); self.assertFalse(s["truth_established"])

    def test_cache_reused(self):
        self.l.append(ev(),appended_epoch_ns=2000); a=self.l.verify(); b=self.l.verify(); self.assertFalse(a.cache_reused); self.assertTrue(b.cache_reused)
    def test_cache_never_authority(self):
        self.l.append(ev(),appended_epoch_ns=2000); self.l.verify(); self.assertFalse(self.l.verify().authoritative)
    def test_append_invalidates_cache(self):
        self.l.append(ev(1),appended_epoch_ns=2000); self.l.verify(); self.assertGreater(self.l.cache_size(),0)
        self.l.append(ev(2),appended_epoch_ns=2001); self.assertEqual(self.l.cache_size(),0)
    def test_full_record_fingerprint_tamper_changes(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        tam=replace(r,event=replace(r.event,metadata={"x":1}))
        a=self.l.verify_records((r,)).ledger_fingerprint; b=self.l.verify_records((tam,)).ledger_fingerprint
        self.assertNotEqual(a,b)
    def test_clear_cache(self):
        self.l.append(ev(),appended_epoch_ns=2000); self.l.verify(); self.l.clear_cache(); self.assertEqual(self.l.cache_size(),0)

    def test_event_types(self):
        ts=2000
        for i,t in enumerate(EventType,1):
            self.l.append(ev(i,event_type=t),appended_epoch_ns=ts+i)
        self.assertEqual(len(self.l.records()),len(EventType))
    def test_metadata_order_deterministic(self):
        a=ev(metadata={"b":2,"a":1}); b=ev(metadata={"a":1,"b":2})
        ha=self.l.compute_record_hash(1,a,H0,2000); hb=self.l.compute_record_hash(1,b,H0,2000); self.assertEqual(ha,hb)
    def test_evidence_refs_affect_hash(self):
        a=ev(evidence_refs=("x",)); b=ev(evidence_refs=("y",))
        self.assertNotEqual(self.l.compute_record_hash(1,a,H0,2000),self.l.compute_record_hash(1,b,H0,2000))
    def test_target_version_affects_hash(self):
        a=ev(target_version="v1"); b=ev(target_version="v2")
        self.assertNotEqual(self.l.compute_record_hash(1,a,H0,2000),self.l.compute_record_hash(1,b,H0,2000))
    def test_authority_version_affects_hash(self):
        a=ev(authority_version=1); b=ev(authority_version=2)
        self.assertNotEqual(self.l.compute_record_hash(1,a,H0,2000),self.l.compute_record_hash(1,b,H0,2000))
    def test_decision_affects_hash(self):
        a=ev(decision="ALLOW"); b=ev(decision="DENY")
        self.assertNotEqual(self.l.compute_record_hash(1,a,H0,2000),self.l.compute_record_hash(1,b,H0,2000))
    def test_claimed_outcome_affects_hash(self):
        a=ev(claimed_outcome="OK"); b=ev(claimed_outcome="FAIL")
        self.assertNotEqual(self.l.compute_record_hash(1,a,H0,2000),self.l.compute_record_hash(1,b,H0,2000))
    def test_run_order(self):
        for i in range(1,6): self.l.append(ev(i,run_id="r"),appended_epoch_ns=2000+i)
        self.assertEqual(tuple(r.sequence for r in self.l.reconstruct_run("r")),(1,2,3,4,5))
    def test_snapshot_record_count(self):
        for i in range(1,4): self.l.append(ev(i),appended_epoch_ns=2000+i)
        self.assertEqual(self.l.export_snapshot()["record_count"],3)
    def test_no_delete_update_methods(self):
        self.assertFalse(hasattr(self.l,"delete")); self.assertFalse(hasattr(self.l,"update"))
    def test_verify_external_copy(self):
        r=self.l.append(ev(),appended_epoch_ns=2000); v=self.l.verify_records((r,)); self.assertTrue(v.valid)
    def test_invalid_external_event(self):
        r=self.l.append(ev(),appended_epoch_ns=2000)
        bad_event=replace(r.event,payload_fingerprint="bad")
        bad=replace(r,event=bad_event)
        self.assertFalse(self.l.verify_records((bad,)).valid)
    def test_empty_snapshot(self):
        s=self.l.export_snapshot(); self.assertEqual(s["record_count"],0); self.assertEqual(s["head_hash"],H0)

def replay_fingerprint():
    l=AuditForensicLedger(policy_version="v2")
    types=list(EventType)
    for i in range(1,1001):
        e=ev(
            i,
            run_id=f"run{i%17}",
            actor_ref=f"agent{i%9}",
            event_type=types[i%len(types)],
            observed_epoch_ns=100000+i,
            payload_fingerprint=hashlib.sha256(f"payload{i%31}".encode()).hexdigest(),
            decision=("ALLOW" if i%3==0 else "HOLD" if i%3==1 else "DENY"),
            claimed_outcome=("SUCCESS" if i%5==0 else None),
            approval_ref=(f"H{i%11}" if i%7==0 else None),
            evidence_refs=(f"ev{i%13}",),
            authority_version=1+(i%3),
            target_version=f"v{i%5}",
            metadata={"x":i%4,"y":i%6},
        )
        l.append(e,appended_epoch_ns=200000+i)
    v=l.verify()
    payload={
        "verification":v.stable_payload(),
        "head":l.head_hash(),
        "runs":[len(l.reconstruct_run(f"run{x}")) for x in range(17)],
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
