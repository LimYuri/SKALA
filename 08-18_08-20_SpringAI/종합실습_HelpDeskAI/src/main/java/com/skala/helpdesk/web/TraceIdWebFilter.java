package com.skala.helpdesk.web;

import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

// 요청마다 짧은 traceId를 하나씩 만들어서 응답 헤더(X-Trace-Id)로도 내려주고 MDC에도 심어둠 -
// 감사 로그(AuditService)에서 같은 traceId로 요청 하나의 전체 흐름을 이어서 볼 수 있게 하기 위함
@Component
public class TraceIdWebFilter implements WebFilter {
    @Override public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String traceId = UUID.randomUUID().toString().substring(0, 8);
        exchange.getAttributes().put("traceId", traceId);
        exchange.getResponse().getHeaders().set("X-Trace-Id", traceId);
        return Mono.defer(() -> {
            MDC.put("traceId", traceId);
            return chain.filter(exchange).doFinally(signal -> MDC.remove("traceId"));
        });
    }
}
