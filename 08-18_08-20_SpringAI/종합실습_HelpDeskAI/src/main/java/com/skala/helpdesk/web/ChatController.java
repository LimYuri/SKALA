package com.skala.helpdesk.web;

import com.skala.helpdesk.chat.AnswerDto;
import com.skala.helpdesk.chat.HelpDeskService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import java.security.Principal;
import java.time.Duration;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

@RestController
@RequestMapping("/api/chat")
public class ChatController {
    private final HelpDeskService service;
    public ChatController(HelpDeskService service) { this.service = service; }

    // 일반 질문/답변. Principal에서 로그인 사용자 이름을 그대로 userId로 씀(권한 체크는 서비스단 소유권 확인으로 처리)
    @PostMapping
    public Mono<AnswerDto> ask(@Valid @RequestBody AskRequest request, Principal user, ServerWebExchange exchange) {
        return Mono.fromCallable(() -> service.askWithTrace(request.question(), request.tenantId(),
                        user.getName(), request.sessionId(), traceId(exchange)))
                .subscribeOn(Schedulers.boundedElastic());
    }

    // SSE 스트리밍. 토큰들을 먼저 다 흘려보내고 마지막에 sources 이벤트 하나로 출처를 붙여줌
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream(@Valid @RequestBody AskRequest request, Principal user,
                                                ServerWebExchange exchange) {
        Flux<ServerSentEvent<String>> tokens = service.streamAnswer(request.question(), request.tenantId(),
                        user.getName(), request.sessionId(), traceId(exchange))
                .map(token -> ServerSentEvent.builder(token).event("token").build());
        Mono<ServerSentEvent<String>> sources = Mono.fromCallable(() -> service.streamSources(request.question()))
                .subscribeOn(Schedulers.boundedElastic())
                .map(value -> ServerSentEvent.builder(value.toString()).event("sources").build());
        return tokens.concatWith(sources)
                .timeout(Duration.ofSeconds(60));
    }

    private String traceId(ServerWebExchange exchange) {
        return String.valueOf(exchange.getAttributeOrDefault("traceId", "no-trace"));
    }

    public record AskRequest(@NotBlank String question, @NotBlank String sessionId, String tenantId) {
        public AskRequest { if (tenantId == null || tenantId.isBlank()) tenantId = "skala"; }
    }
}
