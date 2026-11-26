# Step 31: PDA tracker and regional checklist

## Tracker redesign: 20 November 2026

The page now separates **Checks** and **Progression**. A persistent header shows
the goal, completion/availability totals and reward application counts. Connection,
delivery and scouting feedback have their own footer, so they do not displace the
goal or checklist. The selected tab has a brighter text colour. Both page bodies
share a rectangle but only the active one is shown.

Checks opens with the **Available** filter. Region and status have visible labels
and an instruction: left-click cycles forward, right-click cycles backward,
wrapping at either end. Right-click is handled through the native script window's
`OnMouse` override and absolute cursor/rectangle hit tests. A button-click callback
alone cannot handle it: native `CUIButton` only emits its click event for the left
button. Other mouse input retains the native delegate.

The full-width native list shows four checks per page. Each measured row has a
text status, region and check name; status colours are supplementary. Clicking a
row selects it directly and highlights it. Requirements and the scouted reward's
recipient appear below, beside an explicit **Scout reward** action. Empty filters
explain how to recover and disable scouting; Previous/Next disable at page edges.
The old indirect Select next check button is removed. Selection follows the same
location ID across live updates, and feedback clears when the selection/session
changes. Completed checks do not display the generic encounter-availability caveat.

The XML explicitly sets `can_select="1"`: native `InitScrollView`, also used by
`InitListBox`, defaults that flag to zero. The misleading `ShowSelectedItem` Lua
export aliases ordinary `Show` and does not enable selection. The test model
matches those defaults; direct selection fails without the XML flag.

Progression has one full-width scroll view for counters, forthcoming scouted
rewards, equipment/deliveries, unlocked permissions, lab visits, then locked
permissions. Groups come from the detached tracker projection, not parsing
English text; the legacy flat projection remains available. Hidden ten-entry
pagination is removed.
Highest rank uses the catalogue's named thresholds rather than printing rank
points as a "rank index". All new labels live in the English translation resources.

Native list rows come from `CUIListBox.AddTextItem`, whose C++ factory owns their
lifetime; text-only scroll rows still use XML factories. Never substitute
Lua-constructed userdata in a non-adopting AddWindow call. Cache unchanged rows
and preserve scrolling on data refresh, while filter/page navigation resets its
list. Long names, reasons and rewards remain inside measured scroll viewports.

Primary source probes at Monolith `7289a03` checked `uiscriptwnd_script2.cpp`
(`OnMouse`), `UIButton.cpp`, `UIListBox.cpp`, `UIListBoxItem.cpp` and the associated
Lua exports, plus extracted Anomaly `ui_scenes_dlg.xml` list/font configuration.
The layout model and any exported preview use synthetic data and substitute
fonts; they are **not native rendering evidence**. Owen must verify right-click,
selection/highlight, scrolling, other PDA tabs and aspect ratios in GAMMA Dev.
No APWorld/client, generation, published ID, save or bridge schema changes.

## Scroll-row lifetime correction: 19 November 2026

Owen's opening-tracker crash reaches the native child update through
`gamma_ap_pda.Update`. The checklist rows were Lua-constructed `CUIWindow`
objects, while the scroll view's `AddWindow` binding has no luabind ownership
adoption policy. Its `true` argument enables native auto-deletion on removal;
it does not stop Lua from collecting a constructed object while its pointer
remains in the native tree. The old table-only UI mock retained the object
strongly and did not exercise this boundary.

Create row containers through `CScriptXmlInit.InitStatic`, as the installed MCM
does, then let the scroll view own their native lifetime. This keeps the existing
column coordinates, measured heights, native update delegation and refresh cache.
There are no session, save, protocol, ID or generation changes.

The regression model separates Lua-owned handles from native child pointers and
forces actual Lua garbage collection before native-tree traversal. Opening and
repeated refresh/reopen cases both fail before the correction and pass with it;
the tests do not execute native C++ or establish an in-game result. Complete
verifier and current-head Windows/Linux evidence are recorded with the PR.
Native confirmation remains **not run**, reserved for Owen.

Ownership references at pinned Monolith commit
`7289a03f19a3cc712d9fc4cf6122345984c8c094`:
[constructor, adopting AttachChild and non-adopting AddWindow bindings](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ui/UIWindow_script.cpp),
[XML factories](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ScriptXMLInit.cpp)
and [scroll ownership/update](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ui/UIScrollView.cpp).

## Layout correction: 19 November 2026

The reported concatenated entries were text paragraphs, not a native table.
Ordinary LF characters were passed to X-Ray's complex-text parser, which expects
the two-character `\n` marker. The summary also began inside the native tab band:
the custom tab attaches to the PDA background at y=-34, while the saved profile's
tabs start at y=23 with height 27.

The AP dialog now starts at background-relative y=100. Its summary, filter row,
column headings, two content viewports, page count and bottom actions occupy
separate non-overlapping rectangles. The checklist has independent Status,
Region and Check cells, with reason and reward beneath each row. Native
`AdjustHeightToText` measures every wrapped cell before the following fields
and row are positioned. The summary and progression entries also use independent
measured rows. Scroll-view clipping contains unusually long text instead of
drawing over other controls.

Display text explicitly enables complex mode and converts CR/LF line breaks to
the native marker. Unchanged content does not recreate widgets; data refresh
preserves scroll positions, while filter/page navigation returns its panel to
the beginning. Disabled/unbound views clear old rows, page count and selection.
No check, receipt, scouting or save ownership changes.

