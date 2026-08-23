package com.example.day2.lab3.repository;

import com.example.day2.lab3.model.Order;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository("lab3OrderRepository")
public class OrderRepository {
    private final Map<String, Order> orders = Map.of(
            "12345", new Order("12345", "user1", "배송 중", "서울 물류센터", "무선 이어폰"),
            "99999", new Order("99999", "user2", "결제 완료", "출고 준비 중", "노트북 파우치"));
    public Optional<Order> findByIdAndOwnerId(String id, String ownerId) {
        return Optional.ofNullable(orders.get(id)).filter(order -> order.ownerId().equals(ownerId));
    }
}
