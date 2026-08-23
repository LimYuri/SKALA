# SpringAI 종합실습 — HelpDeskAI

Spring AI 교안의 **13. 종합실습 — HelpDeskAI 만들기**를 독립 프로젝트로 구현한 제출용 코드입니다. Day3 단일 실습에 덮어쓰지 않고, PDF가 지정한 프로젝트명 `SpringAI_종합실습`과 루트 패키지 `com.skala.helpdesk`를 사용했습니다.

## 핵심 기능

- RAG 문서 인제스트와 근거 출처 표시
- `orderStatus`, `createTicket` Tool과 소유권 검증
- 교환/환불 티켓 `PENDING` 생성 후 관리자 승인
- JDBC 영속 메모리와 `tenant:user:session` 격리
- 안전성 차단, Tool 횟수 제한, 감사/추적 ID
- 주 모델 장애 시 보조 모델 fallback
- 구조화 JSON 응답과 SSE `token` 후 `sources` 이벤트
- 토큰·비용·지연·Tool 지표, 50회 P95 부하 검증
- 10종 레드팀 프롬프트 방어 테스트

## 1. 테스트

```bash
./gradlew test --rerun-tasks --info
```

정상 결과: `39 tests`, `BUILD SUCCESSFUL`.

## 2. 실행

기본은 외부 API 비용이 들지 않는 재현 가능한 로컬 모드입니다.

기본 프로파일은 별도 설치가 필요 없는 `SimpleVectorStore`를 사용하며, `docker compose up -d` 후 `--spring.profiles.active=pgvector`로 실행하면 PostgreSQL/pgvector를 사용합니다.

```bash
./gradlew bootRun
```

- Swagger: `http://localhost:8080/swagger-ui.html`
- 사용자: `user1 / user1-pass`, `user2 / user2-pass`
- 관리자: `admin / admin-pass`

실제 OpenAI 모델을 사용할 때만 현재 터미널에 키를 설정하고 라이브 모드를 켭니다. API 키는 코드와 캡처에 넣지 마세요.

```bash
export OPENAI_API_KEY="본인_API_키"
export HELPDESK_LIVE_AI_ENABLED=true
./gradlew bootRun
```

## 3. PDF 검증 시나리오

1. `POST /api/admin/ingest`
2. `POST /api/chat` — `반품 규정 알려줘`
3. `POST /api/chat` — `제 주문 12345는 지금 어디예요?`
4. 같은 `sessionId`로 `그럼 그거 반품돼요?`
5. 같은 `sessionId`로 `교환으로 바꿔주세요`
6. `GET /api/admin/tickets/pending`으로 `PENDING` 확인
7. `POST /api/admin/tickets/{id}/approve`로 승인
8. `GET /api/admin/audit`, `GET /api/admin/metrics/summary`로 감사·성능 확인

요청 JSON 예시:

```json
{
  "question": "반품 규정 알려줘",
  "sessionId": "demo-1",
  "tenantId": "skala"
}
```

## 설계 선택과 제한

- 로컬에서 즉시 실행되도록 `SimpleVectorStore` + H2 JDBC를 사용했습니다. 교안의 아키텍처 계약(`VectorStore`, JDBC 영속화)은 유지합니다.
- 2026-08-20에 `OPENAI_API_KEY` + `HELPDESK_LIVE_AI_ENABLED=true` 조건으로 RAG, Tool, 멀티턴, 티켓 승인, SSE까지 라이브 OpenAI E2E를 실제 검증했습니다. fallback 로직은 장애 주입 테스트로 검증했습니다.
- 실제 `text-embedding-3-small` 유사도가 0.32~0.48대로 측정되어 RAG 기본 threshold를 0.62에서 0.35로 조정했습니다.
