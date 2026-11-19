# Step 29: compatibility and release hardening

Stack base: #32. Numeric IDs now require actual Python integers. A known ID
written as a float no longer passes through set equality into manifests, history
or confirmed checks. Snapshot receipt counts and goal booleans are checked before
session mutation. Canonical string parsing and seed/slot binding remain strict.
Protocol/session line and branch coverage remain 100%.

Equipment manifests advertise only the groups selected for AP locks. The client
also recognizes the exact older schema-3 category-wide equipment projection,
then binds only the selected permissions. It never enables an unselected group
because an old manifest listed it. Existing published IDs are retained.

## Save compatibility

Owned AP snapshots now carry additive save schema 1; earlier snapshots without
the field remain supported. Loading validates bounded plain data, identity,
receipt prefix, completed-check IDs, known permissions and approved stash plans.
Malformed nested structures are also caught at the owned copy boundary. Refusal
persists as a refused save marker: it cannot silently clear receipts and bind to
another seed. Restore a valid full backup or start a fresh character. This does
not repair arbitrary native game-save corruption or validate third-party state.

Confirmed stash/baseline creation markers can finish their pending action without
recreating the object. Unknown creation side effects still block automatic retry.
There remains no engine transaction between creation and saving. Older-save
rollback can replay consumables; keep the documented timeline/backup policy.
Forward migration supports legacy pilot slots 1/2 and expanded slot 3, plus the
optional travel-field default migration. Downgrading an expanded save to an older
add-on is unsupported: restore the matching old seed/client/add-on/save bundle.

## Tooling and packages

All checkout CLI tools prioritize their own `src` before an unrelated editable
installation. Bootstrap copies the shared core into the separate AP runtime and
rejects destinations within either normal or development game/MO2 roots. A
deterministic companion ZIP carries that core and a runtime-local launcher.
The isolated archive-loading test uses the distributed APWorld and companion,
with no developer `PYTHONPATH`, and runs the packaged launcher's help command.
Package sources reject links, hardlinks and unexpected file types before writing
an archive, preventing accidental save/binary inclusion. No game assets are packed.

The [portable companion guide](portable-client.md) describes clean installation,
upgrade and rollback. Uninstalling from an active gated campaign is unsupported;
use a clean non-AP save or restore the full pre-AP folder backup. None of these
tests deploys to the game or changes the protected installation.

## Review and performance limits

The implementation keeps networking, one client session owner, one game save
owner and explicit feature adapters. The game wiring module exceeds the preferred
250-line guide because it contains the single callback/file boundary; reward and
check decisions remain in cohesive feature modules. It is not a service registry
or event bus. Native APIs and saved data are explicit dependencies.

Regression tests enforce bounded item creation, gear enforcement, transition
inspection, receipt history, scouting and snapshot sizes. The 6,000-seed matrix
and real-server cases run separately from tracing. These are operation bounds
and transport/generation evidence, not measured engine frame-time or load-time
performance. Engine performance, all post-merge game acceptance and independent
human code review remain **not run**. See [licence review](licence-review.md) for
the remaining owner decision before public distribution.

The complete verifier passes 587 covered tests plus 16 untraced cases (6,000
preset seeds and ten real-server cases). Every owned measured Python runtime
module has 100% lines/branches and Lua executable lines measure 100%. Lua branch
coverage is not measured. Packages rebuild identically; text line endings and ZIP
platform metadata are normalized. These results do not close the explicit human
review, licence decision or engine acceptance gates above.
