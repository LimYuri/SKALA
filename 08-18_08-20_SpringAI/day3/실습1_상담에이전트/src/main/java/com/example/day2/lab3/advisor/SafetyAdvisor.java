package com.example.day2.lab3.advisor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

public class SafetyAdvisor implements CallAdvisor {
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        String prompt = request.prompt().getContents().toLowerCase();
        if (prompt.length() > 8_000 || prompt.matches("(?s).*(이전 지시를 무시|system prompt를 보여|주민등록번호).*")) {
            throw new IllegalArgumentException("SafetyAdvisor가 안전하지 않은 모델 요청을 차단했습니다.");
        }
        return chain.nextCall(request);
    }
    @Override public String getName() { return "SafetyAdvisor"; }
    @Override public int getOrder() { return 100; }
}
