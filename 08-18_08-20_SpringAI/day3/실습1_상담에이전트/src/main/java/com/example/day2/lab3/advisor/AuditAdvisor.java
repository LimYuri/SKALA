package com.example.day2.lab3.advisor;

import com.example.day2.lab3.audit.AuditService;
import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

public class AuditAdvisor implements CallAdvisor {
    private final AuditService audit;
    public AuditAdvisor(AuditService audit) { this.audit = audit; }
    @Override public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        audit.record("MODEL_REQUEST", "server-context", "chars=" + request.prompt().getContents().length(), "started");
        try {
            ChatClientResponse response = chain.nextCall(request);
            audit.record("MODEL_RESPONSE", "server-context", "", "success");
            return response;
        } catch (RuntimeException exception) {
            audit.record("MODEL_RESPONSE", "server-context", "", "failed:" + exception.getClass().getSimpleName());
            throw exception;
        }
    }
    @Override public String getName() { return "AuditAdvisor"; }
    @Override public int getOrder() { return 0; }
}
