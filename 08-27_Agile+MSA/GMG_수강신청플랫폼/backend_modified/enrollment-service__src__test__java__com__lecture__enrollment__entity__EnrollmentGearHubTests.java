package com.lecture.enrollment.entity;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class EnrollmentGearHubTests {

    @Test
    void pendingLoanCanBeApproved() {
        Enrollment enrollment = pendingLoan();

        enrollment.activate();

        assertThat(enrollment.getStatus()).isEqualTo(Enrollment.Status.ACTIVE);
    }

    @Test
    void rejectedLoanStoresReasonAndCannotBeApproved() {
        Enrollment enrollment = pendingLoan();
        enrollment.reject("프로젝트 목적이 불명확합니다");

        assertThat(enrollment.getStatus()).isEqualTo(Enrollment.Status.REJECTED);
        assertThat(enrollment.getReviewComment()).contains("불명확");
        assertThatThrownBy(enrollment::activate).isInstanceOf(IllegalStateException.class);
    }

    private Enrollment pendingLoan() {
        return Enrollment.builder()
                .userId(2L)
                .courseId(3L)
                .requestType(Enrollment.RequestType.LOAN)
                .reason("모바일 앱 테스트")
                .build();
    }
}
