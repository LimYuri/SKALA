package com.skala.ch02.web;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.skala.ch02.domain.Order;
import com.skala.ch02.domain.OrderNotFoundException;
import com.skala.ch02.repository.OrderRepository;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

@RestController
@RequestMapping("/ch02/orders")
@Tag(name = "기존 계층 예제 · 주문 조회")
public class OrderController {
    private final OrderRepository orders;

    public OrderController(OrderRepository orders) {
        this.orders = orders;
    }

    @GetMapping("/{orderId}")
    @Operation(summary = "본인 주문 조회", description = "Day 1 실습 전 계층 예제 확인용 API")
    public Order find(@PathVariable String orderId, @RequestParam String userId) {
        return orders.findByIdAndOwnerId(orderId, userId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));
    }
}
