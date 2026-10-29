"""Audited old timeouts must not exempt later or modified outcomes."""

import hashlib
import json

import pytest
from eval.pr_replay import reconciled_rows, tripwire_reasons


def outcome():
    return {"task_id": "old", "outcome": "timeout", "cost_lower_bound": "True", "cost_usd": "0.0231", "wall_s": "100"}


def audit(row):
    return {
        row["task_id"]: {
            "reconciled": True,
            "exact_cost_usd": 0.02313272,
            "row_sha256": hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }
    }


def test_audited_old_timeout_keeps_failure_and_original_evidence():
    row = outcome()
    checked = reconciled_rows([row], audit(row))
    assert row["cost_lower_bound"] == "True"
    assert checked[0]["outcome"] == "timeout"
    assert tripwire_reasons(checked, 0.0231, 0.068, 620) == []


def test_new_timeout_still_stops_after_old_timeout_is_reconciled():
    row = outcome()
    new = {**row, "task_id": "new"}
    checked = reconciled_rows([row, new], audit(row))
    assert tripwire_reasons(checked, 0.0462, 0.068, 620) == ["timeout cost is a lower bound; reconcile before further paid work"]


def test_modified_outcome_or_billing_mismatch_is_rejected_before_resume():
    row = outcome()
    with pytest.raises(ValueError, match="outcome changed"):
        reconciled_rows([{**row, "wall_s": "101"}], audit(row))
    record = audit(row)
    record["old"]["exact_cost_usd"] = 0.1
    with pytest.raises(ValueError, match="does not match recorded cost"):
        reconciled_rows([row], record)
    with pytest.raises(ValueError, match="absent"):
        reconciled_rows([], audit(row))
