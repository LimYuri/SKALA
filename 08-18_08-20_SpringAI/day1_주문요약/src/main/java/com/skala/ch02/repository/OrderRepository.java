package com.skala.ch02.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Repository;

import com.skala.ch02.domain.Order;

@Repository
public class OrderRepository {
    private final List<Order> orders = List.of(
            new Order("12345", "user1", "무선 이어폰", "배송 중", "7월 30일"),
            new Order("12346", "user1", "기계식 키보드", "상품 준비 중", "8월 20일"),
            new Order("12347", "user1", "USB-C 허브", "배송 완료", "8월 17일"),
            new Order("99999", "user2", "스마트 워치", "배송 중", "8월 22일"));

    public Optional<Order> findByIdAndOwnerId(String orderId, String ownerId) {
        return orders.stream()
                .filter(order -> order.getId().equals(orderId)
                        && order.getOwnerId().equals(ownerId))
                .findFirst();
    }
}
