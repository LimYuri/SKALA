package com.lecture.course.service;

import com.lecture.course.dto.CourseDto;
import com.lecture.course.entity.Course;
import com.lecture.course.repository.CourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CourseService {

    private final CourseRepository courseRepository;
    private final MemberServiceClient memberServiceClient;

    @Transactional
    public CourseDto.CourseResponse createCourse(CourseDto.CreateRequest request, Long operatorId) {
        Course.ItemType itemType = request.getItemType() == null
                ? Course.ItemType.OWNED
                : request.getItemType();
        if (itemType != Course.ItemType.OWNED) {
            throw new IllegalArgumentException("미보유 장비 도입 요청은 도입 요청 API를 사용해 주세요");
        }

        Course.Visibility visibility = resolveVisibility(
                request.getVisibility(), request.getOwnerGroupId());
        assertCanManageScope(operatorId, request.getOwnerGroupId(), visibility);

        int totalQuantity = request.getTotalQuantity() == null ? 1 : request.getTotalQuantity();
        int maxLoanDays = request.getMaxLoanDays() == null ? 7 : request.getMaxLoanDays();

        Course course = Course.builder()
                .title(request.getTitle().trim())
                .description(normalize(request.getDescription()))
                .category(request.getCategory())
                .price(request.getPrice())
                .itemType(Course.ItemType.OWNED)
                .totalQuantity(totalQuantity)
                .availableQuantity(totalQuantity)
                .purchaseUrl(normalize(request.getPurchaseUrl()))
                .ownerGroupId(request.getOwnerGroupId())
                .visibility(visibility)
                .pickupLocation(normalize(request.getPickupLocation()))
                .maxLoanDays(maxLoanDays)
                .instructorId(operatorId)
                .status(Course.Status.ACTIVE)
                .build();

        return CourseDto.CourseResponse.from(courseRepository.save(course));
    }

    @Transactional
    public CourseDto.CourseResponse createAcquisitionRequest(
            CourseDto.InternalAcquisitionRequest request) {
        Course course = Course.builder()
                .title(request.getTitle().trim())
                .description(normalize(request.getDescription()))
                .category(request.getCategory())
                .price(request.getPrice())
                .itemType(Course.ItemType.PURCHASE_REQUEST)
                .totalQuantity(request.getTotalQuantity() == null ? 1 : request.getTotalQuantity())
                .availableQuantity(0)
                .purchaseUrl(normalize(request.getPurchaseUrl()))
                .ownerGroupId(request.getOwnerGroupId())
                .visibility(Course.Visibility.GROUP)
                .maxLoanDays(7)
                .instructorId(request.getRequestedBy())
                .status(Course.Status.INACTIVE)
                .build();
        return CourseDto.CourseResponse.from(courseRepository.save(course));
    }

    public CourseDto.CourseResponse getCourse(Long id) {
        return CourseDto.CourseResponse.from(findCourseById(id));
    }

    public CourseDto.CourseResponse getCourseForUser(Long id, Long userId) {
        Course course = findCourseById(id);
        assertCanRead(userId, course);
        return CourseDto.CourseResponse.from(course);
    }

    public List<CourseDto.CourseResponse> getAllCourses(Long userId, Long groupId) {
        if (groupId != null) {
            assertMember(groupId, userId);
        }

        return courseRepository.findByStatus(Course.Status.ACTIVE).stream()
                .filter(course -> course.getItemType() == Course.ItemType.OWNED)
                .filter(course -> course.getVisibility() == Course.Visibility.ORGANIZATION
                        || (groupId != null && groupId.equals(course.getOwnerGroupId())))
                .map(CourseDto.CourseResponse::from)
                .toList();
    }

    public List<CourseDto.CourseResponse> getAllAssetsInternal() {
        return courseRepository.findByStatus(Course.Status.ACTIVE).stream()
                .filter(course -> course.getItemType() == Course.ItemType.OWNED)
                .map(CourseDto.CourseResponse::from)
                .toList();
    }

    public List<CourseDto.CourseResponse> getCoursesByCategory(
            Course.Category category,
            Long userId,
            Long groupId) {
        return getAllCourses(userId, groupId).stream()
                .filter(course -> course.getCategory() == category)
                .toList();
    }

    public boolean existsCourse(Long id) {
        return courseRepository.existsById(id);
    }

    @Transactional
    public void increaseEnrollmentCount(Long courseId) {
        Course course = findCourseForUpdate(courseId);
        course.increaseEnrollmentCount();
    }

    @Transactional
    public void borrowCourse(Long courseId) {
        Course course = findCourseForUpdate(courseId);
        course.borrowOne();
    }

    @Transactional
    public void returnCourse(Long courseId) {
        Course course = findCourseForUpdate(courseId);
        course.returnOne();
    }

    @Transactional
    public CourseDto.CourseResponse receiveCourse(
            Long courseId,
            CourseDto.ReceiveRequest request) {
        Course course = findCourseForUpdate(courseId);
        course.receiveAsOwned(
                request.getReceivedQuantity(),
                request.getPickupLocation(),
                request.getVisibility()
        );
        return CourseDto.CourseResponse.from(course);
    }

    public List<CourseDto.CourseResponse> getRecommendCourses(
            Course.Category category, List<Long> excludeCourseIds) {
        List<Course> courses = excludeCourseIds.isEmpty()
                ? courseRepository.findByCategoryAndStatus(category, Course.Status.ACTIVE)
                : courseRepository.findByCategoryAndStatusAndIdNotIn(
                        category, Course.Status.ACTIVE, excludeCourseIds);

        return courses.stream()
                .filter(course -> course.getItemType() == Course.ItemType.OWNED)
                .filter(course -> course.getAvailableQuantity() != null
                        && course.getAvailableQuantity() > 0)
                .sorted((a, b) -> b.getEnrollmentCount() - a.getEnrollmentCount())
                .map(CourseDto.CourseResponse::from)
                .toList();
    }

    private void assertCanManageScope(
            Long userId,
            Long ownerGroupId,
            Course.Visibility visibility) {
        if (visibility == Course.Visibility.ORGANIZATION) {
            if (!memberServiceClient.isOrganizationAdmin(userId)) {
                throw new IllegalStateException("학교 공용 자산은 학교 관리자만 등록할 수 있습니다");
            }
            return;
        }
        if (ownerGroupId == null) {
            throw new IllegalArgumentException("그룹 전용 자산에는 소유 그룹이 필요합니다");
        }
        MemberServiceClient.GroupAccess access = memberServiceClient.getGroupAccess(ownerGroupId, userId);
        if (!access.isManager()) {
            throw new IllegalStateException("그룹 관리자만 그룹 자산을 등록할 수 있습니다");
        }
    }

    private void assertCanRead(Long userId, Course course) {
        if (course.getVisibility() == Course.Visibility.ORGANIZATION) {
            return;
        }
        if (userId == null || course.getOwnerGroupId() == null) {
            throw new IllegalStateException("이 자산에 접근할 권한이 없습니다");
        }
        assertMember(course.getOwnerGroupId(), userId);
    }

    private void assertMember(Long groupId, Long userId) {
        if (userId == null) {
            throw new IllegalStateException("그룹 자산 조회에는 사용자 정보가 필요합니다");
        }
        if (!memberServiceClient.getGroupAccess(groupId, userId).isMember()) {
            throw new IllegalStateException("이 그룹에 접근할 권한이 없습니다");
        }
    }

    private Course.Visibility resolveVisibility(
            Course.Visibility visibility,
            Long ownerGroupId) {
        if (visibility != null) {
            return visibility;
        }
        return ownerGroupId == null
                ? Course.Visibility.ORGANIZATION
                : Course.Visibility.GROUP;
    }

    private Course findCourseById(Long id) {
        return courseRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("자산을 찾을 수 없습니다: " + id));
    }

    private Course findCourseForUpdate(Long id) {
        return courseRepository.findByIdForUpdate(id)
                .orElseThrow(() -> new IllegalArgumentException("자산을 찾을 수 없습니다: " + id));
    }

    private String normalize(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
