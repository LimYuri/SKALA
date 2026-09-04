package com.lecture.course.entity;

import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "courses")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EntityListeners(AuditingEntityListener.class)
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Category category;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    // 기존 Course 모델을 유지하면서 교보재/구매요청 상품만 구분한다.
    @Enumerated(EnumType.STRING)
    @Column(name = "item_type")
    @Builder.Default
    private ItemType itemType = ItemType.OWNED;

    @Column(name = "total_quantity")
    @Builder.Default
    private Integer totalQuantity = 1;

    @Column(name = "available_quantity")
    @Builder.Default
    private Integer availableQuantity = 1;

    @Column(name = "purchase_url", length = 1000)
    private String purchaseUrl;

    @Column(name = "owner_group_id")
    private Long ownerGroupId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private Visibility visibility = Visibility.ORGANIZATION;

    @Column(name = "pickup_location", length = 200)
    private String pickupLocation;

    @Column(name = "max_loan_days", nullable = false)
    @Builder.Default
    private Integer maxLoanDays = 7;

    // 강사 ID (users 테이블 참조 - 직접 JOIN 없이 ID만 보관)
    @Column(nullable = false)
    private Long instructorId;

    // 수강생 수 (추천 서비스 정렬 기준)
    @Column(nullable = false)
    @Builder.Default
    private Integer enrollmentCount = 0;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private Status status = Status.ACTIVE;

    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;

    @Version
    private Long version;

    public enum Category {
        BACKEND, FRONTEND, DEVOPS, DATA_SCIENCE, MOBILE, SECURITY, DATABASE, OTHER,
        DEVICE, COMPUTER, SERVER_CLOUD, ELECTRONICS_IOT, MAKER, CAMERA_AUDIO,
        PRESENTATION, ACCESSORY, ETC
    }

    public enum ItemType {
        OWNED,
        PURCHASE_REQUEST
    }

    public enum Status {
        ACTIVE, INACTIVE
    }

    public enum Visibility {
        ORGANIZATION,
        GROUP
    }

    public void increaseEnrollmentCount() {
        this.enrollmentCount++;
    }

    public void borrowOne() {
        applyGearHubDefaults();
        if (itemType != ItemType.OWNED || status != Status.ACTIVE) {
            throw new IllegalStateException("대여할 수 있는 교보재가 아닙니다");
        }
        if (availableQuantity == null || availableQuantity <= 0) {
            throw new IllegalStateException("현재 대여 가능한 수량이 없습니다");
        }
        this.availableQuantity--;
        this.enrollmentCount++;
    }

    public void returnOne() {
        applyGearHubDefaults();
        if (itemType != ItemType.OWNED || status != Status.ACTIVE) {
            throw new IllegalStateException("반납할 수 있는 자산이 아닙니다");
        }
        if (availableQuantity >= totalQuantity) {
            throw new IllegalStateException("이미 모든 수량이 반납된 자산입니다");
        }
        this.availableQuantity++;
    }

    public void receiveAsOwned(
            Integer receivedQuantity,
            String pickupLocation,
            Visibility visibility) {
        if (itemType != ItemType.PURCHASE_REQUEST || status != Status.INACTIVE) {
            throw new IllegalStateException("입고 대기 중인 장비만 자산으로 전환할 수 있습니다");
        }
        int quantity = receivedQuantity == null ? totalQuantity : receivedQuantity;
        if (quantity <= 0) {
            throw new IllegalArgumentException("입고 수량은 1 이상이어야 합니다");
        }
        this.totalQuantity = quantity;
        this.availableQuantity = quantity;
        this.itemType = ItemType.OWNED;
        this.status = Status.ACTIVE;
        this.visibility = visibility == null ? Visibility.GROUP : visibility;
        if (pickupLocation != null && !pickupLocation.isBlank()) {
            this.pickupLocation = pickupLocation.trim();
        }
    }

    @PrePersist
    @PostLoad
    private void applyGearHubDefaults() {
        if (itemType == null) itemType = ItemType.OWNED;
        if (totalQuantity == null) totalQuantity = 1;
        if (availableQuantity == null) availableQuantity = totalQuantity;
        if (visibility == null) visibility = ownerGroupId == null
                ? Visibility.ORGANIZATION
                : Visibility.GROUP;
        if (maxLoanDays == null || maxLoanDays <= 0) maxLoanDays = 7;
    }
}
