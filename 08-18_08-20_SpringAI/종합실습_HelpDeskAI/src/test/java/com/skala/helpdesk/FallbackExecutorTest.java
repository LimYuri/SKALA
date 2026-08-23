package com.skala.helpdesk;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.skala.helpdesk.chat.ModelFallbackExecutor;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "helpdesk.live-ai-enabled=false")
class FallbackExecutorTest {
    @Autowired ModelFallbackExecutor executor;

    @Test void 주모델_일시적장애는_3회_시도후_보조모델로_응답한다() throws Exception {
        AtomicInteger primaryCalls = new AtomicInteger();
        AtomicInteger fallbackCalls = new AtomicInteger();

        var result = executor.execute("user1", "primary", "fallback",
                () -> {
                    primaryCalls.incrementAndGet();
                    throw new IOException("injected transient outage");
                },
                () -> {
                    fallbackCalls.incrementAndGet();
                    return "fallback-response";
                },
                () -> "local-response");

        assertThat(result.value()).isEqualTo("fallback-response");
        assertThat(result.fallbackUsed()).isTrue();
        assertThat(result.localUsed()).isFalse();
        assertThat(primaryCalls).hasValue(3);
        assertThat(fallbackCalls).hasValue(1);
    }

    @Test void 주모델과_보조모델이_모두_실패하면_로컬응답을_반환한다() throws Exception {
        AtomicInteger primaryCalls = new AtomicInteger();
        AtomicInteger fallbackCalls = new AtomicInteger();
        AtomicInteger localCalls = new AtomicInteger();

        var result = executor.execute("user1", "primary", "fallback",
                () -> {
                    primaryCalls.incrementAndGet();
                    throw new IOException("primary outage");
                },
                () -> {
                    fallbackCalls.incrementAndGet();
                    throw new IOException("fallback outage");
                },
                () -> {
                    localCalls.incrementAndGet();
                    return "local-response";
                });

        assertThat(result.value()).isEqualTo("local-response");
        assertThat(result.fallbackUsed()).isTrue();
        assertThat(result.localUsed()).isTrue();
        assertThat(primaryCalls).hasValue(3);
        assertThat(fallbackCalls).hasValue(1);
        assertThat(localCalls).hasValue(1);
    }

    @Test void 잘못된_요청은_재시도하지_않고_보조모델으로도_넘기지_않는다() {
        AtomicInteger primaryCalls = new AtomicInteger();
        AtomicInteger fallbackCalls = new AtomicInteger();

        assertThatThrownBy(() -> executor.execute("user1", "primary", "fallback",
                () -> {
                    primaryCalls.incrementAndGet();
                    throw new IllegalArgumentException("bad request");
                },
                () -> {
                    fallbackCalls.incrementAndGet();
                    return "fallback-response";
                },
                () -> "local-response"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("bad request");

        assertThat(primaryCalls).hasValue(1);
        assertThat(fallbackCalls).hasValue(0);
    }
}
