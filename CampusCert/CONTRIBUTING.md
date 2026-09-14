# Contributing

## Branch model

```
main        <- protected, PR-only, tagged at milestones
develop     <- integration branch, PR-only
feature/*, fix/*, docs/*   <- your work happens here
```

**`main` is protected** — no direct pushes or merges from anyone, ever. It only
advances via a PR from `develop`, at the Week 3 and Week 6 milestones.

**`develop`** takes PRs from feature branches. Any teammate other than the PR's
author can review and merge it — there's no fixed reviewer, just don't approve or
merge your own work.

## Daily workflow

```bash
# start a feature
git checkout develop
git pull origin develop
git checkout -b feature/exam-timer

# commit as you go
git add .
git commit -m "feat: implement exam timer"

# push
git push -u origin feature/exam-timer

# before opening a PR, bring your branch up to date
git checkout develop && git pull origin develop
git checkout feature/exam-timer
git merge develop        # resolve conflicts locally, then commit

# open PR: feature/exam-timer -> develop
```

Release: PR `develop -> main`, then tag (e.g. `v0.3.0`). Do this at clear milestones —
end of Week 3 (core flow working end-to-end) and end of Week 6 (MVP freeze) — not
continuously, so `main` always reflects a demoable state.

## Commit convention

```
feat:      new feature
fix:       bug fix
docs:      documentation only
test:      adding/adjusting tests
refactor:  code change with no behavior change
chore:     tooling, config, housekeeping
```

## Ownership & merge-conflict avoidance

See the ownership table in `README.md`. In short:

- Stay inside your own module folder for your feature work.
- If you need to touch a shared folder (`core/`, `shared/`, `api/`, `database/migrations/`),
  say so in the team chat first.
- Keep PRs small and scoped to one feature — a giant PR touching five folders is the
  fastest way to get a conflict.
- Pull `develop` at the start of every work session, not just before opening a PR.

## Who reviews your PR

Anyone on the team except you. Post it in the team chat and whoever's free reviews
and merges. The only rule is you never merge your own PR.

## Keeping integration painless

Merge conflicts and integration bugs are different problems — folder ownership
solves the first, not the second. Before building anything that crosses the
frontend/backend boundary, write the request/response shape in
`docs/api-contracts.md` and get a quick nod from whoever owns the other side.
Run `docker compose up` (see `docs/INTEGRATION.md`) before every weekly merge to
`develop` so you catch integration breaks early, not during Week 6 freeze.

## PR checklist

- [ ] Branch is up to date with `develop`
- [ ] Tests pass locally
- [ ] PR description explains *what* changed and *why*
- [ ] No secrets, `.env`, or generated files committed
- [ ] Reviewed and merged by someone other than the author
- [ ] CI is green

## Rules

1. Pull latest `develop` before starting work.
2. One feature = one branch.
3. Never work directly on `main`.
4. Keep PRs small.
5. Test before opening a PR.
6. Explain changes in the PR description.
7. Review at least one teammate's PR per week.
8. Communicate breaking changes before merging them.
9. Resolve conflicts together, not by force-pushing over someone.
10. Don't leave uncommitted work sitting for more than a day or two.
11. Integrate frequently.
12. Never commit secrets.
13. Every member should be able to explain their own module to the teacher.
14. Everyone contributes to final integration and testing.
