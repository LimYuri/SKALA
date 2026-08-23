package com.example.day2.lab3.model;

import java.time.Instant;

public record RefundTicket(String ticketNo, String orderId, String ownerId, String reason,
                           TicketStatus status, Instant createdAt) {
    public enum TicketStatus { PENDING, APPROVED }
    public RefundTicket approve() {
        return new RefundTicket(ticketNo, orderId, ownerId, reason, TicketStatus.APPROVED, createdAt);
    }
}
