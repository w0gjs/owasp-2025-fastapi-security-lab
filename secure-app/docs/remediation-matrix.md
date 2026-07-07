# Secure App Remediation Matrix

| OWASP 2025 | Security control | Implementation |
| --- | --- | --- |
| A01 | Owner and role authorization | `app/routers/posts.py`, `admin.py` |
| A02 | Headers, docs disabled, upload allowlist | `app/main.py`, `app/routers/upload.py` |
| A03 | Runtime dependencies only | `requirements.txt` |
| A04 | Salted scrypt password hashing | `app/common/passwords.py` |
| A05 | SQLAlchemy expressions and Jinja escaping | `app/routers/posts.py`, templates |
| A06 | Positive amount, balance, recipient rules | `app/routers/points.py` |
| A07 | Password policy, lockout, session timeout | `app/routers/auth.py`, `app/main.py` |
| A08 | HMAC-signed backup and server-side owner | `app/routers/backup.py` |
| A09 | Persistent security events | `app/common/audit.py` |
| A10 | Generic error responses | `app/routers/errors.py` |
