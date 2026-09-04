package com.lecture.course.dto;

import com.lecture.course.entity.Course;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public class CourseDto {

    // 강의 등록 요청
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class CreateRequest {

        @NotBlank(message = "강의 제목은 필수입니다")
        private String title;

        private String description;

        @NotNull(message = "카테고리는 필수입니다")
        private Course.Category category;

        @NotNull(message = "가격은 필수입니다")
        @PositiveOrZero(message = "가격은 0 이상이어야 합니다")
        private BigDecimal price;

        private Course.ItemType itemType;

        @Positive(message = "수량은 1 이상이어야 합니다")
        private Integer totalQuantity;

        @Pattern(regexp = "^https?://.+", message = "구매 링크는 http:// 또는 https://로 시작해야 합니다")
        private String purchaseUrl;

        private Long ownerGroupId;

        private Course.Visibility visibility;

        private String pickupLocation;

        @Min(value = 1, message = "최대 대여일은 1일 이상이어야 합니다")
        @Max(value = 60, message = "최대 대여일은 60일 이하여야 합니다")
        private Integer maxLoanDays;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class InternalAcquisitionRequest {
        @NotBlank(message = "장비 이름은 필수입니다")
        private String title;
        private String description;
        @NotNull(message = "카테고리는 필수입니다")
        private Course.Category category;
        @NotNull(message = "예상 단가는 필수입니다")
        @PositiveOrZero(message = "예상 단가는 0 이상이어야 합니다")
        private BigDecimal price;
        @Positive(message = "수량은 1 이상이어야 합니다")
        private Integer totalQuantity;
        private String purchaseUrl;
        @NotNull(message = "도입 대상 그룹은 필수입니다")
        private Long ownerGroupId;
        @NotNull(message = "요청자 ID는 필수입니다")
        private Long requestedBy;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReceiveRequest {
        @Positive(message = "입고 수량은 1 이상이어야 합니다")
        private Integer receivedQuantity;
        private String pickupLocation;
        private Course.Visibility visibility;
    }

    // 강의 응답
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class CourseResponse {
        private Long id;
        private String title;
        private String description;
        private Course.Category category;
        private BigDecimal price;
        private Course.ItemType itemType;
        private Integer totalQuantity;
        private Integer availableQuantity;
        private String purchaseUrl;
        private Long ownerGroupId;
        private Course.Visibility visibility;
        private String pickupLocation;
        private Integer maxLoanDays;
        private Long instructorId;
        private Integer enrollmentCount;
        private Course.Status status;
        private LocalDateTime createdAt;

        public static CourseResponse from(Course course) {
            return CourseResponse.builder()
                    .id(course.getId())
                    .title(course.getTitle())
                    .description(course.getDescription())
                    .category(course.getCategory())
                    .price(course.getPrice())
                    .itemType(course.getItemType())
                    .totalQuantity(course.getTotalQuantity())
                    .availableQuantity(course.getAvailableQuantity())
                    .purchaseUrl(course.getPurchaseUrl())
                    .ownerGroupId(course.getOwnerGroupId())
                    .visibility(course.getVisibility())
                    .pickupLocation(course.getPickupLocation())
                    .maxLoanDays(course.getMaxLoanDays())
                    .instructorId(course.getInstructorId())
                    .enrollmentCount(course.getEnrollmentCount())
                    .status(course.getStatus())
                    .createdAt(course.getCreatedAt())
                    .build();
        }
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

    // 추천 서비스용 응답 (카테고리 기반 미수강 강의 목록)
    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class RecommendResponse {
        private List<CourseResponse> courses;
        private Course.Category category;
    }
}
