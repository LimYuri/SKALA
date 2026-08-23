package com.skala.helpdesk.advisor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

// 체인에서 제일 먼저(order 0) 실행돼서 요청/응답을 전부 기록함.
// 실패해도 무조건 감사 로그를 남겨야 해서 catch에서도 record 호출 후 다시 던짐
public class AuditAdvisor implements CallAdvisor {
    private final AuditService audit;
    public AuditAdvisor(AuditService audit) { this.audit = audit; }
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        String userId = String.valueOf(request.context().getOrDefault("auditUserId", "server"));
        audit.record("MODEL_REQUEST", userId, "chars=" + request.prompt().getContents().length(), "started");
        try {
            ChatClientResponse response = chain.nextCall(request);
            audit.record("MODEL_RESPONSE", userId, "", "success");
            return response;
        } catch (RuntimeException exception) {
            audit.record("MODEL_RESPONSE", userId, "", "failed:" + exception.getClass().getSimpleName());
            throw exception;
        }
    }
    @Override public String getName() { return "AuditAdvisor"; }
    @Override public int getOrder() { return 0; }
}
