package com.skala.helpdesk.tools;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.ai.chat.model.ToolContext;

// OrderTools/TicketTools 둘 다 쓰는 공통 로직이라 따로 뺌. package-private이라 tools 패키지 밖에서는 못 씀
final class ToolGuard {
    private ToolGuard() {}
    static String user(ToolContext context) {
        Object value = context.getContext().get("userId");
        if (value == null || value.toString().isBlank()) throw new IllegalArgumentException("인증 사용자가 없습니다.");
        return value.toString();
    }
    // 한 요청 안에서 모델이 툴을 무한히 호출하는 걸 막는 안전장치(maxToolCalls 설정값 초과하면 예외)
    @SuppressWarnings("unchecked")
    static void called(ToolContext context, String toolName, int maxCalls) {
        Object counterValue = context.getContext().get("toolCallCount");
        if (!(counterValue instanceof AtomicInteger counter)) throw new IllegalArgumentException("도구 계수기가 없습니다.");
        if (counter.incrementAndGet() > maxCalls) throw new IllegalStateException("도구 호출 상한을 초과했습니다.");
        Object calls = context.getContext().get("toolCalls");
        if (calls instanceof List<?> list) ((List<String>) list).add(toolName);
    }
}
