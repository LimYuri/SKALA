package com.skala.helpdesk.tools;

import com.skala.helpdesk.config.HelpDeskProperties;
import com.skala.helpdesk.repository.OrderRepository;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class OrderTools {
    private final OrderRepository orders;
    private final MeterRegistry meters;
    private final int maxCalls;
    public OrderTools(OrderRepository orders, MeterRegistry meters, HelpDeskProperties props) {
        this.orders = orders; this.meters = meters; this.maxCalls = props.safety().maxToolCalls();
    }
    // 다른 사람 주문번호를 넣어도 findOwned가 userId까지 같이 확인해서 걸러줌
    @Tool(description = "주문번호로 현재 로그인 사용자의 배송 상태·위치·예상 도착일을 조회할 때 사용한다.")
    public String orderStatus(@ToolParam(description = "주문번호. 예: 12345") String orderId, ToolContext context) {
        ToolGuard.called(context, "orderStatus", maxCalls);
        String userId = ToolGuard.user(context);
        String result = orders.findOwned(orderId, userId)
                .map(o -> "주문 %s · 상태 %s · 위치 %s · 예상도착 %s".formatted(o.id(), o.status(), o.location(), o.eta()))
                .orElse("해당 주문을 찾을 수 없습니다.");
        meters.counter("ai.tool.calls", "tool", "orderStatus",
                "result", result.contains("찾을 수") ? "denied" : "ok").increment();
        return result;
    }
}
