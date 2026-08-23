package com.skala.day1.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

import com.skala.ch02.domain.Order;
import com.skala.ch02.domain.OrderNotFoundException;
import com.skala.ch02.repository.OrderRepository;

import io.swagger.v3.oas.annotations.media.Schema;

@Service
public class OrderSummaryService {
    private static final Logger log = LoggerFactory.getLogger(OrderSummaryService.class);

    private final OrderRepository orders;
    private final ChatClient summaryChat;

    public OrderSummaryService(OrderRepository orders, ChatClient summaryChatClient) {
        this.orders = orders;
        this.summaryChat = summaryChatClient;
    }

    public SummaryResponse summarize(String orderId, String userId) {
        Order order = orders.findByIdAndOwnerId(orderId, userId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));

        String summary;
        try {
            summary = summaryChat.prompt()
                    .user(user -> user.text(
                            "주문번호 {id} · 상품 {item} · 상태 {status} · 도착예정 {eta}\n위 정보를 한 문장으로 요약해 줘.")
                            .param("id", order.getId())
                            .param("item", order.getItem())
                            .param("status", order.getStatus())
                            .param("eta", order.getEta()))
                    .call()
                    .content();
        } catch (Exception exception) {
            log.warn("AI 요약 실패 - 주문 정보로 fallback: {}", orderId,
                    exception);
            summary = order.getItem() + " · " + order.getStatus()
                    + " · " + order.getEta() + " 도착 예정";
        }

        return new SummaryResponse(order.getId(), summary);
    }

    public record SummaryResponse(
            @Schema(example = "12345") String orderId,
            @Schema(example = "무선 이어폰이 배송 중이며 7월 30일 도착 예정입니다.")
            String summary) {}
}
