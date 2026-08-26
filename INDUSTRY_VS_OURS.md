# Industry deploy vs our trust gate

GitHub: [harishapuri/ZeroGuard](https://github.com/harishapuri/ZeroGuard)

**Northstar Bank** still ships a chatbot with **blue** and **green**. This repo is the **trust** plane: open doors, extra permissions, unusual grants?

Today IAM review is a later ticket. We still produce **one** go / wait / stop **before** anyone leaves blue. ZeroGuard Ψ is fused with CRC η and InfraAgent Ω. An open security group on calm traffic still **stops**.

Complete figures: [ARCHITECTURE.md](ARCHITECTURE.md). Plan: [PLAN.md](PLAN.md). Fused library: [unifiedframework](https://github.com/harishapuri/unifiedframework).

---

## Typical bank identity path today

1. CI is green. Checkov findings are advisory or a separate security ticket.
2. Wildcard chatbot roles wait for a weekly IAM review.
3. Platform flips traffic. Customers move first.
4. Public buckets and `0.0.0.0/0` show up in a cloud-posture dashboard after the fact.

No fused trust decision **before** customers leave the old assistant.

---

## Our trust deploy

1. Same two copies. Blue stays live until the fused gate says go.
2. One Checkov JSON enters this CLI (`python3 -m zeroguard`). Telemetry is optional but still scored.
3. This plane answers: **open doors or extra permissions?** Seven NIST SP 800-207 pillars, Ξ, Γ, Ψ.
4. The same run still scores CRC and stay-up. Hot traffic still **Undo** even if pillars look fine.
5. One decision: go / wait / stop. A security suggestion beats a rollout suggestion. IAM patches stay `apply: false`.
6. Sign the log. Shadow by default. `--enforce` only after a scorecard on real releases.

Demo: http://127.0.0.1:8873/ (`python3 -m zeroguard.demo`).

---

## Where we are better (trust plane)

| Area | Typical deploy | Ours | Why it helps a bank |
| --- | --- | --- | --- |
| Identity | IAM review is a later ticket | Extra permissions scored in the same run | Wildcard chatbot roles show up before live customers |
| Open doors | Cloud posture after the flip | Pillars + critical IaC **Stop** | `0.0.0.0/0` and public buckets block the switch |
| Conflict | Security ticket vs platform canary | GRA wins security attrs; RPA owns traffic | One orchestrator, not two owners arguing in Slack |
| Auto-fix | “just open the PR” | Suggest only | Chatbot IAM is never rewritten by the gate |
| Evidence | CSPM in one tab | Signed hash chain + fused pick | Examiner can replay why customers stayed on blue |
| Cross-plane | Trust pass, site still dies | Calm traffic + hot φ still **Undo** | Trust-only dashboards miss stay-up |

---

## Benefits you can claim

The claim is not “we replaced a CSPM.” Banks already scan IAM. This plane is the **trust join**: NIST pillars and privilege excess share a gate with CRC and stay-up.

- Wildcard roles and open SGs are in the **same** pick as capacity.
- Real Checkov IDs map onto P1–P7. No auto-patch.
- Shadow first. `--enforce` only after outcomes match the log.

---

## What we do not claim

| Still later | Why we left it |
| --- | --- |
| ICA graph / ZTPA attention | Checkov ID → pillar map is the shipped sensor |
| IAEA set-cover / GRA + Rego apply | Templates later; `apply = false` now |
| Paper F1 / MTTD numbers | Those belong to the published ZeroGuard system, not this CLI |

Industry already has IAM reviews. The edge is the **join with rules and stay-up**, not a new identity product.

---

## Short paragraph you can reuse

Banks already review IAM, but that review is usually a later ticket. A chatbot release can look green in CI and still open a network door or grant extra permissions. This repo is the ZeroGuard plane of one orchestrator: NIST zero-trust pillars and privilege excess are scored with CRC η and InfraAgent Ω. The only customer-facing output is go, wait, or stop. Suggested remediations are never applied automatically. The old system stays live until the output is go. Every pick is hash-chained and later scored against what actually happened.
