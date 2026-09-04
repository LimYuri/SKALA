package com.lecture.enrollment.repository;

import com.lecture.enrollment.entity.Enrollment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface EnrollmentRepository extends JpaRepository<Enrollment, Long> {

    List<Enrollment> findByUserId(Long userId);

    List<Enrollment> findByUserIdAndGroupId(Long userId, Long groupId);

    List<Enrollment> findByUserIdAndStatus(Long userId, Enrollment.Status status);

    List<Enrollment> findByStatusAndRequestType(
            Enrollment.Status status,
            Enrollment.RequestType requestType
    );

    List<Enrollment> findByStatusAndRequestTypeAndGroupId(
            Enrollment.Status status,
            Enrollment.RequestType requestType,
            Long groupId
    );

    Optional<Enrollment> findFirstByUserIdAndCourseIdAndRequestTypeOrderByCreatedAtDesc(
            Long userId,
            Long courseId,
            Enrollment.RequestType requestType
    );

    List<Enrollment> findByGroupIdAndRequestTypeAndStatusOrderByCreatedAtDesc(
            Long groupId,
            Enrollment.RequestType requestType,
            Enrollment.Status status
    );

    boolean existsByUserIdAndCourseIdAndStatusIn(
            Long userId,
            Long courseId,
            List<Enrollment.Status> statuses
    );

    // 수강 완료(ACTIVE)된 강의 ID 목록 - 추천 서비스용
    List<Enrollment> findByUserIdAndStatusIn(Long userId, List<Enrollment.Status> statuses);
}
