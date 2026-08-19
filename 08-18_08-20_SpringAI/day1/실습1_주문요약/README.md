# Day 1 주문 요약 API

## 실행

```bash
export OPENAI_API_KEY="sk-..."
./gradlew bootRun
```

Swagger UI: <http://localhost:8080/swagger-ui.html>

## 확인

```bash
curl 'http://localhost:8080/ch02/orders/12345?userId=user1'
curl 'http://localhost:8080/lab1/orders/12345/summary?userId=user1'
curl 'http://localhost:8080/lab1/orders/99999/summary?userId=user1'
```

API 키가 없거나 AI 호출이 실패하면 주문 정보 기반 fallback 요약을 반환합니다.

## 구조

```text
com.skala.ch02
├─ domain/Order.java, OrderNotFoundException.java
├─ repository/OrderRepository.java
└─ web/OrderController.java

com.skala.day1
├─ config/Lab1AiConfig.java
├─ service/OrderSummaryService.java
└─ web/OrderSummaryController.java, SummaryResponse.java,
       ErrorResponse.java, Lab1ExceptionHandler.java
```

`OrderSummaryController`는 `ChatClient`를 직접 사용하지 않습니다. 주문 조회와
AI 호출은 `OrderSummaryService`에 있고, AI 호출 실패 시 기존 주문 정보로 만든
fallback 문장을 반환합니다. 없는 주문과 다른 사용자의 주문은 모두 동일하게
404로 응답합니다.
