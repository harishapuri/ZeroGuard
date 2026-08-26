# ZeroGuard — trust plane

Zero-trust IaC posture (paper 2143) as its **own repo**. NIST SP 800-207 pillars, Ξ, privilege excess Γ, and Ψ still join CRC η and InfraAgent Ω on the **unified framework** bus. One DSA pick. GRA would own security attributes later; suggestions stay `apply: false`.

Sibling products: [`CICD`](../CICD) (rules) and [`infra`](../infra) (stay-up). Shared library: [`unified_framework`](../unified_framework). Snapshot: `vendor/unified_framework`.

## What this repo owns

- Checkov IDs → seven ZTA pillars
- Ξ (mean pillar score), Γ (IAM excess), Ψ (posture × η)
- Critical IaC / sigma for the fused gate

It does not auto-patch IAM or security groups.

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
python3 -m unittest tests.test_zeroguard -v
```

## Layout

| Path | Role |
| --- | --- |
| `zeroguard/` | Trust CLI wrapping the unified orchestrator |
| `vendor/unified_framework/` | Shared pillars, ingest, bus, audit, gate |
| `.github/workflows/gate.yml` | Shadow gate on push |
