package com.lecture.payment.service;

import com.lecture.payment.dto.PaymentDto;
import com.lecture.payment.entity.Payment;
import com.lecture.payment.kafka.PaymentKafkaProducer;
import com.lecture.payment.repository.PaymentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final PaymentKafkaProducer kafkaProducer;

    /**
     * 기존 결제 요청을 예산 검토 등록으로 재사용한다.
     * 즉시 완료하지 않고 운영진 검토 전까지 PENDING으로 유지한다.
     */
    @Transactional
    public PaymentDto.InternalPaymentResult processInternalPayment(
            PaymentDto.InternalPaymentRequest request) {
        log.info("[PaymentService] 예산 검토 등록 - userId: {}, courseId: {}, amount: {}",
                request.getUserId(), request.getCourseId(), request.getAmount());

        Payment payment = paymentRepository.save(
                Payment.builder()
                        .userId(request.getUserId())
                        .courseId(request.getCourseId())
                        .requestId(request.getRequestId())
                        .groupId(request.getGroupId())
                        .amount(request.getAmount())
                        .build()
        );

        return PaymentDto.InternalPaymentResult.builder()
                .paymentId(payment.getId())
                .status(payment.getStatus().name())
                .build();
    }

    @Transactional
    public PaymentDto.PaymentResponse approveBudget(Long paymentId) {
        Payment payment = findPayment(paymentId);
        if (payment.getStatus() == Payment.Status.COMPLETED) {
            return PaymentDto.PaymentResponse.from(payment);
        }

        String approvalNumber = "BUDGET-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        payment.complete(approvalNumber);
        publishReviewResult(payment);

        log.info("[PaymentService] 예산 승인 - paymentId: {}, approvalNumber: {}",
                payment.getId(), approvalNumber);
        return PaymentDto.PaymentResponse.from(payment);
    }

    @Transactional
    public PaymentDto.PaymentResponse rejectBudget(Long paymentId) {
        Payment payment = findPayment(paymentId);
        if (payment.getStatus() == Payment.Status.FAILED) {
            return PaymentDto.PaymentResponse.from(payment);
        }

        payment.fail();
        publishReviewResult(payment);

        log.info("[PaymentService] 예산 반려 - paymentId: {}", payment.getId());
        return PaymentDto.PaymentResponse.from(payment);
    }

    public PaymentDto.PaymentResponse getPayment(Long id) {
        return PaymentDto.PaymentResponse.from(findPayment(id));
    }

    public List<PaymentDto.PaymentResponse> getPayments(Payment.Status status, Long groupId) {
        List<Payment> payments;
        if (status != null && groupId != null) {
            payments = paymentRepository.findByStatusAndGroupId(status, groupId);
        } else if (status != null) {
            payments = paymentRepository.findByStatus(status);
        } else if (groupId != null) {
            payments = paymentRepository.findByGroupId(groupId);
        } else {
            payments = paymentRepository.findAll();
        }
        return payments.stream()
                .map(PaymentDto.PaymentResponse::from)
                .collect(Collectors.toList());
    }

    public List<PaymentDto.PaymentResponse> getPaymentsByUser(Long userId) {
        return paymentRepository.findByUserId(userId).stream()
                .map(PaymentDto.PaymentResponse::from)
                .collect(Collectors.toList());
    }

    private Payment findPayment(Long id) {
        return paymentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("예산 검토 정보를 찾을 수 없습니다: " + id));
    }

    private void publishReviewResult(Payment payment) {
        kafkaProducer.publishPaymentCompleted(
                PaymentKafkaProducer.PaymentCompletedEvent.builder()
                        .paymentId(payment.getId())
                        .userId(payment.getUserId())
                        .courseId(payment.getCourseId())
                        .requestId(payment.getRequestId())
                        .groupId(payment.getGroupId())
                        .status(payment.getStatus().name())
                        .build()
        );
    }
}
