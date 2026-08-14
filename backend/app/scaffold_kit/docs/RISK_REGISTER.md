# RISK_REGISTER.md

**Last updated:** _YYYY-MM-DD_

---

## Severity Scale

| Level | Meaning | Response |
|---|---|---|
| 🔴 Critical | Data loss, security breach, or system unusable | Fix before anything else |
| 🟠 High | Major feature broken or serious performance problem | Fix this sprint |
| 🟡 Medium | Degraded experience, technical debt with real cost | Schedule it |
| 🟢 Low | Cosmetic or minor cleanup | Fix when convenient |

---

## Active Risks

| # | Severity | Risk | Impact if it happens | Likelihood | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | Open |

---

## Security Checklist

- [ ] No hardcoded secrets anywhere in code or history
- [ ] All user input validated server-side
- [ ] SQL parameterized (no string-concatenated queries)
- [ ] Authentication on every protected route
- [ ] Authorization checked per resource, not just per route
- [ ] Passwords hashed with a modern algorithm (bcrypt / argon2)
- [ ] Secrets in environment variables, never in the repo
- [ ] Dependencies scanned for known CVEs
- [ ] Internal errors never exposed to end users
- [ ] Data backed up, and **restore tested at least once**

---

## Performance Checklist

- [ ] No N+1 queries
- [ ] Indexes on all columns used in `WHERE` / `JOIN` / `ORDER BY`
- [ ] Large result sets paginated
- [ ] No blocking work on the UI thread
- [ ] Connections and file handles closed properly
- [ ] Caching used where reads dominate

---

## Assumptions That Could Break

_Every assumption in `PROJECT_OVERVIEW.md` is a risk until verified. List the dangerous ones here._

| Assumption | What breaks if it's wrong | How to verify |
|---|---|---|
| | | |