Primary source basis: pinned Monolith
[text parsing](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ui/UILines.cpp),
[PDA dialog attachment](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ui/UIPdaWnd.cpp)
and [scroll/text initialization](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/ui/UIXmlInit.cpp),
plus read-only inspection of the active DEV Taskboard XML and MCM/Taskboard
`InitScrollView`, `AddWindow` and text-measurement usage. No base PDA XML is replaced.

Four regressions reproduced the original native-newline mistake and tab
intersection. Automated layout contracts model native XML coordinates and fixed
glyph-width wrapping; they are **not native pixel/font rendering evidence**.
Owen still needs to verify the page at the supported aspect ratios, scroll bars,
long/localized names, other tabs and scouting controls. No game was launched or
installed add-on changed by this source fix. The changes are independent of
the loading-notice fix in PR #51 and do not require a new seed.

## Original tracker implementation

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
- Region/status filters and bounded pages keep long catalogues readable. A separate
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


## Server hints and optional scouting (26 November 2026)

The Hints tab is separate from check scouting. Enter an item name and select
Request item hint to submit the upstream `!hint <item name>` command. Show my
hints submits `!hint`, listing existing hints and points. The AP server owns
fuzzy matching, available hints, costs and payment; the UI never reveals a seed
placement locally or deducts points itself. Its budget shows the latest received
points and the pinned server's cost formula, with stale connection state explicit.
The bounded reply view shows recent room replies including hints, newest first;
it is a 32-message view of transient room news, not a persistent hint database.
Buttons only enqueue bounded data requests. No networking runs in native UI code.

Scouting remains disabled by default in every fresh preset and the APWorld.
Disabled scouting now hides the Scout reward button, selected-check reveal text
and next-milestone previews; stale callbacks cannot request reveals. AP shop
contract previews remain independently available under their existing playability
rules. Existing seed settings are retained, not silently changed.

Native console research found no Lua registration/interception API for arbitrary
player-typed commands in the pinned Monolith baseline. Anomaly's
`on_console_execute` is emitted by `_g.exec_console_cmd` after a script executes
a command, not by the engine's player input path. Do not claim an `!` or `ap_say`
console hook works from mocked callbacks. The user was offered alternatives;
no engine replacement or console interception is included here. Standard AP uses
`!hint` directly in chat; A Hat in Time uses `ap_say !hint` in its supported console.

Source references: [AP commands](https://archipelago.gg/tutorial/Archipelago/commands_en),
[A Hat in Time setup](https://archipelago.gg/tutorial/A%20Hat%20in%20Time/setup_en),
[pinned console dispatch](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrEngine/XR_IOConsole.cpp#L557),
[Lua console bindings](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrGame/console_registrator_script.cpp#L107).

English controls have string-table resources. Mocked layout bounds, request and
reply tests do not establish native edit-box input, focus or visual rendering.
Those checks remain not run, reserved for Owen. The normal installation,
developer panel and current session remain untouched.


## PDA chat composer (26 November 2026)

Owen selected an in-tracker chat box instead of a native-console extension.
The Chat & hints page retains the item-hint shortcuts and adds a message field
with Send and Enter submission. Text is passed unchanged to the existing AP Say
queue: `!hint` and `!hint <item name>` are server commands, while `Hello everyone`
is room chat. No escape prefix is added or removed and no command is executed
locally. Server echoes, other players' chat and command replies appear in the
existing bounded reply pane; the UI does not fabricate a delivery echo.

Empty/whitespace-only messages are refused. A successfully queued message clears
the field; an invalid message or full queue retains the draft and displays the
reason. Hidden/disabled controls cannot submit stale Enter/click events. Drafts
survive tab changes but are transient UI state, not part of a game save. Outbound spacing and punctuation are preserved; incoming room news retains
the existing PDA display sanitization. The existing queue's 512 UTF-8 byte validation and reconnect/acknowledgement behavior
remain authoritative; queued is not proof of server receipt or room-wide display.

The composer uses the same native InitEditBox, Register and EDIT_TEXT_COMMIT
pattern as the pinned Anomaly ui_debug_launcher console input. XML bounds reserve
separate space for replies, instructions and the composer. English labels live in
the existing string table. Native focus, Enter behavior and visual rendering are
not run and remain Owen's acceptance checks. No engine, protocol, catalogue ID,
seed or save-schema changes; the installed game and active session are untouched.


Manual chat submission flushes the bounded data snapshot immediately when a
fresh companion challenge is available. The visible Chat & hints page retries
pending writes at most once per second, including while actor updates are paused.
This performs file I/O only; upstream networking remains in the companion.
A failed write leaves the accepted request queued for retry. Manual flushing
never creates the automatic world-entry request; that still requires the existing
unpaused loading-readiness gate. Native paused-PDA interaction remains unverified.


### Merge review: paused-clock correction

The pinned engine uses a pausable TimerGlobal for `time_global`, while
`time_continual` advances during timer pauses. Tracker refresh and communication
heartbeat expiry now use the continual clock consistently. Otherwise a paused
PDA could stop retrying queued chat and keep a stopped companion's status online.
Two regressions reproduce those failures with a frozen game clock and advancing
UI clock. Automatic world-entry readiness still checks native loading/frame/pause
signals; this clock correction does not release loading-screen announcements.

Primary baseline: [device timers and pause](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrEngine/device.cpp#L642)
and [pausable TimerGlobal definition](https://github.com/themrdemonized/xray-monolith/blob/7289a03f19a3cc712d9fc4cf6122345984c8c094/src/xrEngine/device.h#L107).
Native PDA interaction remains not run, reserved for Owen.
