# Troubleshooting

## Replit workspace to MongoDB Atlas — 2026-10-14

### Current findings

The workspace's observed outbound IPv4 is `35.243.136.216`, unchanged on recheck and matching the temporary
Atlas access-list entry reported by the user. Atlas's access-list state and exact expiry timestamp cannot be
inspected from this workspace. The successful connections below show the current network path is open, but do
not independently prove which Atlas access-list row allowed it.

All three Atlas shard hostnames resolved. TCP connections to port 27017 succeeded. A direct TLS handshake using
each proper server hostname succeeded as TLS 1.3 under Python's default verified SSL context. No certificate
verification bypass, `tlsAllowInvalidCertificates`, or `tlsInsecure` option was used.

PyMongo's authenticated `ping` received Atlas error code `8000` with message `bad auth: authentication failed`.
This indicates authentication failed before database authorization could be established. It does not prove
whether the cause is an incorrect/inactive Atlas database user, mismatched password, URI encoding/auth-source
configuration, or another credential configuration issue. Do not troubleshoot this by weakening TLS.

### Diagnostic environment

- Python: 3.11.14
- OpenSSL: 3.6.0 (1 Oct 2025)
- PyMongo: 4.6.3
- Motor: 3.3.1
- `certifi` package: 2026.7.22
- Default OpenSSL CA file: `/etc/ssl/certs/ca-certificates.crt`
- Default SSL context loaded 174 system CA certificates

The user reports a temporary Atlas entry of `35.243.136.216/32`. Replit development egress is dynamic and should
not be treated as a stable address. A changed backend egress address may require a new Atlas `/32` entry. Check
the temporary entry's expiry in Atlas; its exact expiration is not visible in Replit.

### Safe next steps

1. Re-enter or correct `MONGO_URL` only through Replit Secrets. Do not paste it into chat or logs.
2. In Atlas, verify the database user is active and that its credentials/authentication settings match the URI.
3. After authentication works, verify least-privilege permissions for `curator_replit_dev` and `curator_pytest`.
   The test fixture calls `drop_database` on `curator_pytest` before and after the suite, so that operation must
   be permitted for the test database. Do not run the suite against production.
4. Rerun setup diagnostics, then the isolated test suite, then restart the application and run smoke checks.
   The workflow runs migrations during startup, so it should not be retried while database authentication fails.

### Verification attempts and limitations

Setup diagnostics reported the database, migrations, and participant-account checks as failed. The test suite
stopped in `conftest.py` before collecting tests because authentication failed during its `curator_pytest`
database setup. No successful database drop or write occurred.

The application workflow was restarted once after the access-list change. Its frontend build passed, but FastAPI
exited during startup migrations on the authentication error. The smoke script could not verify the app: the
backend was not serving, and the HTTPS request to the Replit preview also failed local certificate verification.
No TLS verification was disabled. Do not make repeated startup attempts until database authentication is fixed.
