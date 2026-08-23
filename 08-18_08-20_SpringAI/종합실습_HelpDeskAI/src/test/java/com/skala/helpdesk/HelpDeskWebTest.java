package com.skala.helpdesk;

import static org.springframework.security.test.web.reactive.server.SecurityMockServerConfigurers.mockUser;

import com.skala.helpdesk.advisor.AuditService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.reactive.server.WebTestClient;

@SpringBootTest(properties = "helpdesk.live-ai-enabled=false", webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
class HelpDeskWebTest {
    @Autowired WebTestClient client;
    @Autowired AuditService audit;

    @Test void 동기_API는_구조화응답을_반환한다() {
        client.mutateWith(mockUser("user1").roles("USER")).post().uri("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue("{\"question\":\"반품 규정 알려줘\",\"sessionId\":\"web\",\"tenantId\":\"skala\"}")
                .exchange().expectStatus().isOk()
                .expectHeader().exists("X-Trace-Id")
                .expectBody().jsonPath("$.answer").exists().jsonPath("$.sources[0].document").isEqualTo("return-policy.md")
                .jsonPath("$.toolUsed").isEqualTo(false);
    }

    @Test void SSE는_token_이벤트뒤에_sources_이벤트를_보낸다() {
        client.mutateWith(mockUser("user1").roles("USER")).post().uri("/api/chat/stream")
                .contentType(MediaType.APPLICATION_JSON).accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue("{\"question\":\"반품 규정 알려줘\",\"sessionId\":\"sse\",\"tenantId\":\"skala\"}")
                .exchange().expectStatus().isOk().expectBody(String.class)
                .value(body -> org.assertj.core.api.Assertions.assertThat(body)
                        .contains("event:token", "event:sources", "return-policy.md"));
    }

    @Test void 일반사용자는_admin을_403으로_차단하고_ADMIN은_접근한다() {
        client.mutateWith(mockUser("user1").roles("USER")).get().uri("/api/admin/tickets/pending")
                .exchange().expectStatus().isForbidden();
        client.mutateWith(mockUser("admin").roles("ADMIN")).get().uri("/api/admin/tickets/pending")
                .exchange().expectStatus().isOk();
    }

    @Test void Tool_감사로그에_HTTP_추적ID가_전파된다() {
        client.mutateWith(mockUser("user1").roles("USER")).post().uri("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue("{\"question\":\"주문 12345 어디예요?\",\"sessionId\":\"trace\",\"tenantId\":\"skala\"}")
                .exchange().expectStatus().isOk();
        org.assertj.core.api.Assertions.assertThat(audit.events())
                .anyMatch(event -> event.action().equals("orderStatus")
                        && !event.traceId().equals("no-trace") && !event.traceId().isBlank());
    }
}
