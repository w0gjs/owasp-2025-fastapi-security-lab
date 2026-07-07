# Comparison Tests

두 앱을 각각 8000, 8001 포트에서 실행한 뒤 저장소 루트에서 다음을 실행한다.

```bash
bash scripts/run-comparison.sh
```

기대 결과:

| Scenario | Vulnerable | Secure |
| --- | --- | --- |
| Login SQL Injection | 303 | 401 |
| API docs | 200 | 404 |
| Private post IDOR | 200 | 404 |
| Negative point transfer | 303 | 400 |
| PHP upload | 303 | 400 |

추가 직접 호출 테스트는 임시 SQLite DB를 이용해 다음을 확인했다.

- 취약 버전: 평문 비밀번호, SQLi 우회, 음수 송금, 변조 백업 수용
- 보안 버전: scrypt 해시, SQLi 차단, 음수 송금 차단, HMAC 변조 차단
- 보안 버전: 일반 사용자 관리자 접근 403, IDOR 404, XSS escape
- 보안 버전: 로그인 5회 실패 후 429, 위험 업로드 400, 보안 이벤트 기록
