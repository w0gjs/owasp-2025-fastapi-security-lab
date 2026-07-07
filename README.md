# OWASP Top 10:2025 FastAPI Security Lab

동일한 커뮤니티 서비스를 **취약 버전**과 **보안조치 버전**으로 나누어 공격 전후를 비교하는
FastAPI 기반 애플리케이션 보안 포트폴리오 프로젝트입니다.

> 교육 및 허가된 로컬 테스트 전용입니다. 인터넷에 공개 배포하지 마세요.

## 프로젝트 구성

```text
owasp-2025-fastapi-lab/
├── vulnerable-app/  # OWASP Top 10:2025 취약점이 의도적으로 포함된 버전
├── secure-app/      # 동일 기능에 보안조치를 적용한 버전
├── docs/           # 공격·방어 비교 및 검증 문서
└── tests/          # 공격 전후 회귀검증
```

두 앱은 FastAPI, Jinja2, SQLAlchemy 2.0, PostgreSQL, Alembic을 공통으로 사용합니다.

## OWASP Top 10:2025 범위

| 분류 | 취약 버전 시나리오 | 보안 버전 조치 |
| --- | --- | --- |
| A01 Broken Access Control | IDOR, 일반 사용자 관리자 접근, 타인 글 삭제 | 소유자·role 검증과 거부 로그 |
| A02 Security Misconfiguration | 문서 노출, 헤더 누락, 무제한 업로드 | 문서 비활성화, CSP 등 보안 헤더, 업로드 allowlist |
| A03 Software Supply Chain Failures | 구버전 의존성 스캔 파일 | 실행 의존성 분리, 취약 의존성 제거 |
| A04 Cryptographic Failures | 비밀번호 평문 저장 | salt가 포함된 scrypt 해시 저장 |
| A05 Injection | 로그인·검색 SQLi, Stored/Reflected XSS | ORM 파라미터화와 Jinja 자동 escape |
| A06 Insecure Design | 음수·잔액 초과 포인트 송금 | 양수·잔액·수신자 업무 규칙 검증 |
| A07 Authentication Failures | 약한 비밀번호, 무제한 재시도, 긴 세션 | 복잡도, 잠금, 실패 로그, 30분 세션 |
| A08 Software or Data Integrity Failures | 서명 없는 JSON 백업 신뢰 | HMAC 서명 검증과 서버 소유자 강제 |
| A09 Security Logging & Alerting Failures | 공격 후에도 빈 활동 기록 | 인증·권한·업로드·변조 이벤트 기록 |
| A10 Mishandling of Exceptional Conditions | 예외·SQL·내부 경로 노출 | 일반화된 오류 응답과 debug 비활성화 |

## 실행 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r vulnerable-app/requirements.txt
```

## 취약 버전 실행

터미널 1:

```bash
cd vulnerable-app
cp -n .env.example .env
docker compose up -d postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

## 보안 버전 실행

터미널 2:

```bash
cd secure-app
cp -n .env.example .env
# .env의 두 REPLACE 값을 서로 다른 32자 이상 난수로 교체
docker compose up -d postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8001
```

초기 계정:

| 버전 | 일반 사용자 | 관리자 |
| --- | --- | --- |
| 취약 | `user1 / password123` | `admin / admin123` |
| 보안 | `user1 / Password123` | `admin / Admin12345` |

## 포트

| 대상 | 애플리케이션 | PostgreSQL |
| --- | --- | --- |
| 취약 버전 | `127.0.0.1:8000` | `localhost:5433` |
| 보안 버전 | `127.0.0.1:8001` | `localhost:5434` |

## 문서

- [OWASP 전체 범위](docs/owasp-coverage.md)
- [공격과 보안조치 비교](docs/attack-vs-defense.md)
- [취약 버전 상세 매트릭스](vulnerable-app/docs/vulnerability-matrix.md)
- [보안 버전 조치 매트릭스](secure-app/docs/remediation-matrix.md)

## 공격 전후 자동 비교

두 앱을 실행한 상태에서:

```bash
bash scripts/run-comparison.sh
```

자세한 기대 결과는 `tests/README.md`를 참고하세요.

## 포트폴리오 핵심 흐름

```text
취약 기능 구현 → PoC 재현 → 보안조치 적용 → 동일 PoC 차단 확인 → 자동 탐지 오탐·미탐 분석
```
