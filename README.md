# ZeroGuard — trust plane

GitHub: [harishapuri/ZeroGuard](https://github.com/harishapuri/ZeroGuard)

Zero-trust IaC posture (paper 2143). NIST SP 800-207 pillars, Ξ, privilege excess Γ, and Ψ still join CRC η and InfraAgent Ω on the unified bus. One DSA pick. GRA would own security attributes later; suggestions stay `apply: false`. This repo does not auto-patch IAM or security groups.

Python module name after clone is `zeroguard`.

```bash
git clone https://github.com/harishapuri/ZeroGuard.git
cd ZeroGuard
```

## Related repos

| Repo | Plane |
| --- | --- |
| [unifiedframework](https://github.com/harishapuri/unifiedframework) | Fused CRC × ZeroGuard × InfraAgent gate (source of `vendor/unified_framework`) |
| [infraagent](https://github.com/harishapuri/infraagent) | CRC / CI-CD rules (η) |
| [CICD_Compliance](https://github.com/harishapuri/CICD_Compliance) | Stay-up / rollout (Ω) |

This repo runs alone via `vendor/unified_framework`. To use a live checkout instead:

```bash
export UNIFIED_FRAMEWORK=/path/to/unifiedframework
```

A sibling folder named `unified_framework` (same parent directory) wins over vendor.

Full figures: [ARCHITECTURE.md](ARCHITECTURE.md). Industry comparison: [INDUSTRY_VS_OURS.md](INDUSTRY_VS_OURS.md). Module plan: [PLAN.md](PLAN.md).

## What this repo owns

- Checkov IDs → seven ZTA pillars
- Ξ (mean pillar score), Γ (IAM excess), Ψ (posture × η)
- Critical IaC / sigma for the fused gate

## Demo and automation

Open-door on calm traffic is the trust story: pillars drop and the fused gate still **stops**.

```bash
python3 -m zeroguard.demo          # http://127.0.0.1:8873/
python3 -m zeroguard.automate      # exit 1 if a pick drifts
```

| Story | Expected pick |
| --- | --- |
| All clear | Go (`ALLOW`) |
| Almost full / errors rising | Wait (`WARN`) |
| Unsafe setup / open door | Stop (`BLOCK_DEPLOYMENT`) |
| Safe setup, bad traffic / site down | Undo (`ROLLBACK`) |

## CLI

```bash
python3 -m zeroguard vendor/unified_framework/examples/checkov_fail.json \
  --telemetry vendor/unified_framework/examples/telemetry_ok.json \
  --focus

python3 -m zeroguard vendor/unified_framework/examples/checkov_pass.json \
  --telemetry vendor/unified_framework/examples/telemetry_ok.json
```

`--enforce` exits `2` on BLOCK. Default is shadow.

## Tests and CI

```bash
python3 -m unittest tests.test_zeroguard tests.test_automate -v
```

`.github/workflows/gate.yml` runs unit tests, `python3 -m zeroguard.automate`, and a shadow pass fixture on every push and pull request.

## Layout

| Path | Role |
| --- | --- |
| `zeroguard/` | Trust CLI, browser demo, headless automate |
| `demo/static/` | Autoplay UI (SSE) |
| `vendor/unified_framework/` | Shared pillars, ingest, bus, audit, gate |
| `.github/workflows/gate.yml` | Tests + automate + shadow gate |
