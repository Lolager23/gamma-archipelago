# Step 31: PDA tracker and regional checklist

Stack base: PDA localization PR #38. `pda_tracker` is an APWorld toggle, enabled
by default. The AP tab stays registered for UI compatibility; disabled seeds show
a disabled page. The tab uses owned XML plus DXML injection, never a replacement
for the profile's complete PDA XML. Existing buttons retain their identifiers and
delegates, with their row proportionally resized to reserve 36 pixels for AP.

The sole game-state owner exposes a detached read-only view. No tracker action
creates items, marks checks, changes a save or accesses the network. The UI refreshes
at most once per second while active and also has a manual refresh button.

- Completed: saved observation or confirmed server check.
- Available: documented access/equipment/quest requirements are currently met.
- Blocked: missing zone access, connected route, usable psi protection, equipment
  or quest permissions. Global activities retain conservative world restrictions.
- Region/status filters and six-row pages keep long catalogues bounded. A separate
  paginated panel shows the selected goal, important permissions, lab visits,
  cumulative kills, side tasks and rank. Disabled check categories do not hide goal
  observation. Random NPC/encounter availability is never implied.
- Delivery shows known receipts, applied count, pending count and the adapter's
  latest error. It does not infer server connectivity from an old snapshot or
  treat received stash coordinates as proof of a physical claim. Scouted rewards,
  server connection details and richer delivery status arrive in later increments.

Display metadata is generated from the authoritative catalogue. Availability walks
the same undirected level graph, with live permission facts rather than an assumed
future helmet claim. This conservative UI is not an authoritative solver or proof
that an NPC/quest can be completed in the current ALife simulation.

## Compatibility and source probes

Missing `pda_tracker` in old configuration snapshots defaults to enabled. The
default is omitted from the digest, preserving old seed/config identities. Off
is digest-bound. No published item/location ID or save schema changes. New
companion configuration fields require the matching add-on; upgrade the bundle
together. Old clients continue working with the new add-on at the legacy default.

Read-only installed-source probes confirmed the engine's `pda.set_active_subdialog`
extension returns a `CUIScriptWnd`, `CScriptXmlInit` text/button construction,
`CUIScriptWnd.Update`, and the DXML query/get/set/insert APIs. The saved DEV profile
uses PDA Taskboard's eight-button `pda_16.xml`; the additive wrapper delegates all
non-AP sections and supports other wrappers in either installation order.
These are source probes, not native runtime verification.

## Verification and acceptance

Automated regressions cover disabled/unbound/refused saves, snapshot detachment,
receipt counts, legacy configuration, catalogue parity, connected routes in both
directions, psi/equipment/quest/combat requirements, filters, page bounds, tab
delegate preservation, idempotent XML insertion and update throttling. The full
verifier and current-head Windows/Linux CI are required before delivery.

The full local verifier passed: 789 covered Python/Lua tests, 32 untraced
generator/server tests and five Node tests (826 total). Every owned Python runtime
module measured 100% lines/branches; all measured Lua executable lines were covered.
Lua branch coverage is not measured. The preset files include the new option and
the six-preset, 6,000-seed matrix remains required. Reports/checksums are retained
outside Git and by CI. Native acceptance below remains separate.
The Lua collector walks nested class tables with cycle/depth bounds; a regression
proves that an unexecuted UI method contributes missing executable lines.

Native verification is **not run**, reserved for Owen: confirm AP and existing tabs
at supported aspect ratios, text wrapping and all page controls, real progression
changes, no-PDA restoration, save/reload and a failed/pending reward. Confirm other
tabs after repeated loads and with the active Taskboard/DART stack. No deployment,
game launch or installed developer-panel change is part of this increment.
