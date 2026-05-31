# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ |
| Tagged releases | ✅ (latest only) |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a security issue, email: **lrameshkumar126@gmail.com**

Include in your report:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (optional)

You will receive a response within 72 hours. We will work with you to understand and address
the issue before public disclosure.

## Security Architecture Notes

For contributors and auditors, these are the key security properties of AEP:

### API Key Authentication
- Raw keys are **never stored** — only their SHA256 hash is persisted.
- Keys are prefixed `aep_` and generated with `secrets.token_hex(24)` (192 bits of entropy).
- A revoked key (`revoked_at IS NOT NULL`) is permanently rejected — no re-activation.
- Auth is **disabled by default** (`AEP_API_AUTH_ENABLED=false`) for offline dev. Enable in production.

### Admin Bootstrap
- The first API key is created via `POST /admin/api-keys` with `X-Admin-Secret` header.
- This header value comes from `AEP_ADMIN_SECRET` env var — never hardcoded.
- When auth is disabled, the admin secret check is skipped for local dev.

### RBAC Roles
- `viewer(0) < evaluator(1) < approver(2) < admin(3)` — hierarchical level comparison.
- Role is checked per-endpoint via `require_role(minimum)` FastAPI dependency.

### Rate Limiting
- Sliding-window rate limit per API key (or IP when unauthenticated).
- Default: 1000 requests/minute. Configurable via `AEP_RATE_LIMIT_PER_MINUTE`.
- `/health` and `/ready` are exempt from rate limiting.
- **Note:** The in-process rate limiter does not coordinate across multiple Uvicorn workers
  or Kubernetes pods. For multi-process production deployments, use a Redis-backed rate limiter.

### Security Headers
Every HTTP response includes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0` (modern browsers use CSP instead)
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### Audit Trail
- Every mutation writes an `AuditEvent` with `sha256(prev_hash + canonical_payload)`.
- The chain is tamper-evident. Verify it via `GET /audit/verify`.
- Audit events are never deleted or updated.

### Deployment Hardening
- Dockerfile: non-root user (UID 1000), multi-stage build (no dev tools in production image).
- Kubernetes: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`,
  all Linux capabilities dropped.

### Known Limitations
- In-process rate limiting is single-process only (see Rate Limiting note above).
- No CSRF protection — AEP is an API server (no cookies/sessions); CSRF is not applicable.
- No Content-Security-Policy header — CSP for the React SPA requires frontend configuration.
