# Moa Community - Secure App

`vulnerable-app/`과 동일한 사용자 기능에 보안조치를 적용한 비교 버전입니다.

## 실행

```bash
cp -n .env.example .env
# .env의 SESSION_SECRET과 BACKUP_SIGNING_KEY를 각각 다른 난수로 교체
docker compose up -d postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8001
```

난수 생성 예시:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))"
```

초기 계정:

- `admin / Admin12345`
- `user1 / Password123`
- `user2 / Password123`

적용된 조치는 `docs/remediation-matrix.md`와 루트 `docs/attack-vs-defense.md`를 참고하세요.
