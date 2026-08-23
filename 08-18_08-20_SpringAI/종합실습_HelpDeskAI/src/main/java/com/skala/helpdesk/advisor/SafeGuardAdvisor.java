package com.skala.helpdesk.advisor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

// SafetyService랑 겹치는 것 같지만 역할이 다름: SafetyService는 서비스 진입 초반에 원문 질문을 검사하고,
// 이건 Advisor 체인 안에서 모델에 실제로 들어갈 프롬프트(메모리에 쌓인 이전 대화 포함) 기준으로 한번 더 걸러줌
public class SafeGuardAdvisor implements CallAdvisor {
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        String text = request.prompt().getContents().toLowerCase();
        if (text.matches("(?s).*(이전 지시.*무시|시스템 프롬프트|주민등록번호|카드번호).*"))
            throw new IllegalArgumentException("SafeGuardAdvisor가 요청을 차단했습니다.");
        return chain.nextCall(request);
    }
    @Override public String getName() { return "SafeGuardAdvisor"; }
    @Override public int getOrder() { return 100; }
}
