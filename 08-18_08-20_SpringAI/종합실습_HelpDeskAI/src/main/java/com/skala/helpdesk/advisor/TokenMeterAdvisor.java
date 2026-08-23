package com.skala.helpdesk.advisor;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

// 감사(0) 다음, 안전장치(100) 이전에 둬서 실제로 모델까지 갔다 온 호출만 토큰/비용을 집계함.
// 비용 단가는 대략치라 실제 청구액과는 다를 수 있음(과제 요구사항은 "집계가 되는지"라 정확한 단가까지는 안 맞춤)
public class TokenMeterAdvisor implements CallAdvisor {
    private final MeterRegistry meters;
    public TokenMeterAdvisor(MeterRegistry meters) { this.meters = meters; }
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        Timer.Sample sample = Timer.start(meters);
        try {
            ChatClientResponse response = chain.nextCall(request);
            var usage = response.chatResponse().getMetadata().getUsage();
            meters.counter("ai.tokens", "type", "prompt", "feature", "helpdesk")
                    .increment(usage.getPromptTokens());
            meters.counter("ai.tokens", "type", "completion", "feature", "helpdesk")
                    .increment(usage.getCompletionTokens());
            meters.counter("ai.cost.usd", "feature", "helpdesk")
                    .increment((usage.getPromptTokens() + usage.getCompletionTokens()) * 0.000001);
            return response;
        } finally {
            sample.stop(meters.timer("ai.latency", "phase", "model", "feature", "helpdesk"));
        }
    }
    @Override public String getName() { return "TokenMeterAdvisor"; }
    @Override public int getOrder() { return 50; }
}
