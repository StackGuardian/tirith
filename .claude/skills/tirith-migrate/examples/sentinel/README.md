# Sentinel migrations

Five translations, one per fidelity story. Each directory holds `source.sentinel`, `notes.md`,
and where a translation exists, `policy.json` with `should-fail.json` and `should-pass.json`.
Approximate translations add `diverges.json`, a plan where Sentinel and Tirith disagree.

```bash
cd restrict-instance-type
tirith -policy-path policy.json -input-path should-fail.json --fail-on-error -var-path variables.json; echo $?   # 3
tirith -policy-path policy.json -input-path should-pass.json --fail-on-error -var-path variables.json; echo $?   # 0
```

The Sentinel sources are short originals written in the idioms of `hashicorp/terraform-sentinel-policies`.
