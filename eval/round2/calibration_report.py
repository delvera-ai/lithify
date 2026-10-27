"""Compare the single calibration with frozen round-1 baseline task 1."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    reference = json.loads((root / "eval/round2/ROUND1_SESSION_AUDIT.json").read_text())
    reference = next(r for r in reference if "baseline" in r["arm"] and "/01-" in r["trajectory"])
    assert len(reference["evidence"]) == 1
    old = reference["evidence"][0]
    results = list(a.out.glob("results*.csv"))
    assert len(results) == 1
    with results[0].open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1 and rows[0]["task"] == "sqlglot#7492"
    row = rows[0]
    metadata = list(a.out.glob("raw/*/01-pr7492/run/sessions/*-execute.json"))
    assert len(metadata) == 1
    billing = json.loads(metadata[0].read_text())
    by_session: dict[str, float] = {}
    for result in billing["results"]:
        sid = result.get("session_id", "")
        by_session[sid] = max(by_session.get(sid, 0.0), float(result.get("total_cost_usd", 0) or 0))
    calibration_cost = sum(by_session.values())
    calls = []
    for label, source in (("round1", old["calls"]), ("calibration", billing["calls"])):
        for index, call in enumerate(source, 1):
            calls.append(
                {
                    "run": label,
                    "call": index,
                    "model": call["model"],
                    "context_tokens": call["context_tokens"],
                    **{
                        k: call["usage"].get(k, 0)
                        for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
                    },
                }
            )
    with (a.out / "per-call-context.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(calls[0]))
        writer.writeheader()
        writer.writerows(calls)
    summary = {
        "round1": {
            "versions": old["versions"],
            "cost_states": old["cost_states"],
            "calls": len(old["calls"]),
            "context_sizes": [c["context_tokens"] for c in old["calls"]],
        },
        "calibration": {"row": row, "billing": billing, "context_sizes": [c["context_tokens"] for c in billing["calls"]]},
        "calibration_cost_unrounded": calibration_cost,
        "recorded_cost_ratio": calibration_cost / 0.0294,
        "exceeds_three_times_round1": calibration_cost > 3 * 0.0294,
    }
    (a.out / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cost": row["cost_usd"],
                "ratio": summary["recorded_cost_ratio"],
                "stop": summary["exceeds_three_times_round1"],
                "models": billing["model_usage"],
                "calls": len(billing["calls"]),
                "turns": billing["num_turns"],
                "result_events": billing["result_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
