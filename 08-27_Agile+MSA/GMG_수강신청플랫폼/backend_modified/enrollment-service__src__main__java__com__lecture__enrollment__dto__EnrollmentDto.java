package com.lecture.enrollment.dto;

import com.lecture.enrollment.entity.Enrollment;
import jakarta.validation.constraints.FutureOrPresent;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.LocalDate;
import java.util.List;

public class EnrollmentDto {

    // 수강신청 요청
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EnrollRequest {
        @NotNull(message = "강의 ID는 필수입니다")
        private Long courseId;

        @NotNull(message = "그룹 ID는 필수입니다")
        private Long groupId;

        @NotBlank(message = "사용 목적을 입력해 주세요")
        private String reason;

        @NotNull(message = "대여 시작일은 필수입니다")
        @FutureOrPresent(message = "대여 시작일은 오늘 이후여야 합니다")
        private LocalDate requestedFrom;

        @NotNull(message = "반납 예정일은 필수입니다")
        @FutureOrPresent(message = "반납 예정일은 오늘 이후여야 합니다")
        private LocalDate dueDate;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PurchaseRequest {
        @NotBlank(message = "상품명은 필수입니다")
        private String title;

        private String description;

        @NotNull(message = "도입 대상 그룹은 필수입니다")
        private Long groupId;

        @NotBlank(message = "카테고리는 필수입니다")
        private String category;

        @NotNull(message = "단가는 필수입니다")
        @Positive(message = "단가는 0보다 커야 합니다")
        private BigDecimal unitPrice;

        @NotNull(message = "수량은 필수입니다")
        @Positive(message = "수량은 1 이상이어야 합니다")
        private Integer quantity;

        @NotBlank(message = "구매 링크는 필수입니다")
        @Pattern(regexp = "^https?://.+", message = "구매 링크는 http:// 또는 https://로 시작해야 합니다")
        private String purchaseUrl;

        @NotBlank(message = "신청 사유를 입력해 주세요")
        private String reason;

        private Boolean alternativeChecked;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReviewRequest {
        private String reviewComment;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReceiveRequest {
        @Positive(message = "입고 수량은 1 이상이어야 합니다")
        private Integer receivedQuantity;
        private String pickupLocation;
        private String visibility;
    }

    // 강의 요약 정보 (내 수강 목록 표시용)
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class CourseSummary {
        private Long id;
        private String title;
        private String description;
        private String category;
        private BigDecimal price;
        private String thumbnail;
        private String instructorName;
        private Integer enrollmentCount;
        private String itemType;
        private Integer totalQuantity;
        private Integer availableQuantity;
        private String purchaseUrl;
        private Long ownerGroupId;
        private String visibility;
        private String pickupLocation;
        private Integer maxLoanDays;
    }

    // 수강 응답
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EnrollmentResponse {
        private Long id;
        private Long userId;
        private Long courseId;
        private Long groupId;
        private Enrollment.RequestType requestType;
        private String reason;
        private String reviewComment;
        private Enrollment.Status status;
        private LocalDate requestedFrom;
        private LocalDate dueDate;
        private LocalDateTime approvedAt;
        private LocalDateTime returnedAt;
        private Long reviewedBy;
        private boolean overdue;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;

        // 추가
        private CourseSummary course;

        public static EnrollmentResponse from(Enrollment enrollment) {
            return EnrollmentResponse.builder()
                    .id(enrollment.getId())
                    .userId(enrollment.getUserId())
                    .courseId(enrollment.getCourseId())
                    .groupId(enrollment.getGroupId())
                    .requestType(enrollment.getRequestType())
                    .reason(enrollment.getReason())
                    .reviewComment(enrollment.getReviewComment())
                    .status(enrollment.getStatus())
                    .requestedFrom(enrollment.getRequestedFrom())
                    .dueDate(enrollment.getDueDate())
                    .approvedAt(enrollment.getApprovedAt())
                    .returnedAt(enrollment.getReturnedAt())
                    .reviewedBy(enrollment.getReviewedBy())
                    .overdue(enrollment.isOverdue(LocalDate.now()))
                    .createdAt(enrollment.getCreatedAt())
                    .updatedAt(enrollment.getUpdatedAt())
                    .build();
        }

        public static EnrollmentResponse from(Enrollment enrollment, CourseSummary course) {
            return EnrollmentResponse.builder()
                    .id(enrollment.getId())
                    .userId(enrollment.getUserId())
                    .courseId(enrollment.getCourseId())
                    .groupId(enrollment.getGroupId())
                    .requestType(enrollment.getRequestType())
                    .reason(enrollment.getReason())
                    .reviewComment(enrollment.getReviewComment())
                    .status(enrollment.getStatus())
                    .requestedFrom(enrollment.getRequestedFrom())
                    .dueDate(enrollment.getDueDate())
                    .approvedAt(enrollment.getApprovedAt())
                    .returnedAt(enrollment.getReturnedAt())
                    .reviewedBy(enrollment.getReviewedBy())
                    .overdue(enrollment.isOverdue(LocalDate.now()))
                    .createdAt(enrollment.getCreatedAt())
                    .updatedAt(enrollment.getUpdatedAt())
                    .course(course)
                    .build();
        }
    }

    // 추천 서비스용: 수강 이력 조회 응답
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class EnrollmentHistoryResponse {
        private Long userId;
        private List<Long> activeCourseIds;
    }

    // 공통 API 응답 래퍼
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ApiResponse<T> {
        private boolean success;
        private String message;
        private T data;

        public static <T> ApiResponse<T> success(T data) {
            return ApiResponse.<T>builder()
                    .success(true)
                    .message("성공")
                    .data(data)
                    .build();
        }

        public static <T> ApiResponse<T> error(String message) {
            return ApiResponse.<T>builder()
                    .success(false)
                    .message(message)
                    .build();
        }
    }
}
