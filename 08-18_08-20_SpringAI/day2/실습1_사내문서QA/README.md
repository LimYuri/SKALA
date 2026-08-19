# Spring AI Day 2 종합실습 - 사내 문서 Q&A

PDF의 "어제 만든 API 위에 근거를 붙인다"는 흐름에 맞춘 누적 프로젝트입니다.
기존 Day 1 주문 조회·요약 API(`com.skala.ch02`, `com.skala.day1`)를 유지하고,
Day 2 RAG API(`com.example.day2.lab2`)를 추가했습니다. Spring Boot 3.5.16,
Spring AI 1.1.8 기준입니다.

한 서버에서 다음 API가 함께 노출됩니다.

- Day 1: `/ch02/orders/{orderId}`, `/lab1/orders/{orderId}/summary`
- Day 2: `/lab2/ingest`, `/lab2/retrieve`, `/lab2/ask`

## 실행

```bash
export OPENAI_API_KEY="본인 키"
./gradlew bootRun
```

Swagger: `http://localhost:8080/swagger-ui.html`

```bash
curl -X POST http://localhost:8080/lab2/ingest
curl --get http://localhost:8080/lab2/retrieve --data-urlencode 'q=물건 돌려보내려면 며칠 안에 해야 해요?' --data 'topK=4'
curl -X POST http://localhost:8080/lab2/ask -H 'Content-Type: application/json' -d '{"question":"골드 등급 적립률은?"}'
./gradlew test -Peval
```

`LAB2_CHUNK_SIZE`, `LAB2_OVERLAP_CHARS`, `LAB2_TOP_K`, `LAB2_THRESHOLD` 환경변수로 실험값을 바꿀 수 있습니다. 한 번에 하나만 변경하세요.

## 기존 프로젝트에 복사할 때 확인

1. `com.example.day2`를 기존 `group`/메인 애플리케이션 하위 패키지로 변경합니다.
2. Spring AI가 1.0.x라면 `TokenTextSplitter` 생성자와 `VectorStore.delete(...)` 시그니처를 해당 버전에 맞춥니다.
3. 기존 VectorStore가 PGVector/Qdrant라면 simple starter를 제거하고 기존 설정을 유지합니다.
4. OpenAI가 아닌 모델을 쓰면 starter와 `application.yml` 모델 설정을 교체합니다.
