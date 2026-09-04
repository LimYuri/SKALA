package com.lecture.payment.entity;

import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PaymentGearHubTests {

    @Test
    void pendingBudgetCanBeApproved() {
        Payment payment = pendingBudget();

        payment.complete("BUDGET-12345678");

        assertThat(payment.getStatus()).isEqualTo(Payment.Status.COMPLETED);
        assertThat(payment.getTransactionId()).startsWith("BUDGET-");
    }

    @Test
    void completedBudgetCannotBeRejected() {
        Payment payment = pendingBudget();
        payment.complete("BUDGET-12345678");

        assertThatThrownBy(payment::fail).isInstanceOf(IllegalStateException.class);
    }

    private Payment pendingBudget() {
        return Payment.builder()
                .userId(2L)
                .courseId(3L)
                .amount(BigDecimal.valueOf(250_000))
                .build();
    }
}
