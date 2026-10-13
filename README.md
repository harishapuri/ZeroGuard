# ZeroGuard — trust plane

GitHub: [harishapuri/ZeroGuard](https://github.com/harishapuri/ZeroGuard)

Zero-trust IaC posture (paper 2143). NIST SP 800-207 pillars, Ξ, privilege excess Γ, and Ψ still join CRC η and InfraAgent Ω on the unified bus. One DSA pick. Gate suggestions stay `apply: false`. A separate, opt-in `zeroguard.remediate` command can fix a short allowlist of low-risk Terraform settings; it is a dry run unless you pass `--apply`. This repo never auto-patches IAM, security groups, or network ACLs.

Python module name after clone is `zeroguard`.

```bash
git clone https://github.com/harishapuri/ZeroGuard.git
cd ZeroGuard
```

## Related repos

| Repo | Plane |
| --- | --- |
| [unifiedframework](https://github.com/harishapuri/unifiedframework) | Fused CRC × ZeroGuard × InfraAgent gate (source of `vendor/unified_framework`) |
| [MAWS](https://github.com/harishapuri/MAWS) | Hive orchestrator (named agents, stay-on-blue) |
| [CICD_Compliance](https://github.com/harishapuri/CICD_Compliance) | CRC / CI-CD rules (η) |
| [infraagent](https://github.com/harishapuri/infraagent) | Stay-up / rollout (Ω) |

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

## Opt-in remediation (dry run by default)

`zeroguard.remediate` reads Checkov JSON and fixes only allowlisted, low-risk settings: each one sets a single boolean on one resource type and updates the resource in place.

| Checkov ID | Resource | Setting |
| --- | --- | --- |
| CKV_AWS_7 | `aws_kms_key` | `enable_key_rotation = true` |
| CKV_AWS_27 | `aws_sqs_queue` | `sqs_managed_sse_enabled = true` |
| CKV_AWS_36 | `aws_cloudtrail` | `enable_log_file_validation = true` |
| CKV_AWS_131 | `aws_lb` / `aws_alb` | `drop_invalid_header_fields = true` |
| CKV_AWS_150 | `aws_lb` / `aws_alb` | `enable_deletion_protection = true` |
| CKV_AWS_293 | `aws_db_instance` | `deletion_protection = true` |

Everything else is skipped with a reason. IAM, security groups, and network ACLs are on a deny list that wins even over the allowlist.

```bash
# Dry run: prints the plan and a unified diff, writes nothing
python3 -m zeroguard.remediate examples/remediate/checkov_remediate.json --root examples/remediate

# Write the changes and record the run in the hash-chained audit log
python3 -m zeroguard.remediate checkov.json --root . --apply --audit data/audit.jsonl
```

Other guards: files must resolve inside `--root`, at most 10 fixes per run (`--max-fixes`), multi-line values are left for a human, and a second run is a no-op. Review the diff and open a pull request as usual; this tool edits files, it does not run `terraform apply`. The example Terraform under `examples/remediate/` is illustrative, not a real environment.

## Tests and CI

```bash
python3 -m unittest tests.test_zeroguard tests.test_automate tests.test_remediate -v
```

`.github/workflows/gate.yml` runs unit tests, `python3 -m zeroguard.automate`, a shadow pass fixture, and a remediation dry run (checked to write nothing) on every push and pull request.

## Layout

| Path | Role |
| --- | --- |
| `zeroguard/` | Trust CLI, browser demo, headless automate, opt-in remediation |
| `examples/remediate/` | Illustrative Terraform + Checkov JSON for the remediation dry run |
| `demo/static/` | Autoplay UI (SSE) |
| `vendor/unified_framework/` | Shared pillars, ingest, bus, audit, gate |
| `.github/workflows/gate.yml` | Tests + automate + shadow gate |
