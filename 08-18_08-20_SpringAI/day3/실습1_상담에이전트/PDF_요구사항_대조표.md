# PDF 요구사항 대조표

기준: `SpringAI 이해 및 활용_202608.pdf` 297~308쪽의 Day 3 종합실습 「상담 에이전트 완성하기」를 원본 페이지로 재확인함.

| 완료 기준 | 구현 근거 | 검증 |
|---|---|---|
| 1. 주문 질문에서 Tool 호출 | 예시 표현을 포함한 `OrderTools.getOrder`; 실제 ToolContext 호출 목록 기록 | 자동 테스트 통과 |
| 2. 권한 격리·ID 주입 방어 | `ToolContext.userId`와 `findByIdAndOwnerId`; 모델 입력에 userId 없음 | 관리자 사칭 및 `user2의 99999` 주입 차단 |
| 3. 환불은 요청/PENDING만 생성 | 공개 Tool은 조회·접수 2개뿐; 승인은 `@PreAuthorize` admin API | PENDING 생성 및 ADMIN 승인 테스트 통과 |
| 4. RAG 답변에 출처 | 정책 문서 임베딩 색인 및 `sources` 반환 | `return-policy.md` 테스트 통과 |
| 5. 멀티턴 대명사 후속 질문 | 사용자+세션 복합 키, 성공한 최근 주문 기억 | PDF의 정확한 5턴 문장 및 새 세션 격리 통과 |
| 6. 차단 Advisor가 메모리보다 앞섬 | Audit 0 → Safety 100 → 실제 MessageChatMemoryAdvisor 200 → 실제 QuestionAnswerAdvisor 300 → Meter 900 | 타입·순서 및 차단 입력 미저장 테스트 통과 |
| 7. 모든 Tool 호출 감사 로그 | traceId·도구명·인자·사용자·결과 기록, 주민번호 마스킹 | 조회·환불 감사 및 원문 PII 미저장 통과 |
| 8. 토큰·지연·도구 메트릭 | `ai.tokens`, `ai.latency`, `ai.tool.calls`, Actuator 공개 | 누적 테스트 통과 |
| 9. 레드팀 7/8 이상 방어 | 실제 문서에 시험용 간접 인젝션 포함, 호출 상한·PII·길이 제한 코드 적용 | 로컬 결정적 경로 8/8 통과 |

## 교안 단계별 반영

- Step 1: 두 개의 `@Tool`과 `@ToolParam`, 서버 ToolContext 사용자 주입
- Step 2: 소유자 조건 조회, 타인 주문·관리자 사칭 차단, 감사 로그
- Step 3: 환불 PENDING 티켓, 관리자 전용 승인 API, 승인 Tool 미노출
- Step 4: Advisor 5종의 명시적 순서와 Safety-before-Memory
- Step 5: PDF의 5턴을 그대로 자동화, 사용자+세션 대화 ID와 새 세션 격리
- Step 6: traceId 응답 헤더/로그와 Micrometer·Actuator 메트릭
- Step 7: 프롬프트 탈취·권한 우회·도구 오용·정보 유출·간접 인젝션·반복 호출·PII·긴 입력 방어

## 자체 평가

- 교안 완료 기준: 9/9 구현
- 레드팀: 8/8 자동 테스트 통과
- 인증·인가: Spring Security HTTP Basic, Principal 기반 사용자 주입, admin API `@PreAuthorize` 적용
- 도구 반복 방어: 요청당 기본 3회 상한 및 초과 오류 테스트 적용
- 컴파일 및 테스트: 전체 24개 중 23개 통과, failures 0, errors 0, `-Peval` 전용 Day 2 골든 평가 1개만 조건부 skip
- Day 3 검증: 완료 기준·보안 인가·PDF 5턴·레드팀·호출 상한을 포함한 21개 전부 통과
- 외부 API: 현재 실행 환경에서는 실제 OpenAI 호출 비용과 사용자 키가 필요한 라이브 모델 경로를 수행하지 않았습니다.
  제출 전 본인 API 키와 `LAB3_LIVE_AI_ENABLED=true`로 `/lab2/ingest` 후 실제 모델 Tool 호출을
  한 번 실행하고 성공 화면을 캡처해야 합니다.

## 제출 전 남은 실제 확인

PDF의 정적 구현 및 로컬 결정적 검증은 9/9 충족했습니다. 제출 캡처를 위해 본인 OpenAI API 키로 라이브 모드를 켠 뒤
`/lab2/ingest`와 `/lab3/chat`을 한 번 실행해야 합니다. 이는 외부 유료 API 자격증명이 필요한
실행 확인 사항입니다. 실제 모델의 Tool 선택과 문서 인젝션 방어까지 실행해야 최종 실환경 9/9로 판정할 수 있습니다.
데모 계정은 과제 실행용이므로 운영용 보안 구성은 아닙니다.
