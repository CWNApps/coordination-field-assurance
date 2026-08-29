from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cwn_coordination_assurance.stack_test0 import REQUIRED_RUNTIME_LABELS, evaluate_cwn_stack_agent_test0


NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


def passing_evidence() -> dict:
    return {
        "schema_version": "1.0.0",
        "collected_at": "2026-08-28T11:30:00Z",
        "environment": "synthetic-shadow",
        "evidence_mode": "read_only_shadow",
        "graph": {
            "migration_log_reconciled": True,
            "label_counts": {name: 1 for name in REQUIRED_RUNTIME_LABELS},
        },
        "agents": {
            "unique_agent_ids": True,
            "run_principal_bindings_complete": True,
            "tenant_bindings_complete": True,
            "signed_event_coverage": 1.0,
            "event_sequence_coverage": 1.0,
        },
        "authorization": {
            "unsigned_permits_rejected": True,
            "advisory_cannot_overwrite_hard_facts": True,
            "research_plane_has_authority": False,
        },
        "receipts": {
            "signature_verification_coverage": 1.0,
            "replay_protection_enabled": True,
            "policy_epoch_bound": True,
        },
        "privacy": {"restricted_payloads_excluded": True},
    }


class CWNStackAgentTest0(unittest.TestCase):
    def test_00_supplied_snapshot_is_not_a_live_pass(self) -> None:
        evidence = json.loads((ROOT / "evals" / "cwn_stack_agent_test0_snapshot.json").read_text(encoding="utf-8"))
        result = evaluate_cwn_stack_agent_test0(evidence, now=NOW)
        self.assertEqual(result.state, "UNKNOWN")
        self.assertNotEqual(result.state, "PASS")

    def test_01_complete_shadow_evidence_passes(self) -> None:
        result = evaluate_cwn_stack_agent_test0(passing_evidence(), now=NOW)
        self.assertEqual(result.state, "PASS")
        self.assertTrue(all(g.state == "PASS" for g in result.gates))

    def test_02_unsigned_permit_is_a_hard_failure(self) -> None:
        evidence = passing_evidence()
        evidence["authorization"]["unsigned_permits_rejected"] = False
        self.assertEqual(evaluate_cwn_stack_agent_test0(evidence, now=NOW).state, "FAIL")

    def test_03_advisory_authority_is_a_hard_failure(self) -> None:
        evidence = passing_evidence()
        evidence["authorization"]["research_plane_has_authority"] = True
        self.assertEqual(evaluate_cwn_stack_agent_test0(evidence, now=NOW).state, "FAIL")

    def test_04_missing_runtime_writer_remains_unknown(self) -> None:
        evidence = passing_evidence()
        evidence["graph"]["label_counts"]["ReceiptStream"] = 0
        self.assertEqual(evaluate_cwn_stack_agent_test0(evidence, now=NOW).state, "UNKNOWN")

    def test_05_low_signed_event_coverage_fails(self) -> None:
        evidence = passing_evidence()
        evidence["agents"]["signed_event_coverage"] = 0.98
        self.assertEqual(evaluate_cwn_stack_agent_test0(evidence, now=NOW).state, "FAIL")

    def test_06_stale_snapshot_cannot_pass(self) -> None:
        evidence = passing_evidence()
        evidence["collected_at"] = "2026-08-02T00:00:00Z"
        self.assertEqual(evaluate_cwn_stack_agent_test0(evidence, now=NOW).state, "UNKNOWN")
