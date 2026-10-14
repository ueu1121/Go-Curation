# Project state

Last checked: 2026-10-14. Branch: `portability/replit`; starting commit for this portability work:
`56d10c8b39e2d8e43f4b4b62d88634493c9df731`. Current changes are local to this branch; no merge or deployment was
performed.

## Replit verification

- Development `DB_NAME` is configured as `curator_replit_dev`. The test fixture overrides it to
  `curator_pytest` and asserts the `_pytest` suffix before attempting its database cleanup.
- Current observed outbound IPv4 is `35.243.136.216`, matching the temporary Atlas `/32` entry the user reports
  adding. Replit development egress is not guaranteed stable. The entry's exact expiry time is not visible from the
  workspace and must be checked in Atlas. If egress changes, the Atlas entry may need updating.
- DNS resolved the three Atlas shard nodes; TCP port 27017 connected to each; direct TLS using each proper
  hostname succeeded as TLS 1.3 with normal certificate verification.
- The MongoDB driver then received Atlas error `8000`, `bad auth: authentication failed`. Authentication, not
  TLS, is the current blocker. The database user's access to either database is therefore unverified.
- The `Start application` workflow was restarted once. The frontend build passed, but FastAPI exited during
  startup migrations after the same authentication failure. The application is not serving.
- Setup diagnostics fail on database reachability, migrations, and participant accounts. Tests fail in
  `conftest.py` before collection while attempting the isolated `curator_pytest` setup. The read-only smoke
  script could not verify the app: the workflow is down, and the HTTPS request to the Replit preview failed
  certificate verification. TLS verification was not disabled.

No database operation succeeded, no candidate outings were added, and no production data or deployment was
changed. Research, notifications, scheduling, and real-provider integrations remain disabled.

## Pending verification

Correct the development `MONGO_URL` through Replit Secrets, then verify authentication and least-privilege
permissions for the application and test databases. Confirm the test user can perform the test fixture's
database cleanup on `curator_pytest`. Only then rerun setup diagnostics, tests, workflow startup, and smoke checks.
