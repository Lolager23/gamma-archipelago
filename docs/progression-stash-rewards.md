# Step 15: orange progression stashes

Stack base: #18. `rewards_progression_stashes` adds one guaranteed progression
coordinate item, ID 28051201, for a calibrated psi helmet in the named Cordon
`esc_treasure_3` container. Its native description identifies the pipe near the
Rookie Village. Missing/moved containers keep delivery pending rather than
rerolling behind another gate. Existing white stashes keep their separate markers.

Coordinates reveal an AP-owned orange marker. Only interaction with the recorded
box enables delivery. The protected helmet is created directly in the actor's
inventory using the inspected native `good_psy_helmet` section, so NPC scavenging
cannot remove critical loot. The saved action/uncertain-creation policy from step
14 applies. Successful creation claims the marker; merely receiving coordinates
or taking unrelated items does not. No story task is auto-completed or granted.

The AP solver has a separate local Cordon claim event requiring the coordinate
item. Receiving coordinates alone does not grant its Calibrated Psi Protection
event. Local events have no network location IDs and never consume reward slots.
The required coordinate item is placed exactly once. Default and legacy seeds
remain unchanged. Later gate/goal steps will consume this local protection rule.

The full verifier passes 446 covered tests plus two real-server cases, with 100%
measured Python lines/branches and Lua executable lines. Tests include fixed-box
selection, wrong-box refusal, failed creation, actor ownership, marker removal,
reload, solver event access and excluding events from network manifests. Lua
branch coverage is not measured. Engine geometry, orange rendering and native
psi effects are not run; Owen will verify after merge. No game was launched.
