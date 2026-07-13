import argparse
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


def percentile(values: list[int], quantile: float) -> int:
    if not values:
        return 0
    ordered = sorted(max(0, int(value)) for value in values)
    index = max(0, math.ceil(len(ordered) * quantile) - 1)
    return ordered[index]


def build_report(database_path: Path) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    connection = sqlite3.connect(database_path)
    try:
        rows = connection.execute(
            "SELECT agent_type, duration_ms, execution_metadata FROM agent_run_steps ORDER BY id"
        ).fetchall()
    finally:
        connection.close()

    for agent_type, duration_ms, raw_metadata in rows:
        try:
            metadata = json.loads(raw_metadata or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        provider = str(metadata.get("provider") or "")
        is_llm_attempt = (
            metadata.get("execution_mode") == "llm"
            or bool(metadata.get("fallback_used"))
            or provider not in {"", "rule_based"}
        )
        if not is_llm_attempt:
            continue
        groups[str(agent_type)].append(
            {
                "duration_ms": max(0, int(duration_ms or metadata.get("duration_ms") or 0)),
                "provider_duration_ms": max(0, int(metadata.get("provider_duration_ms") or 0)),
                "retry_count": max(0, int(metadata.get("retry_count") or 0)),
                "token_usage": metadata.get("token_usage") if isinstance(metadata.get("token_usage"), dict) else {},
                "fallback_used": bool(metadata.get("fallback_used")),
                "fallback_reason": str(metadata.get("fallback_reason") or ""),
            }
        )

    agents: dict[str, Any] = {}
    for agent_type, samples in sorted(groups.items()):
        durations = [sample["duration_ms"] for sample in samples]
        provider_durations = [sample["provider_duration_ms"] for sample in samples if sample["provider_duration_ms"]]
        fallback_reasons = sorted({sample["fallback_reason"] for sample in samples if sample["fallback_reason"]})
        agents[agent_type] = {
            "sample_count": len(samples),
            "duration_ms": {"p50": percentile(durations, 0.50), "p95": percentile(durations, 0.95)},
            "provider_duration_ms": {
                "p50": percentile(provider_durations, 0.50),
                "p95": percentile(provider_durations, 0.95),
            },
            "retry_count": sum(sample["retry_count"] for sample in samples),
            "total_tokens": sum(int(sample["token_usage"].get("total_tokens") or 0) for sample in samples),
            "fallback_count": sum(1 for sample in samples if sample["fallback_used"]),
            "fallback_reasons": fallback_reasons,
        }
    return {"database": str(database_path), "agents": agents}


def main() -> None:
    parser = argparse.ArgumentParser(description="Report safe LLM p50/p95 runtime evidence from Agent traces.")
    parser.add_argument("database", type=Path, help="Path to the SQLite database file.")
    args = parser.parse_args()
    print(json.dumps(build_report(args.database), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
