# Step 36: permission supplies and delivery state

Stacks on workshop/recipe PR #44. APWorld `permission_supplies` is off by default.
When enabled, supported direct permissions carry bounded catalogue-defined extras:
the first three Progressive Tools receipts supply their corresponding physical
toolkit; workshop and recipe permissions supply relevant maintenance, medical,
ammunition or container items; other direct quest/zone permissions carry a bandage.
Repeated copies of an already applied permanent permission add no further extras,
and tools beyond Expert add no further toolkit. Starting-equipment permissions
already grant baseline equipment through their existing recovery plan; stash
rewards retain their existing claim contents. Those systems are not duplicated.

## Application and recovery

The central save owns an optional `deliveries` table keyed by ordered receipt
index. Each record pins its item, copied section list, next action and uncertain
flag. All sections are checked before spawning. Each poll creates at most one
supply object. Successfully completed actions advance the saved cursor. The
permission and receipt complete only after every supply action succeeds, so
the normal received notice waits for completion too.

A definite nil creation result leaves that action pending for retry. An exception
or invalid returned object identity is treated as uncertain: automatic retry is
blocked and an actionable message requests valid-save recovery. This prevents
blind repeated creation after a possible side effect. Acquisition callbacks are
guarded so AP-created supplies cannot produce artefact discovery feedback.
Permission failure after supplies were created retries the permission without
spawning those supplies again. A conflicting pending item history is refused.

Saved plans are bounded plain data, checked against catalogue contents, enabled
items, configuration and applied receipt history. Completed plans cannot be
uncertain or incomplete. Copies are detached from both saved snapshots and the
generated catalogue. Older saves without the optional table migrate to empty;
the save schema and receipt protocol are unchanged. Zero-default configuration
digests are retained. Non-default use requires a fresh seed and coordinated
world/client/add-on upgrade.

Creation and a game save are separate operations. A crash between them is not
crash-proof exactly-once delivery. Ordinary partial save/load resumes the cursor;
an older save restores its own inventory and action state and can replay later
receipts. The add-on cannot establish an external engine transaction.

## PDA state

The tracker reports `Receipt N: X/Y supplies delivered; permission pending`, or
an explicit uncertain/retry-blocked state. Completion removes that pending line.
Received stash coordinates and claimed stash contents have separate counters in
the progression pane. The normal applied-receipt count continues to mean the
receipt's own effect, including coordinates for stash rewards; it does not imply
that a cache has been visited or emptied. Scouting and companion writes never
acknowledge any of these effects.

The supported sections were checked against extracted Anomaly tool, repair,
medical, container and ammunition definitions; active-engine availability is
also checked before mutation. Native acceptance is **not run**, reserved for
Owen: actual quantities, partial failure/retry, native acquisition callbacks,
save/load, older-save rollback, and PDA layout/status. No launch, deployment,
installed-game write or local developer-panel change is included.
