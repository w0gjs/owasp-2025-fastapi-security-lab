# Attack vs Defense

## 검증 원칙

동일한 요청을 두 앱에 전송한다.

- 취약 버전: 공격 효과가 발생해야 한다.
- 보안 버전: 기능은 유지하면서 공격 요청이 거부되거나 무해하게 처리되어야 한다.

## 기대 결과

| Scenario | Vulnerable app | Secure app |
| --- | --- | --- |
| Login SQLi | 303 로그인 성공 | 401 실패 + 이벤트 기록 |
| Search SQLi | 비공개 글 링크 노출 | 문자열 검색으로 처리 |
| Stored XSS | alert 실행 | 태그가 텍스트로 표시 |
| Private post IDOR | 타인 글 200 | 404 |
| General user admin | 200 | 403 + 이벤트 기록 |
| Delete another post | 303 삭제 | 403 + 이벤트 기록 |
| PHP upload | 303 저장 | 400 + 이벤트 기록 |
| Weak password | 가입 성공 | 400 |
| 5 failed logins | 계속 시도 가능 | 429 잠금 |
| Negative point transfer | 송신자 잔액 증가 | 400 + 이벤트 기록 |
| Tampered backup import | 변조 데이터 저장 | 400 + 이벤트 기록 |
| Debug error | 내부 상세 노출 | 일반화된 404 |
| `/docs` | 200 | 404 |
| Security headers | 누락 | CSP, XFO, XCTO 적용 |
