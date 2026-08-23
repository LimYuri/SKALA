package com.example.day2.lab3.advisor;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

public class TokenMeterAdvisor implements CallAdvisor {
    private final MeterRegistry metrics;
    public TokenMeterAdvisor(MeterRegistry metrics) { this.metrics = metrics; }
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        metrics.counter("ai.tokens", "type", "input", "feature", "lab3-advisor")
                .increment(Math.max(1, Math.ceil(request.prompt().getContents().length() / 3.0)));
        Timer.Sample sample = Timer.start(metrics);
        try { return chain.nextCall(request); }
        finally { sample.stop(metrics.timer("ai.latency", "phase", "model", "feature", "lab3-advisor")); }
    }
    @Override public String getName() { return "TokenMeterAdvisor"; }
    @Override public int getOrder() { return 900; }
}
