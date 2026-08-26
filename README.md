# ZeroGuard — trust plane

Zero-trust IaC posture (paper 2143) as its **own repo**. NIST SP 800-207 pillars, Ξ, privilege excess Γ, and Ψ still join CRC η and InfraAgent Ω on the **unified framework** bus. One DSA pick. GRA would own security attributes later; suggestions stay `apply: false`.

Sibling products: [`CICD`](../CICD) (rules) and [`infra`](../infra) (stay-up). Shared library: [`unified_framework`](../unified_framework). Snapshot: `vendor/unified_framework`.

## What this repo owns

- Checkov IDs → seven ZTA pillars
- Ξ (mean pillar score), Γ (IAM excess), Ψ (posture × η)
- Critical IaC / sigma for the fused gate

It does not auto-patch IAM or security groups.

## Demo and automation

```bash
cd zeroguard
python3 -m zeroguard.demo          # http://127.0.0.1:8873/
python3 -m zeroguard.automate      # all 7 stories, exit 1 if a pick drifts
```

Open-door on calm traffic is the trust story: pillars drop and the fused gate still **stops**.

## Run

```bash
cd zeroguard
python3 -m zeroguard vendor/unified_framework/examples/checkov_fail.json \
  --telemetry vendor/unified_framework/examples/telemetry_ok.json \
  --focus

python3 -m zeroguard vendor/unified_framework/examples/checkov_pass.json \
  --telemetry vendor/unified_framework/examples/telemetry_ok.json
```

`--enforce` exits `2` on BLOCK. Default is shadow.

```bash
export UNIFIED_FRAMEWORK=/path/to/unified_framework
```

A sibling `../unified_framework` wins over vendor.

## Tests

```bash
python3 -m unittest tests.test_zeroguard tests.test_automate -v
```

## Layout

| Path | Role |
| --- | --- |
| `zeroguard/` | Trust CLI, browser demo, headless automate |
| `demo/static/` | Autoplay UI (SSE) |
| `vendor/unified_framework/` | Shared pillars, ingest, bus, audit, gate |
| `.github/workflows/gate.yml` | Tests + automate + shadow gate |
