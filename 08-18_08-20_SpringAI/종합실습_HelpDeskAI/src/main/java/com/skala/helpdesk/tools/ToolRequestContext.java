package com.skala.helpdesk.tools;

import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.ai.chat.model.ToolContext;

// 매 요청마다 새 ToolContext를 만들어서 넘겨줌 - toolCallCount를 요청 단위로 새로 시작해야
// 이전 요청의 호출 횟수가 다음 요청에 누적되는 걸 방지할 수 있음
public final class ToolRequestContext {
    private ToolRequestContext() {}
    public static ToolContext create(String userId, List<String> calls) {
        return new ToolContext(Map.of("userId", userId, "toolCalls", calls,
                "toolCallCount", new AtomicInteger()));
    }
}
