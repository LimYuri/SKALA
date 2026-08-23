package com.skala.helpdesk.tools;

import com.skala.helpdesk.config.HelpDeskProperties;
import com.skala.helpdesk.repository.OrderRepository;
import com.skala.helpdesk.repository.TicketRepository;
import com.skala.helpdesk.repository.TicketRepository.TicketType;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class TicketTools {
    private final OrderRepository orders;
    private final TicketRepository tickets;
    private final MeterRegistry meters;
    private final int maxCalls;
    public TicketTools(OrderRepository orders, TicketRepository tickets,
                       MeterRegistry meters, HelpDeskProperties props) {
        this.orders = orders; this.tickets = tickets; this.meters = meters;
        this.maxCalls = props.safety().maxToolCalls();
    }
    // 모델이 바로 교환/환불을 확정 처리하면 안 되니, 여기서는 PENDING 티켓만 만들고
    // 실제 승인은 AdminController의 관리자 API에서만 가능하게 분리해둠
    @Tool(description = "현재 사용자의 주문에 교환 또는 환불 티켓을 접수할 때 사용한다. 실제 처리는 담당자 승인 후 진행된다.")
    public String createTicket(@ToolParam(description = "주문번호. 예: 12345") String orderId,
                               @ToolParam(description = "EXCHANGE 또는 REFUND") String type,
                               @ToolParam(description = "접수 사유") String reason,
                               ToolContext context) {
        ToolGuard.called(context, "createTicket", maxCalls);
        String userId = ToolGuard.user(context);
        // 남의 주문번호로 티켓을 만들지 못하게 소유자 확인부터
        if (orders.findOwned(orderId, userId).isEmpty()) {
            String denied = "해당 주문을 찾을 수 없어 티켓을 접수하지 않았습니다.";
            meters.counter("ai.tool.calls", "tool", "createTicket", "result", "denied").increment();
            return denied;
        }
        TicketType ticketType = TicketType.valueOf(type.toUpperCase());
        var ticket = tickets.request(orderId, userId, ticketType, reason);
        String result = "티켓 %s를 접수했습니다. 상태 PENDING이며 담당자 승인 후 처리됩니다.".formatted(ticket.no());
        meters.counter("ai.tool.calls", "tool", "createTicket", "result", "pending").increment();
        return result;
    }
}
