package com.lecture.enrollment.service;

import com.lecture.enrollment.dto.EnrollmentDto;
import com.lecture.enrollment.entity.Enrollment;
import com.lecture.enrollment.kafka.EnrollmentKafkaProducer;
import com.lecture.enrollment.kafka.KafkaEvent;
import com.lecture.enrollment.repository.EnrollmentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class EnrollmentService {

    private static final List<Enrollment.Status> OPEN_LOAN_STATUSES = List.of(
            Enrollment.Status.PENDING,
            Enrollment.Status.ACTIVE,
            Enrollment.Status.RETURN_REQUESTED
    );

    private final EnrollmentRepository enrollmentRepository;
    private final CourseServiceClient courseServiceClient;
    private final PaymentServiceClient paymentServiceClient;
    private final MemberServiceClient memberServiceClient;
    private final EnrollmentKafkaProducer kafkaProducer;
    private final EnrollmentWriteService enrollmentWriteService;

    @Transactional
    public EnrollmentDto.EnrollmentResponse enroll(
            Long userId,
            EnrollmentDto.EnrollRequest request) {
        memberServiceClient.assertMember(request.getGroupId(), userId);

        if (!courseServiceClient.existsCourse(request.getCourseId())) {
            throw new IllegalArgumentException("존재하지 않는 자산입니다: " + request.getCourseId());
        }

        Map<String, Object> courseInfo = courseServiceClient.getCourse(request.getCourseId());
        validateBorrowableAsset(request, courseInfo);

        if (enrollmentRepository.existsByUserIdAndCourseIdAndStatusIn(
                userId, request.getCourseId(), OPEN_LOAN_STATUSES)) {
            throw new IllegalArgumentException("이미 신청했거나 대여 중인 자산입니다");
        }

        Enrollment enrollment = enrollmentWriteService.createPendingEnrollment(
                userId,
                request.getCourseId(),
                request.getGroupId(),
                Enrollment.RequestType.LOAN,
                request.getReason(),
                request.getRequestedFrom(),
                request.getDueDate()
        );

        publishLifecycle("REQUESTED", enrollment, courseInfo);
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse requestAcquisition(
            Long userId,
            EnrollmentDto.PurchaseRequest request) {
        memberServiceClient.assertMember(request.getGroupId(), userId);

        Map<String, Object> courseInfo = courseServiceClient.createPurchaseCourse(userId, request);
        Long courseId = toLong(courseInfo.get("id"));

        Enrollment enrollment = enrollmentWriteService.createPendingEnrollment(
                userId,
                courseId,
                request.getGroupId(),
                Enrollment.RequestType.PURCHASE,
                request.getReason(),
                null,
                null
        );

        log.info("[EnrollmentService] 미보유 장비 도입 요청 - requestId: {}, groupId: {}",
                enrollment.getId(), request.getGroupId());
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse approveLoan(Long enrollmentId, Long reviewerId) {
        Enrollment enrollment = findEnrollment(enrollmentId);
        assertType(enrollment, Enrollment.RequestType.LOAN);
        memberServiceClient.assertManager(enrollment.getGroupId(), reviewerId);

        if (enrollment.getStatus() == Enrollment.Status.ACTIVE) {
            return toResponseWithCourse(enrollment);
        }

        Map<String, Object> courseInfo = courseServiceClient.getCourse(enrollment.getCourseId());
        courseServiceClient.borrowCourse(enrollment.getCourseId());
        enrollment.activate(reviewerId);
        publishCompleted(enrollment);
        publishLifecycle("APPROVED", enrollment, courseInfo);
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse rejectRequest(
            Long enrollmentId,
            Long reviewerId,
            String reviewComment) {
        if (reviewComment == null || reviewComment.isBlank()) {
            throw new IllegalArgumentException("반려 사유를 입력해 주세요");
        }

        Enrollment enrollment = findEnrollment(enrollmentId);
        memberServiceClient.assertManager(enrollment.getGroupId(), reviewerId);
        enrollment.reject(reviewComment.trim());

        if (enrollment.getRequestType() == Enrollment.RequestType.LOAN) {
            publishLifecycle("REJECTED", enrollment, courseServiceClient.getCourse(enrollment.getCourseId()));
        }
        return toResponseWithCourse(enrollment);
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse approveAcquisition(
            Long enrollmentId,
            Long reviewerId) {
        Enrollment enrollment = findEnrollment(enrollmentId);
        assertType(enrollment, Enrollment.RequestType.PURCHASE);
        memberServiceClient.assertManager(enrollment.getGroupId(), reviewerId);

        if (enrollment.getStatus() == Enrollment.Status.GROUP_APPROVED) {
            return toResponseWithCourse(enrollment);
        }

        Map<String, Object> courseInfo = courseServiceClient.getCourse(enrollment.getCourseId());
        enrollment.approveGroup(reviewerId);

        BigDecimal amount = toBigDecimal(courseInfo.get("price"))
                .multiply(BigDecimal.valueOf(toInteger(courseInfo.get("totalQuantity"))));
        paymentServiceClient.requestPayment(
                enrollment.getUserId(),
                enrollment.getCourseId(),
                enrollment.getId(),
                enrollment.getGroupId(),
                amount
        );
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse requestReturn(Long enrollmentId, Long userId) {
        Enrollment enrollment = findEnrollment(enrollmentId);
        assertType(enrollment, Enrollment.RequestType.LOAN);
        if (!enrollment.getUserId().equals(userId)) {
            throw new IllegalStateException("본인의 대여 건만 반납 요청할 수 있습니다");
        }
        enrollment.requestReturn();
        Map<String, Object> courseInfo = courseServiceClient.getCourse(enrollment.getCourseId());
        publishLifecycle("RETURN_REQUESTED", enrollment, courseInfo);
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse confirmReturn(
            Long enrollmentId,
            Long reviewerId) {
        Enrollment enrollment = findEnrollment(enrollmentId);
        assertType(enrollment, Enrollment.RequestType.LOAN);
        memberServiceClient.assertManager(enrollment.getGroupId(), reviewerId);

        Map<String, Object> courseInfo = courseServiceClient.getCourse(enrollment.getCourseId());
        courseServiceClient.returnCourse(enrollment.getCourseId());
        enrollment.completeReturn(reviewerId);
        publishLifecycle("RETURNED", enrollment, courseInfo);
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public EnrollmentDto.EnrollmentResponse receiveAcquisition(
            Long enrollmentId,
            Long reviewerId,
            EnrollmentDto.ReceiveRequest request) {
        Enrollment enrollment = findEnrollment(enrollmentId);
        assertType(enrollment, Enrollment.RequestType.PURCHASE);
        memberServiceClient.assertManager(enrollment.getGroupId(), reviewerId);

        Map<String, Object> courseInfo = courseServiceClient.receiveCourse(
                enrollment.getCourseId(), request);
        enrollment.markReceived(reviewerId);
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    @Transactional
    public void handleBudgetReview(
            Long requestId,
            Long userId,
            Long courseId,
            String status) {
        Enrollment enrollment = requestId != null
                ? findEnrollment(requestId)
                : enrollmentRepository
                        .findFirstByUserIdAndCourseIdAndRequestTypeOrderByCreatedAtDesc(
                                userId, courseId, Enrollment.RequestType.PURCHASE)
                        .orElseThrow(() -> new IllegalArgumentException("도입 요청 정보를 찾을 수 없습니다"));

        assertType(enrollment, Enrollment.RequestType.PURCHASE);
        if ("COMPLETED".equals(status)) {
            if (enrollment.getStatus() != Enrollment.Status.BUDGET_APPROVED) {
                enrollment.approveBudget();
            }
            log.info("[EnrollmentService] 도입 예산 승인 - requestId: {}", enrollment.getId());
            return;
        }

        if ("FAILED".equals(status) && enrollment.getStatus() != Enrollment.Status.REJECTED) {
            enrollment.reject("학교 예산 검토에서 반려되었습니다");
            log.info("[EnrollmentService] 도입 예산 반려 - requestId: {}", enrollment.getId());
        }
    }

    public List<EnrollmentDto.EnrollmentResponse> getEnrollmentsByUser(
            Long userId,
            Long groupId) {
        List<Enrollment> enrollments = groupId == null
                ? enrollmentRepository.findByUserId(userId)
                : enrollmentRepository.findByUserIdAndGroupId(userId, groupId);
        return enrollments.stream().map(this::toResponseWithCourse).toList();
    }

    public List<EnrollmentDto.EnrollmentResponse> getGroupRequests(
            Long groupId,
            Enrollment.RequestType requestType,
            Enrollment.Status status,
            Long requesterId) {
        memberServiceClient.assertManager(groupId, requesterId);
        return enrollmentRepository
                .findByGroupIdAndRequestTypeAndStatusOrderByCreatedAtDesc(
                        groupId, requestType, status)
                .stream()
                .map(this::toResponseWithCourse)
                .toList();
    }

    public EnrollmentDto.EnrollmentHistoryResponse getEnrollmentHistory(Long userId) {
        List<Long> activeCourseIds = enrollmentRepository
                .findByUserIdAndStatus(userId, Enrollment.Status.ACTIVE)
                .stream()
                .filter(enrollment -> enrollment.getRequestType() == Enrollment.RequestType.LOAN)
                .map(Enrollment::getCourseId)
                .toList();

        return EnrollmentDto.EnrollmentHistoryResponse.builder()
                .userId(userId)
                .activeCourseIds(activeCourseIds)
                .build();
    }

    private void validateBorrowableAsset(
            EnrollmentDto.EnrollRequest request,
            Map<String, Object> courseInfo) {
        if (!"OWNED".equals(stringValue(courseInfo.get("itemType")))
                || !"ACTIVE".equals(stringValue(courseInfo.get("status")))) {
            throw new IllegalArgumentException("대여할 수 있는 자산이 아닙니다");
        }
        if (toInteger(courseInfo.get("availableQuantity")) <= 0) {
            throw new IllegalStateException("현재 대여 가능한 수량이 없습니다");
        }

        String visibility = stringValue(courseInfo.get("visibility"));
        Long ownerGroupId = toLong(courseInfo.get("ownerGroupId"));
        if ("GROUP".equals(visibility) && !request.getGroupId().equals(ownerGroupId)) {
            throw new IllegalStateException("다른 그룹의 전용 자산은 대여할 수 없습니다");
        }

        if (request.getDueDate().isBefore(request.getRequestedFrom())) {
            throw new IllegalArgumentException("반납 예정일은 대여 시작일 이후여야 합니다");
        }
        long loanDays = ChronoUnit.DAYS.between(request.getRequestedFrom(), request.getDueDate()) + 1;
        int maxLoanDays = Math.max(1, toInteger(courseInfo.get("maxLoanDays")));
        if (loanDays > maxLoanDays) {
            throw new IllegalArgumentException("이 자산은 최대 " + maxLoanDays + "일까지 대여할 수 있습니다");
        }
    }

    private EnrollmentDto.EnrollmentResponse toResponseWithCourse(Enrollment enrollment) {
        Map<String, Object> courseInfo = courseServiceClient.getCourse(enrollment.getCourseId());
        return EnrollmentDto.EnrollmentResponse.from(enrollment, toCourseSummary(courseInfo));
    }

    private EnrollmentDto.CourseSummary toCourseSummary(Map<String, Object> courseInfo) {
        return EnrollmentDto.CourseSummary.builder()
                .id(toLong(courseInfo.get("id")))
                .title(stringValue(courseInfo.get("title")))
                .description(stringValue(courseInfo.get("description")))
                .category(normalizeCategory(stringValue(courseInfo.get("category"))))
                .price(toBigDecimal(courseInfo.get("price")))
                .thumbnail(stringValue(courseInfo.get("thumbnail")))
                .instructorName(firstNonBlank(
                        stringValue(courseInfo.get("instructorName")),
                        stringValue(courseInfo.get("teacherName")),
                        stringValue(courseInfo.get("instructor_name"))
                ))
                .enrollmentCount(toInteger(courseInfo.get("enrollmentCount")))
                .itemType(stringValue(courseInfo.get("itemType")))
                .totalQuantity(toInteger(courseInfo.get("totalQuantity")))
                .availableQuantity(toInteger(courseInfo.get("availableQuantity")))
                .purchaseUrl(stringValue(courseInfo.get("purchaseUrl")))
                .ownerGroupId(toLong(courseInfo.get("ownerGroupId")))
                .visibility(stringValue(courseInfo.get("visibility")))
                .pickupLocation(stringValue(courseInfo.get("pickupLocation")))
                .maxLoanDays(toInteger(courseInfo.get("maxLoanDays")))
                .build();
    }

    private void publishCompleted(Enrollment enrollment) {
        kafkaProducer.publishEnrollmentCompleted(
                KafkaEvent.EnrollmentCompletedEvent.builder()
                        .enrollmentId(enrollment.getId())
                        .userId(enrollment.getUserId())
                        .courseId(enrollment.getCourseId())
                        .build()
        );
    }

    private void publishLifecycle(
            String eventType,
            Enrollment enrollment,
            Map<String, Object> courseInfo) {
        kafkaProducer.publishRentalLifecycle(KafkaEvent.RentalLifecycleEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType(eventType)
                .occurredAt(LocalDateTime.now())
                .requestId(enrollment.getId())
                .userId(enrollment.getUserId())
                .groupId(enrollment.getGroupId())
                .assetId(enrollment.getCourseId())
                .category(stringValue(courseInfo.get("category")))
                .quantity(1)
                .requestedFrom(enrollment.getRequestedFrom())
                .dueDate(enrollment.getDueDate())
                .returnedAt(enrollment.getReturnedAt())
                .build());
    }

    private Enrollment findEnrollment(Long enrollmentId) {
        return enrollmentRepository.findById(enrollmentId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "신청 정보를 찾을 수 없습니다: " + enrollmentId));
    }

    private void assertType(Enrollment enrollment, Enrollment.RequestType requestType) {
        if (enrollment.getRequestType() != requestType) {
            throw new IllegalArgumentException("요청 유형이 올바르지 않습니다");
        }
    }

    private String normalizeCategory(String category) {
        if (category == null) return null;
        return switch (category) {
            case "DEVICE", "MOBILE" -> "스마트기기";
            case "COMPUTER" -> "컴퓨터";
            case "SERVER_CLOUD", "DEVOPS" -> "서버·클라우드";
            case "ELECTRONICS_IOT" -> "전자·IoT";
            case "MAKER" -> "메이커·공학";
            case "CAMERA_AUDIO" -> "촬영·음향";
            case "PRESENTATION" -> "발표·행사";
            case "ACCESSORY" -> "부속품";
            case "BACKEND" -> "개발장비";
            case "FRONTEND" -> "디자인장비";
            case "DATA_SCIENCE" -> "데이터장비";
            case "SECURITY" -> "보안장비";
            default -> "기타";
        };
    }

    private String stringValue(Object value) {
        return value == null ? null : value.toString();
    }

    private Long toLong(Object value) {
        if (value == null) return null;
        if (value instanceof Number number) return number.longValue();
        return Long.parseLong(value.toString());
    }

    private Integer toInteger(Object value) {
        if (value == null) return 0;
        if (value instanceof Number number) return number.intValue();
        return Integer.parseInt(value.toString());
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value == null) return BigDecimal.ZERO;
        if (value instanceof BigDecimal decimal) return decimal;
        return new BigDecimal(value.toString());
    }

    private String firstNonBlank(String... values) {
        for (String value : values) {
            if (value != null && !value.isBlank()) {
                return value;
            }
        }
        return null;
    }
}
