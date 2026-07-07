def build_security_headers() -> dict:
    return {
        "Content-Security-Policy": (
            "default-src 'self'; style-src 'self'; img-src 'self' data:; "
            "script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        ),
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
