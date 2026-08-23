package com.example.day2.lab3.repository;

import com.example.day2.lab3.model.RefundTicket;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Repository;

@Repository
public class RefundTicketRepository {
    private final AtomicInteger sequence = new AtomicInteger(1000);
    private final Map<String, RefundTicket> tickets = new ConcurrentHashMap<>();
    public RefundTicket create(String orderId, String ownerId, String reason) {
        String no = "RF-" + sequence.incrementAndGet();
        RefundTicket ticket = new RefundTicket(no, orderId, ownerId, reason,
                RefundTicket.TicketStatus.PENDING, Instant.now());
        tickets.put(no, ticket);
        return ticket;
    }
    public List<RefundTicket> pending() {
        return tickets.values().stream().filter(t -> t.status() == RefundTicket.TicketStatus.PENDING).toList();
    }
    public Optional<RefundTicket> approve(String no) {
        return Optional.ofNullable(tickets.computeIfPresent(no, (key, old) -> old.approve()));
    }
}
