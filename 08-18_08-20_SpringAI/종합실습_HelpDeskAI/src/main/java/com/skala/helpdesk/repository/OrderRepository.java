package com.skala.helpdesk.repository;

import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

// 실제 주문 DB 대신 쓰는 샘플 데이터. user1은 12345, user2는 99999를 소유한 걸로 고정해둠
// (권한 체크 테스트할 때 "다른 사람 주문번호 조회 시도" 시나리오가 이걸로 재현됨)
@Repository
public class OrderRepository {
    private final Map<String, Order> orders = Map.of(
            "12345", new Order("12345", "user1", "배송 중", "서울 물류센터", "2026-08-21"),
            "99999", new Order("99999", "user2", "출고 준비", "물류센터", "2026-08-23"));

    public Optional<Order> findOwned(String orderId, String userId) {
        return Optional.ofNullable(orders.get(orderId)).filter(order -> order.ownerId().equals(userId));
    }

    public record Order(String id, String ownerId, String status, String location, String eta) {}
}
