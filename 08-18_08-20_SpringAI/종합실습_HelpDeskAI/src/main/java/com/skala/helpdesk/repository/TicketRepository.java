package com.skala.helpdesk.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Repository;

// 티켓도 인메모리. 재시작하면 초기화되지만 이 과제에서는 흐름(PENDING -> APPROVED)만 보여주면 되니 이 정도로 충분
@Repository
public class TicketRepository {
    private final AtomicInteger sequence = new AtomicInteger(1000); // HD-1001부터 시작
    private final List<Ticket> tickets = new CopyOnWriteArrayList<>();

    public Ticket request(String orderId, String userId, TicketType type, String reason) {
        Ticket ticket = new Ticket("HD-" + sequence.incrementAndGet(), orderId, userId, type,
                reason, TicketStatus.PENDING, Instant.now());
        tickets.add(ticket);
        return ticket;
    }
    public List<Ticket> pending() { return tickets.stream().filter(t -> t.status() == TicketStatus.PENDING).toList(); }
    public Optional<Ticket> approve(String no) {
        for (int i = 0; i < tickets.size(); i++) {
            Ticket old = tickets.get(i);
            if (old.no().equals(no)) {
                Ticket approved = new Ticket(old.no(), old.orderId(), old.userId(), old.type(), old.reason(),
                        TicketStatus.APPROVED, old.createdAt());
                tickets.set(i, approved);
                return Optional.of(approved);
            }
        }
        return Optional.empty();
    }
    public enum TicketType { EXCHANGE, REFUND }
    public enum TicketStatus { PENDING, APPROVED }
    public record Ticket(String no, String orderId, String userId, TicketType type, String reason,
                         TicketStatus status, Instant createdAt) {}
}
