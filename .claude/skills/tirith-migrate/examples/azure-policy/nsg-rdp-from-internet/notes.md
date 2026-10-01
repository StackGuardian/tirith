# RDP access from the Internet should be blocked: approximate, stricter

The definition (deprecated upstream, but the shape is the one every NSG policy has) fires when a
`securityRules` resource has `access Allow` **and** `direction Inbound` **and** a destination port
covering 3389 **and** a source that is the Internet, all on the same rule. The port test includes
ARM expressions splitting `3000-4000` ranges and a `count`/`where` over `destinationPortRanges[*]`.

Tirith evaluators are per resource and `eval_expression` combines whole-plan verdicts, so four
tests cannot be bound to one rule (issue #316), and port-range arithmetic is not expressible
(issue #338). The translation keeps the test that carries the intent: no rule's source is the
Internet. Stricter: a rule opening 443 to the world is refused, where Azure passes it.

| Plan | Azure | Tirith |
| --- | --- | --- |
| `should-fail.json` (RDP from Internet) | audit | exit 3 |
| `should-pass.json` (RDP and HTTPS from the VPC only) | pass | exit 0 |
| `diverges.json` (HTTPS from Internet, RDP internal) | **pass** | **exit 3** |

If the team accepts "no inbound rule from the Internet at all" as the house rule, say so in the
report and this becomes the policy. If they need the port-specific version, it waits on #316.
