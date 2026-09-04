package com.lecture.payment.repository;

import com.lecture.payment.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PaymentRepository extends JpaRepository<Payment, Long> {

    List<Payment> findByUserId(Long userId);

    List<Payment> findByStatus(Payment.Status status);

    List<Payment> findByGroupId(Long groupId);

    List<Payment> findByStatusAndGroupId(Payment.Status status, Long groupId);

    Optional<Payment> findByUserIdAndCourseId(Long userId, Long courseId);

    Optional<Payment> findByTransactionId(String transactionId);
}
