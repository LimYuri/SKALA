package com.lecture.enrollment.kafka;

import com.lecture.enrollment.service.EnrollmentService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class EnrollmentKafkaConsumer {

    private final EnrollmentService enrollmentService;

    /**
     * payment.completed 이벤트 수신
     * → 수강 상태 PENDING → ACTIVE 로 변경
     * → enrollment.completed 이벤트 발행 (→ Recommend Service)
     *
     * budget-service 쪽은 JsonSerializer + type header 미포함으로 이벤트를 발행하므로,
     * 여기서는 특정 DTO 타입으로 바로 받지 않고 Map<String, Object> 로 받아 처리한다.
     */
    @KafkaListener(
            topics = "${kafka.topic.payment-completed}",
            groupId = "${spring.kafka.consumer.group-id}",
            containerFactory = "kafkaListenerContainerFactory"
    )
    public void handlePaymentCompleted(Map<String, Object> event) {
        log.info("[Kafka Consumer] payment.completed raw event 수신: {}", event);

        try {
            Object userIdValue = event.get("userId");
            Object courseIdValue = event.get("courseId");
            Object requestIdValue = event.get("requestId");
            Object statusValue = event.get("status");

            if (userIdValue == null || courseIdValue == null || statusValue == null) {
                throw new IllegalArgumentException("Kafka 이벤트에 userId, courseId 또는 status가 없습니다.");
            }

            Long userId = ((Number) userIdValue).longValue();
            Long courseId = ((Number) courseIdValue).longValue();
            Long requestId = requestIdValue instanceof Number number
                    ? number.longValue()
                    : null;
            String status = statusValue.toString();

            log.info("[Kafka Consumer] payment.completed 파싱 완료 - userId: {}, courseId: {}",
                    userId, courseId);

            enrollmentService.handleBudgetReview(requestId, userId, courseId, status);

            log.info("[Kafka Consumer] 예산 검토 결과 반영 완료 - userId: {}, courseId: {}, status: {}",
                    userId, courseId, status);

        } catch (Exception e) {
            log.error("[Kafka Consumer] 예산 검토 결과 반영 실패 - event: {}, error: {}",
                    event, e.getMessage(), e);
        }
    }
}
