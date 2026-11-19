# Step 17: Haruka skill levels

Stack base: #20. `rewards_stat_levels` enables four useful rewards: Strength,
Endurance, Survival and Scavenging. Each grants one level, capped at the inspected
15-level Haruka baseline. Missing tables/functions, invalid numeric data or an
incompatible cap refuse delivery before acknowledgement.

A saved receipt plan computes the next level, previous/next XP requirement and
stat increments from the native skill tables. It preserves accumulated experience
and raises it to at least the completed level's threshold. Strength, Endurance
and Survival call their explicit native recalculation functions; Scavenging is
read directly by native consumers. Failure retries the same values, avoiding a
second level. Every retry validates the current native schema. Once the saved
target level exists, retries only recalculate effects, preserving XP, later levels
and stat changes earned during normal play. Reapplying a target also preserves
any higher accumulated XP. Haruka owns ordinary XP, stat effects and its save data;
AP owns only its receipt plans. A capped reward is consumed without exceeding 15.

Full verifier: 464 covered tests and two real-server cases, all per-module gates
passed, 100% measured Python lines/branches and Lua executable lines. Tests cover
all skills, XP boundaries, invalid schemas, absent integration, cap, recalculation
failure and save/load without duplicate levels. Lua branch coverage is not
measured. Actual stat/UI changes are not run, reserved for Owen after merge.
No game launch, deployment or protected-install changes were performed.
