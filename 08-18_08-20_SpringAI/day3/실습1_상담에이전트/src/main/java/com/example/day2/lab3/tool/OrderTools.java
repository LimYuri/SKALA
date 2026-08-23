package com.example.day2.lab3.tool;

import com.example.day2.lab3.audit.AuditService;
import com.example.day2.lab3.model.Order;
import com.example.day2.lab3.model.RefundTicket;
import com.example.day2.lab3.repository.OrderRepository;
import com.example.day2.lab3.repository.RefundTicketRepository;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class OrderTools {
    private final OrderRepository orders;
    private final RefundTicketRepository tickets;
    private final AuditService audit;
    private final MeterRegistry metrics;
    private final int maxToolCalls;
    public OrderTools(OrderRepository orders, RefundTicketRepository tickets, AuditService audit, MeterRegistry metrics) {
        this(orders, tickets, audit, metrics, 3);
    }
    @Autowired
    public OrderTools(OrderRepository orders, RefundTicketRepository tickets, AuditService audit, MeterRegistry metrics,
                      @Value("${lab3.max-tool-calls:3}") int maxToolCalls) {
        this.orders = orders; this.tickets = tickets; this.audit = audit; this.metrics = metrics;
        this.maxToolCalls = maxToolCalls;
    }

    @Tool(description = "현재 로그인한 사용자의 주문 상태와 위치를 조회한다. 사용자가 주문번호를 말하거나 '내 주문', '배송 언제'처럼 물으면 사용한다. 다른 사용자의 주문은 조회하지 않는다.")
    public String getOrder(@ToolParam(description = "조회할 주문번호. 예: 12345") String orderId, ToolContext context) {
        checkCallLimit(context);
        recordToolCall(context, "getOrder");
        String userId = requiredUser(context);
        Order order = orders.findByIdAndOwnerId(orderId, userId).orElse(null);
        String result = order == null ? "해당 주문을 찾을 수 없습니다."
                : "주문 " + order.id() + "의 상태는 " + order.status() + "이며 현재 위치는 " + order.location() + "입니다.";
        audit.record("getOrder", userId, "orderId=" + orderId, result);
        metrics.counter("ai.tool.calls", "tool", "getOrder", "result", order == null ? "denied_or_missing" : "success").increment();
        return result;
    }

    @Tool(description = "현재 로그인한 사용자의 주문에 환불 요청 티켓을 접수한다. 즉시 처리하지 않으며 담당자 승인 전에는 항상 PENDING으로 남긴다.")
    public String requestRefund(@ToolParam(description = "환불 요청할 주문번호. 예: 12345") String orderId,
                                @ToolParam(description = "고객이 말한 환불 사유. 예: 단순 변심") String reason, ToolContext context) {
        checkCallLimit(context);
        recordToolCall(context, "requestRefund");
        String userId = requiredUser(context);
        if (orders.findByIdAndOwnerId(orderId, userId).isEmpty()) {
            String result = "해당 주문을 찾을 수 없어 환불을 접수하지 않았습니다.";
            audit.record("requestRefund", userId, "orderId=" + orderId, result);
            metrics.counter("ai.tool.calls", "tool", "requestRefund", "result", "denied_or_missing").increment();
            return result;
        }
        RefundTicket ticket = tickets.create(orderId, userId, reason);
        String result = "환불 요청이 " + ticket.ticketNo() + "번으로 접수되었습니다. 담당자 승인 후 처리됩니다. 상태: PENDING";
        audit.record("REFUND_REQUESTED", userId, "orderId=" + orderId + ",reason=" + reason, result);
        metrics.counter("ai.tool.calls", "tool", "requestRefund", "result", "pending").increment();
        return result;
    }

    private String requiredUser(ToolContext context) {
        Object user = context.getContext().get("userId");
        if (user == null || user.toString().isBlank()) throw new IllegalArgumentException("인증 사용자 정보가 없습니다.");
        return user.toString();
    }
    private void checkCallLimit(ToolContext context) {
        Object value = context.getContext().get("toolCallCount");
        if (!(value instanceof AtomicInteger counter))
            throw new IllegalArgumentException("도구 호출 계수기가 없습니다.");
        if (counter.incrementAndGet() > maxToolCalls)
            throw new IllegalStateException("요청당 도구 호출 상한 " + maxToolCalls + "회를 초과했습니다.");
    }
    @SuppressWarnings("unchecked")
    private void recordToolCall(ToolContext context, String toolName) {
        Object value = context.getContext().get("toolCalls");
        if (value instanceof List<?> calls) ((List<String>) calls).add(toolName);
    }
}
