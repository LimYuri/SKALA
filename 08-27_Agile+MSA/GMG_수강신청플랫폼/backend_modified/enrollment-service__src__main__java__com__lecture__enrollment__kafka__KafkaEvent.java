package com.lecture.enrollment.kafka;

import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * Kafka 이벤트 메시지 DTO
 */
public class KafkaEvent {

    /**
     * Payment Service → Enrollment Service
     * 결제 완료 이벤트 수신
     */
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PaymentCompletedEvent {
        private Long paymentId;
        private Long userId;
        private Long courseId;
        private Long requestId;
        private Long groupId;
        private String status; // COMPLETED
    }

    /**
     * Enrollment Service → Recommend Service
     * 수강 활성화 완료 이벤트 발행
     */
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EnrollmentCompletedEvent {
        private Long enrollmentId;
        private Long userId;
        private Long courseId;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class RentalLifecycleEvent {
        private String eventId;
        private String eventType;
        private LocalDateTime occurredAt;
        private Long requestId;
        private Long userId;
        private Long groupId;
        private Long assetId;
        private String category;
        private Integer quantity;
        private LocalDate requestedFrom;
        private LocalDate dueDate;
        private LocalDateTime returnedAt;
    }
}
