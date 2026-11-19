# Git workflow

## Identity and repository

Use this repository's local identity: **Owen Welch <owenwelch@hotmail.co.uk>**.
The authenticated personal GitHub account is `Lolager23`. Email verification could
not be checked with the existing token scope; the commit address still uses the
explicit address requested. Global work identity must remain untouched.

This checkout sets `core.hooksPath` locally to `.githooks`, whose commit and push
hooks validate the personal identity, including outgoing commit authors and
committers. This replaces the machine's work-only identity policy for this repo;
the global configuration and work repositories remain untouched. On a fresh
clone run `git config --local core.hooksPath .githooks` after setting local
`user`, `author` and `committer` names/emails and `user.useConfigOnly=true`.
Explicit author/committer settings are needed because this machine has work
overrides in its global config. The initial published bootstrap commit `e467777`
inherited those work overrides; that history is retained. Subsequent commits use
the personal identity. The current single-owner policy rejects
any other outgoing identity; revisit that policy explicitly before collaboration.

The push guard checks commits not already reachable from fetched remote branches.
GitHub-created merge commits already published on the remote may use GitHub's
committer identity; importing that shared history is not new authored work.
Unpublished commits and the current local author/committer still require the
personal identity above. This rule is identical for new and existing branches.

Keep `main` in a state that passes automated checks. Initialise it with the project
charter and standards, then develop the Archipelago foundation on
`codex/archipelago-integration`. Create the remote as private initially. Public
publication and release are separate decisions.

## Daily branch work

1. Fetch origin and update local `main` with `git pull --ff-only`.
2. Create one `codex/<short-purpose>` branch from the intended base.
3. Implement one roadmap increment with tests and documentation.
4. Inspect the full diff and staged changes; never stage game installations.
5. Run verification, commit coherent changes and push with an upstream branch.
6. Open a PR against `main`, or explicitly identify an unmerged dependency.
7. Keep it draft until its acceptance checks are complete and evidence is attached.
8. Address review in follow-up commits. Merge only after approval and passing CI.
9. After merge, fetch the result and start the next branch from updated `main`.

Prefer sequential merged increments over a long stack of dependent PRs. If a
stack is necessary, name the dependency in the PR and retarget after it merges.
Do not combine installer updates, progression changes and unrelated refactors.

## Commits

Use `type(scope): imperative description`, for example:

```text
feat(bridge): reject items from a different seed
fix(receipts): retain checks while the server is offline
test(save): reproduce item replay after loading an older save
docs(plan): define the initial progression boundary
```

Types: `feat`, `fix`, `test`, `refactor`, `docs`, `build`, `ci`, `chore`.
Use the body for reasoning and constraints. Reference a real issue when one
exists. Avoid vague subjects such as "updates" or "fix stuff".

A commit should be reviewable and internally consistent. Do not mix mechanical
formatting with behaviour changes. Do not include generated packages, local
paths, logs, archives, personal saves or credentials. Check author and committer
identity before publishing. Never manufacture a test result or approval.

## History and recovery

Rebase an unpublished branch when useful. Do not rewrite a shared branch without
coordination. Never force-push `main`; use `--force-with-lease` only when rewriting
an explicitly authorised feature branch. Use `git revert` for a published defect.
Keep checkpoint commits before a risky refactor; backups protect game state, not
Git history. A source checkout is not a save-game backup.

## PR and release gates

The PR template records purpose, test evidence, save compatibility, isolation and
remaining work. Automated checks must pass, and behaviour that needs GAMMA must
have an in-game result or remain explicitly unverified. Require independent review
for progression logic and save/receipt handling before a public release.

Tag releases `vMAJOR.MINOR.PATCH`. Use `v0.x` for experimental builds and state
supported Anomaly, GAMMA and Archipelago versions in each release. Changes to
published item IDs, location IDs or save schemas require a migration or an explicit
breaking-version change. Retain reproducible source and package checksums.
