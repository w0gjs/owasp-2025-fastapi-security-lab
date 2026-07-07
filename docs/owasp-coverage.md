# OWASP Top 10:2025 Coverage

| ID | Category | Vulnerable implementation | Primary PoC |
| --- | --- | --- | --- |
| A01 | Broken Access Control | Missing owner/role checks | user1 → user2 private post/admin/delete |
| A02 | Security Misconfiguration | Docs, missing headers, unrestricted upload | `/docs`, response headers, `.php` upload |
| A03 | Software Supply Chain Failures | `requirements-legacy.txt` | `pip-audit -r requirements-legacy.txt` |
| A04 | Cryptographic Failures | Plaintext password column | `SELECT username, password FROM users` |
| A05 | Injection | Raw SQL and disabled HTML escaping | SQLi and `<script>alert(1)</script>` |
| A06 | Insecure Design | Missing transfer business rules | Transfer `-500` points |
| A07 | Authentication Failures | Weak passwords and no lockout | Register `1234`, fail login 10 times |
| A08 | Software or Data Integrity Failures | Unsigned backup import trusts `user_id` | Modify exported JSON and import |
| A09 | Security Logging & Alerting Failures | Empty event list | Attack then open security events |
| A10 | Mishandling of Exceptional Conditions | Detailed debug responses | `/debug/error`, `/debug/db-error` |
