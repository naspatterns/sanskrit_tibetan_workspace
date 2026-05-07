"""Phase 5 — D1 + Edge API integrity audit.

Verifies that the deployed Workers API at stw-api.naspatterns.workers.dev
correctly fronts the D1 database, by:
  1. Probing /api/health (liveness)
  2. Querying canonical terms (dharma, agni) — should return entries
  3. Querying Sentinel 215's previously-failing long-tail (vajracchedikā,
     śūraṅgama) — should now succeed via prefix match
  4. Measuring p50/p95 latency
  5. Testing 404 path (non-existent norm)

Output: data/reports/audit-2026-04-30/audit-D-d1-integrity.md

Usage:
    uv run python -m scripts.audit_d1_integrity
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reports" / "audit-2026-04-30" / "audit-D-d1-integrity.md"
API_ORIGIN = "https://stw-api.naspatterns.workers.dev"

PROBES = [
    # (name, expected_count_min, query)
    ("dharma (canonical, in tier0)",         5,  "dharma"),
    ("agni (canonical)",                     5,  "agni"),
    ("vajracchedika (Sentinel ❌ → ✅)",      1,  "vajracchedika"),
    ("surangama (Sentinel ❌ → ✅)",          1,  "surangama"),
    ("prajna",                              5,  "prajna"),
    ("buddha",                              5,  "buddha"),
    ("bodhisattva",                         5,  "bodhisattva"),
    ("rabidlydoesntexistaaa",               0,  "rabidlydoesntexistaaa"),  # 404 path
]


def fetch_json(url: str, timeout: float = 10.0) -> tuple[dict | None, float]:
    """Return (parsed JSON, elapsed-ms). On error returns (None, ms).

    Cloudflare flags Python's default `Python-urllib/x.y` User-Agent as bot
    traffic (HTTP 403). Send a realistic browser-like UA so the audit can
    actually reach the deployed API.
    """
    t0 = time.perf_counter()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (audit_d1_integrity.py) "
                "stw-workspace v2 Phase 5 audit"
            ),
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = (time.perf_counter() - t0) * 1000
            return data, elapsed
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return {"error": str(e)}, elapsed


def main() -> int:
    lines: list[str] = []
    lines.append("# audit-D-d1-integrity — Phase 5 D1 + Edge API verification")
    lines.append("")
    lines.append(f"- API origin: `{API_ORIGIN}`")
    lines.append(f"- Method: HTTP GET via urllib")
    lines.append("")

    # Health probe
    print("Probing /api/health…", file=sys.stderr)
    health, hms = fetch_json(f"{API_ORIGIN}/api/health")
    health_ok = bool(health and health.get("ok"))
    lines.append(f"- **Health**: {'✅' if health_ok else '❌'} "
                 f"(`/api/health` returned in {hms:.0f}ms)")
    lines.append("")

    # Search probes
    lines.append("## Search probes")
    lines.append("")
    lines.append("| # | Name | Query | Expected ≥ | Got | Latency | Verdict |")
    lines.append("|---|---|---|---:|---:|---:|---|")

    latencies: list[float] = []
    failures: list[tuple[str, str]] = []
    for i, (name, expect, q) in enumerate(PROBES, start=1):
        url = f"{API_ORIGIN}/api/search/{urllib.parse.quote(q)}?limit=10"
        data, ms = fetch_json(url)
        latencies.append(ms)
        count = (data or {}).get("count", 0) if isinstance(data, dict) else 0
        if expect == 0:
            verdict = "✅" if count == 0 else "⚠️"
        else:
            verdict = "✅" if count >= expect else "❌"
        if verdict == "❌":
            failures.append((name, str(data)))
        lines.append(
            f"| {i} | {name} | `{q}` | {expect} | {count} | {ms:.0f}ms | {verdict} |"
        )
        print(f"  [{verdict}] {name}: count={count}, {ms:.0f}ms",
              file=sys.stderr)

    lines.append("")
    lines.append("## Latency stats")
    lines.append("")
    if latencies:
        lines.append(f"- p50: {statistics.median(latencies):.0f}ms")
        lines.append(f"- p95: {statistics.quantiles(latencies, n=20)[-1]:.0f}ms"
                     if len(latencies) >= 20 else
                     f"- max: {max(latencies):.0f}ms")
        lines.append(f"- mean: {statistics.fmean(latencies):.0f}ms")
        lines.append(f"- N: {len(latencies)}")
    lines.append("")

    if failures:
        lines.append("## ❌ Failures")
        lines.append("")
        for name, raw in failures:
            lines.append(f"- **{name}**: `{raw[:200]}…`")
        lines.append("")

    summary = (f"\n총합: {len(PROBES) - len(failures)}/{len(PROBES)} ✅ · "
               f"latency mean {statistics.fmean(latencies):.0f}ms")
    print(summary, file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n✓ Wrote {OUT.relative_to(ROOT)}", file=sys.stderr)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
