# Plan — ZeroGuard trust plane

GitHub: [harishapuri/ZeroGuard](https://github.com/harishapuri/ZeroGuard)

Implementation plan for the **ZeroGuard (2143)** plane as its own product, still fused with CRC and InfraAgent.

1. **ZeroGuard (2143)** — this repo: multi-agent zero-trust IaC posture
2. **CRC (207)** — [infraagent](https://github.com/harishapuri/infraagent)
3. **InfraAgent (1239)** — [CICD_Compliance](https://github.com/harishapuri/CICD_Compliance)

Shared library: [unifiedframework](https://github.com/harishapuri/unifiedframework), vendored at `vendor/unified_framework`.

They share one message bus, one autonomy policy, one hash-chained audit, and **one gate**. This repo does not auto-merge IAM.

**Shipped first:** Checkov IDs → 7 pillars, Ξ, Γ, Ψ, shadow DSA, demo on :8873, `python3 -m zeroguard.automate`.

---

## 1. Why trust must not run alone

| Gap if ZeroGuard is a lone CSPM | What the other papers supply |
| --- | --- |
| Pillars look fine but φ_1h is hot | InfraAgent Ω / DSA ROLLBACK |
| Ψ is high but CRC residual-high | CRC η and residual on the same bus |
| GRA patch vs RPA canary | GRA wins security attributes; RPA owns traffic |

Join rule: **η multiplies Ψ** (and Ω).

```
Ψ  = exp(-λ1 Φ̄) · Ξ · exp(-λ2 δ̄) · exp(-λ3 Γ̄) · η

BLOCK  if φ_1h > 0.7  OR  CRC residual-high  OR  critical IaC
WARN   if φ_6h > 0.5  OR  any ZTA pillar fail  OR  κ > 0.15
PASS   otherwise
```

Shared autonomy default **α2**. GRA/RPA `apply = false`.

---

## 2. Architecture (this repo)

```
Checkov JSON (+ telemetry)
        │
        ▼
 ZeroGuard — pillars, Ξ, Γ, Ψ     ← owned here
        │
        ├─ CRC η (vendor)
        └─ InfraAgent Ω (vendor)
        │
        ▼
 Typed bus · SHA-256 audit · DSA gate
        │
        ▼
 python3 -m zeroguard  |  zeroguard.demo :8873  |  zeroguard.automate
```

### ZeroGuard plane — shipped vs later

Shipped: `framework/zeroguard/pillars.py` — Checkov ID → 7 NIST SP 800-207 pillars, `Ξ`, `Γ`, `Ψ`.

Later: ICA graph, ZTPA attention, IAEA set-cover, GRA template patches + Rego (still never auto-apply by default).

---

## 3. One pipeline run

1. Ingest Checkov JSON + optional telemetry.
2. ZeroGuard publishes `ZtaScore` (`Ψ`, pillars, `Γ`).
3. CRC and InfraAgent still publish on the same bus.
4. DSA classifies. Security suggestions beat rollout suggestions.
5. Append audit. `--focus` keeps trust scores + `decision`.

---

## 4. Demo stories (trust-shaped)

**Success:** clean IaC + healthy telemetry → ALLOW.

**Open door, calm traffic:** broken IaC, calm metrics → BLOCK (the trust story).

**Fail mix:** open SG + public bucket + wildcard IAM + hot traffic → BLOCK.

**Cross-plane:** clean IaC + hot `φ_1h` still ROLLBACK — this CLI must not print a trust-only pass as the whole answer.

Headless: `python3 -m zeroguard.automate`.

---

## 5. File map

| Path | Role |
| --- | --- |
| `zeroguard/cli.py` | Shadow / `--enforce` / `--focus` |
| `zeroguard/demo.py` | SSE demo |
| `zeroguard/automate.py` | Story catalog runner |
| `zeroguard/catalog.py` | Seven stories, expected picks |
| `vendor/unified_framework/framework/zeroguard/` | Pillars, Ξ, Γ, Ψ |

### Known heuristic gap

Given current debt weighting, any Checkov failure can already trip `residual_high` before a pillar-only WARN. Not a correctness bug — recalibrate debt when GRA/XGBoost work lands.

---

## 6. Build order

1. **Done.** Split repo, vendor fusion, shadow gate, `--focus`.
2. **Done.** Demo site :8873, automate, GitHub Actions.
3. Label real IAM / IaC incidents; scorecard before `--enforce`.
4. ICA / ZTPA / IAEA when graph data exists; GRA templates still suggest-only.
5. Ticket/PR comments from GRA templates — still never auto-apply IAM.
