# Spring AI Day 3 누적 종합실습 — 상담 에이전트

Day 1 주문 API → Day 2 사내 문서 RAG → Day 3 상담 에이전트를 한 Spring Boot 프로젝트에 누적했습니다.

## 포함 API

- Day 1: `/ch02/orders/{orderId}`, `/lab1/orders/{orderId}/summary`
- Day 2: `POST /lab2/ingest`, `GET /lab2/retrieve`, `POST /lab2/ask`
- Day 3: `POST /lab3/chat`, `GET /lab3/chat/history`
- 관리자: pending 조회, 승인, 감사 로그
- 관찰: `/actuator/metrics/ai.tokens`, `/ai.latency`, `/ai.tool.calls`

## 실행 순서

Java 21이 필요합니다. 외부 호출 없는 로컬 검증은 키 없이 실행할 수 있습니다.

```bash
./gradlew --no-daemon bootRun
```

실제 모델·임베딩 제출 캡처 때만 본인 OpenAI API 키와 라이브 모드를 사용합니다.

```bash
export OPENAI_API_KEY="본인 키"
export LAB3_LIVE_AI_ENABLED=true
./gradlew --no-daemon bootRun
```

1. Swagger `http://localhost:8080/swagger-ui.html`을 엽니다.
2. 오른쪽 위 **Authorize**에서 `user1` / `user1-pass`로 인증합니다.
3. `POST /lab2/ingest`를 먼저 실행합니다. Day 3의 `QuestionAnswerAdvisor`는 같은 VectorStore를 재사용합니다.
4. `POST /lab3/chat`에서 PDF의 아래 5턴을 순서대로 실행합니다.

```json
{
  "question": "단순변심 반품은 며칠 이내인가요?",
  "sessionId": "s1"
}
```

5. 같은 `sessionId`로 `제 주문 12345는 지금 어디예요?` → `그럼 그거 반품돼요?` → `환불로 접수해 주세요`를 보냅니다.
6. 새 `sessionId`로 `그거 어떻게 됐어요?`를 보내 주문번호를 되묻는지 확인합니다.
7. 다시 Authorize에서 `admin` / `admin-pass`로 인증한 뒤 `/lab3/admin/tickets/pending`을 조회합니다.
8. 메트릭과 감사 로그를 확인합니다.

## 권한·승인 설계

- Tool의 `userId`는 모델 인자가 아니라 서버의 `ToolContext`에서만 가져옵니다.
- 주문은 `orderId + ownerId` 조건으로 조회하므로 관리자 사칭 문장도 권한을 바꾸지 못합니다.
- 환불 Tool은 `PENDING` 티켓만 만듭니다.
- 승인은 모델에 Tool로 공개하지 않고 관리자 REST API에만 둡니다.
- Spring Security 인증 사용자를 `Principal`에서 읽고, 관리자 API는 `@PreAuthorize("hasRole('ADMIN')")`로 보호합니다.
- 실습 계정 비밀번호는 데모 전용이므로 운영 배포 시 외부 인증/JWT와 암호화 비밀번호로 교체해야 합니다.
- 요청마다 Tool 호출 횟수를 세고 기본 3회를 넘으면 명확한 오류로 중단합니다.

## 테스트

```bash
./gradlew --no-daemon test --rerun-tasks
```

외부 API 없이도 완료 기준과 레드팀 단위 테스트는 실행됩니다. 실제 모델의 Tool 선택과
Day 2 임베딩 RAG를 확인할 때만 API 키와 `LAB3_LIVE_AI_ENABLED=true`를 사용합니다.
