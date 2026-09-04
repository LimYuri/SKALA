package com.lecture.enrollment.entity;

import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.time.LocalDate;

@Entity
@Table(name = "enrollments")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EntityListeners(AuditingEntityListener.class)
public class Enrollment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "course_id", nullable = false)
    private Long courseId;

    @Column(name = "group_id", nullable = false)
    private Long groupId;

    @Enumerated(EnumType.STRING)
    @Column(name = "request_type")
    @Builder.Default
    private RequestType requestType = RequestType.LOAN;

    @Column(columnDefinition = "TEXT")
    private String reason;

    @Column(name = "review_comment", length = 500)
    private String reviewComment;

    @Column(name = "requested_from")
    private LocalDate requestedFrom;

    @Column(name = "due_date")
    private LocalDate dueDate;

    @Column(name = "approved_at")
    private LocalDateTime approvedAt;

    @Column(name = "returned_at")
    private LocalDateTime returnedAt;

    @Column(name = "reviewed_by")
    private Long reviewedBy;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private Status status = Status.PENDING;

    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;

    public enum Status {
        PENDING,
        GROUP_APPROVED,
        ACTIVE,
        RETURN_REQUESTED,
        RETURNED,
        BUDGET_APPROVED,
        RECEIVED,
        REJECTED,
        CANCELLED
    }

    public enum RequestType {
        LOAN,
        PURCHASE
    }

    public void activate(Long reviewerId) {
        if (this.status != Status.PENDING) {
            throw new IllegalStateException("대기 중인 신청만 승인할 수 있습니다");
        }
        this.status = Status.ACTIVE;
        this.approvedAt = LocalDateTime.now();
        this.reviewedBy = reviewerId;
    }

    public void activate() {
        activate(null);
    }

    public void approveGroup(Long reviewerId) {
        if (requestType != RequestType.PURCHASE || status != Status.PENDING) {
            throw new IllegalStateException("대기 중인 도입 요청만 그룹 검토할 수 있습니다");
        }
        this.status = Status.GROUP_APPROVED;
        this.approvedAt = LocalDateTime.now();
        this.reviewedBy = reviewerId;
    }

    public void approveBudget() {
        if (requestType != RequestType.PURCHASE || status != Status.GROUP_APPROVED) {
            throw new IllegalStateException("그룹 검토가 끝난 도입 요청만 예산 승인할 수 있습니다");
        }
        this.status = Status.BUDGET_APPROVED;
    }

    public void requestReturn() {
        if (requestType != RequestType.LOAN || status != Status.ACTIVE) {
            throw new IllegalStateException("대여 중인 장비만 반납 요청할 수 있습니다");
        }
        this.status = Status.RETURN_REQUESTED;
    }

    public void completeReturn(Long reviewerId) {
        if (requestType != RequestType.LOAN || status != Status.RETURN_REQUESTED) {
            throw new IllegalStateException("반납 요청 중인 장비만 반납 완료할 수 있습니다");
        }
        this.status = Status.RETURNED;
        this.returnedAt = LocalDateTime.now();
        this.reviewedBy = reviewerId;
    }

    public void markReceived(Long reviewerId) {
        if (requestType != RequestType.PURCHASE || status != Status.BUDGET_APPROVED) {
            throw new IllegalStateException("예산 승인된 도입 요청만 입고 완료할 수 있습니다");
        }
        this.status = Status.RECEIVED;
        this.returnedAt = LocalDateTime.now();
        this.reviewedBy = reviewerId;
    }

    public void reject(String reviewComment) {
        if (this.status != Status.PENDING && this.status != Status.GROUP_APPROVED) {
            throw new IllegalStateException("검토 중인 신청만 반려할 수 있습니다");
        }
        this.status = Status.REJECTED;
        this.reviewComment = reviewComment;
    }

    public void cancel() {
        this.status = Status.CANCELLED;
    }

    public boolean isOverdue(LocalDate today) {
        return requestType == RequestType.LOAN
                && (status == Status.ACTIVE || status == Status.RETURN_REQUESTED)
                && dueDate != null
                && dueDate.isBefore(today);
    }

    @PrePersist
    @PostLoad
    private void applyGearHubDefaults() {
        if (requestType == null) requestType = RequestType.LOAN;
    }
}
