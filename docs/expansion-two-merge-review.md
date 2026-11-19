# Second expansion: source review and merge validation

On 19 November 2026 Owen explicitly authorized validating, fixing and merging
the open PRs. This supersedes the earlier instruction to leave the expansion
stack as drafts. Native game acceptance remains reserved for Owen. Public release
and independent human release review remain separate, uncompleted gates.

The review proceeds from the HTTP fixture and PDA localization through the
compatibility audit and Steps 31–40. Prerequisites are integrated with merge
commits; published history is preserved. PRs are retargeted to main only in
dependency order. The linked PRs are authoritative for merge states and merge
commits; the final hardening PR contains this review record itself.

| PR | Reviewed increment | Review result |
|---|---|---|
| [#37](https://github.com/Lolager23/gamma-archipelago/pull/37) | Windows HTTP fixture | Invalid requests retain status/error-reason assertions; production validation is unchanged |
| [#38](https://github.com/Lolager23/gamma-archipelago/pull/38) | PDA grammar/localization | Semantic fields, sanitization, translation fallback, opaque labels, foreign IDs and saved notice identities reviewed |
| [#39](https://github.com/Lolager23/gamma-archipelago/pull/39) | Compatibility investigation | Findings distinguish static syntax, disabled providers and unverified runtime winners; no vendor repair is included |
| [#40](https://github.com/Lolager23/gamma-archipelago/pull/40) | PDA tracker | Additive DXML/delegation, detached views, pagination, refresh, blocked reasons and nested-class coverage reviewed |
| [#41](https://github.com/Lolager23/gamma-archipelago/pull/41) | Scouting/services | Bounds, session/configuration/heartbeat binding, spoiler controls, finite callbacks and no-receipt scouting reviewed |
| [#42](https://github.com/Lolager23/gamma-archipelago/pull/42) | Discovery quotas | Fixed saved discoveries outside the configured roster; regression and migration evidence below |
| [#43](https://github.com/Lolager23/gamma-archipelago/pull/43) | Progressive Tools | Receipt-derived capped tiers, supported guards and matching pool/solver/PDA requirements reviewed |
| [#44](https://github.com/Lolager23/gamma-archipelago/pull/44) | Workshop/recipes | Independent permissions, native tool groups and continued knowledge/material requirements reviewed |
| [#45](https://github.com/Lolager23/gamma-archipelago/pull/45) | Permission supplies | Cursor recovery, uncertainty refusal, delayed permissions, callback feedback and conflict validation reviewed |
| [#46](https://github.com/Lolager23/gamma-archipelago/pull/46) | Supply packages | Contents/calibres, useful weights, repeatable receipts and partial-plan recovery reviewed |
| [#47](https://github.com/Lolager23/gamma-archipelago/pull/47) | Carry rewards | Active keyed API, additive cap, idempotent retries, rollback and preservation of other modifiers reviewed |
| [#48](https://github.com/Lolager23/gamma-archipelago/pull/48) | Generation/pacing | Fixed opening/route placement constraints; budgets, starting inventory, identity and spoiler reports reviewed |
| [#49](https://github.com/Lolager23/gamma-archipelago/pull/49) | Combined hardening | Combined real generation/server tests, mocked recovery and this documentation reconciliation |

## Corrections and compatibility

Discovery save validation previously accepted a known source ID even when that
type was excluded or its category was disabled. Two regressions reproduced
acceptance; such observations could inflate a later distinct quota. Validation
now requires a well-shaped configuration and an enabled, non-excluded source
before loading observations. Empty older discovery state still migrates. Corrupt
observations are refused rather than silently repaired or acknowledged.

Optional opening Medkits/Bandages previously used locked placement without
checking non-local settings or the location's item rule. Three regressions
reproduced that bypass. The reservation now finds a permitted placement, tries
the fallback supply or skips the optional reservation. Required opening
permissions retain explicit conflict/self-lock refusal. Another 150 filled seeds
cover precollected Radar/X16/X19 keys with psi progression.

Remaining zone-route keys also bypassed explicit non-local settings through their
forced local placements. A regression reproduced the conflict. Generation now
refuses that configuration before placing route keys; a companion positive case
confirms already-precollected keys need no placement and remain supported.

Both corrections preserve published IDs, receipt order and save schemas. The
delivery prerequisite conflict was resolved by retaining both roster-aware
discovery validation and delivery-plan validation. No coverage gates, exclusions
or checks were disabled. Source review here is not independent human release
approval or evidence of native gameplay compatibility.

## Evidence and merge gates

Each reviewed head runs the complete verifier using a separate tooling runtime:
lint, formatting, typing, Python/Lua regressions and coverage, Node tests,
catalogue/resource parity, reproducible packages, APWorld loading and actual
generation/server sessions. Original implementation counts remain historical;
the PR bodies record review-run results for their exact heads.

Windows and Linux CI must pass for the current head before merge. The prospective
main merge tree must equal that tested head's source tree. A retarget alone does
not substitute for validating changed source. The merge request pins the reviewed
head SHA and the observed result is checked afterward. No failing check is bypassed
and no synthetic approval is submitted.

Private evidence lives under `D:/GAMMAAPTools/merge-review-two/pr-<number>`:
review notes, verifier logs/coverage/matrix/checksums, tested-tree records,
current-head CI metadata, verified downloaded Windows/Linux packages and observed
merge results. Runtime artifacts and installation inventories remain outside Git.
GitHub PR links retain published source and merge history.

No game launch/load, deployment, save/profile change, running user AP session
change or local developer-panel change is part of this merge pass. The original
checkout and protected normal installations remain untouched. Continue with
[Owen's native matrix](expansion-two-acceptance.md), measured playtime calibration,
compatibility fixes from those runs and the existing release gates.
