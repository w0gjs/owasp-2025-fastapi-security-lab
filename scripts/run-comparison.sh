#!/usr/bin/env bash
set -u

VULNERABLE_URL="${VULNERABLE_URL:-http://127.0.0.1:8000}"
SECURE_URL="${SECURE_URL:-http://127.0.0.1:8001}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

http_code() {
  curl -sS -o /dev/null -w '%{http_code}' "$@"
}

row() {
  printf '%-28s | %-10s | %-10s\n' "$1" "$2" "$3"
}

printf '%-28s | %-10s | %-10s\n' 'Scenario' 'Vulnerable' 'Secure'
printf '%s\n' '-----------------------------+------------+-----------'

v_login="$(http_code --data-urlencode "username=' OR '1'='1' --" --data-urlencode 'password=x' "$VULNERABLE_URL/login")"
s_login="$(http_code --data-urlencode "username=' OR '1'='1' --" --data-urlencode 'password=x' "$SECURE_URL/login")"
row 'Login SQL Injection' "$v_login" "$s_login"

row 'API docs exposure' "$(http_code "$VULNERABLE_URL/docs")" "$(http_code "$SECURE_URL/docs")"

curl -sS -c "$TMP_DIR/v.cookies" -o /dev/null \
  --data-urlencode 'username=user1' --data-urlencode 'password=password123' "$VULNERABLE_URL/login"
curl -sS -c "$TMP_DIR/s.cookies" -o /dev/null \
  --data-urlencode 'username=user1' --data-urlencode 'password=Password123' "$SECURE_URL/login"

row 'Private post IDOR' \
  "$(http_code -b "$TMP_DIR/v.cookies" "$VULNERABLE_URL/posts/private/4")" \
  "$(http_code -b "$TMP_DIR/s.cookies" "$SECURE_URL/posts/private/4")"

row 'Negative point transfer' \
  "$(http_code -b "$TMP_DIR/v.cookies" --data 'recipient_username=user2&amount=-100' "$VULNERABLE_URL/points/transfer")" \
  "$(http_code -b "$TMP_DIR/s.cookies" --data 'recipient_username=user2&amount=-100' "$SECURE_URL/points/transfer")"

printf '<?php echo "poc"; ?>\n' > "$TMP_DIR/poc.php"
row 'PHP upload' \
  "$(http_code -b "$TMP_DIR/v.cookies" -F "file=@$TMP_DIR/poc.php;type=text/html" "$VULNERABLE_URL/upload")" \
  "$(http_code -b "$TMP_DIR/s.cookies" -F "file=@$TMP_DIR/poc.php;type=text/html" "$SECURE_URL/upload")"

printf '\nExpected status patterns are documented in docs/attack-vs-defense.md.\n'
