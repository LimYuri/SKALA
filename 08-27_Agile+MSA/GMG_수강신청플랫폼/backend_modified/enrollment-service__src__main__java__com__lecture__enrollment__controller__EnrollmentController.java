package com.lecture.enrollment.controller;

import com.lecture.enrollment.dto.EnrollmentDto;
import com.lecture.enrollment.entity.Enrollment;
import com.lecture.enrollment.service.EnrollmentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/enrollments")
@RequiredArgsConstructor
public class EnrollmentController {

    private final EnrollmentService enrollmentService;

    @PostMapping
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> enroll(
            @Valid @RequestBody EnrollmentDto.EnrollRequest request,
            @RequestHeader("X-User-Id") Long userId) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(EnrollmentDto.ApiResponse.success(
                        enrollmentService.enroll(userId, request)
                ));
    }

    @PostMapping({"/acquisitions", "/purchases"})
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> requestAcquisition(
            @Valid @RequestBody EnrollmentDto.PurchaseRequest request,
            @RequestHeader("X-User-Id") Long userId) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(EnrollmentDto.ApiResponse.success(
                        enrollmentService.requestAcquisition(userId, request)
                ));
    }

    @GetMapping("/group/{groupId}")
    public ResponseEntity<EnrollmentDto.ApiResponse<List<EnrollmentDto.EnrollmentResponse>>> getGroupRequests(
            @PathVariable Long groupId,
            @RequestParam Enrollment.RequestType requestType,
            @RequestParam Enrollment.Status status,
            @RequestHeader("X-User-Id") Long requesterId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.getGroupRequests(groupId, requestType, status, requesterId)
        ));
    }

    @GetMapping("/pending")
    public ResponseEntity<EnrollmentDto.ApiResponse<List<EnrollmentDto.EnrollmentResponse>>> getPending(
            @RequestParam Enrollment.RequestType requestType,
            @RequestParam Long groupId,
            @RequestHeader("X-User-Id") Long requesterId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.getGroupRequests(
                        groupId,
                        requestType,
                        Enrollment.Status.PENDING,
                        requesterId
                )
        ));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> approveLoan(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long reviewerId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.approveLoan(id, reviewerId)
        ));
    }

    @PostMapping("/{id}/group-approve")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> approveAcquisition(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long reviewerId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.approveAcquisition(id, reviewerId)
        ));
    }

    @PostMapping("/{id}/reject")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> rejectRequest(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long reviewerId,
            @RequestBody EnrollmentDto.ReviewRequest request) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.rejectRequest(id, reviewerId, request.getReviewComment())
        ));
    }

    @PostMapping("/{id}/return-request")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> requestReturn(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long userId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.requestReturn(id, userId)
        ));
    }

    @PostMapping("/{id}/return-confirm")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> confirmReturn(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long reviewerId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.confirmReturn(id, reviewerId)
        ));
    }

    @PostMapping("/{id}/receive")
    public ResponseEntity<EnrollmentDto.ApiResponse<EnrollmentDto.EnrollmentResponse>> receiveAcquisition(
            @PathVariable Long id,
            @RequestHeader("X-User-Id") Long reviewerId,
            @Valid @RequestBody EnrollmentDto.ReceiveRequest request) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.receiveAcquisition(id, reviewerId, request)
        ));
    }

    @GetMapping("/my")
    public ResponseEntity<EnrollmentDto.ApiResponse<List<EnrollmentDto.EnrollmentResponse>>> getMyEnrollments(
            @RequestHeader("X-User-Id") Long userId,
            @RequestParam(required = false) Long groupId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.getEnrollmentsByUser(userId, groupId)
        ));
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<EnrollmentDto.ApiResponse<List<EnrollmentDto.EnrollmentResponse>>> getEnrollments(
            @PathVariable Long userId,
            @RequestParam(required = false) Long groupId) {
        return ResponseEntity.ok(EnrollmentDto.ApiResponse.success(
                enrollmentService.getEnrollmentsByUser(userId, groupId)
        ));
    }

    @GetMapping("/internal/history/{userId}")
    public ResponseEntity<EnrollmentDto.EnrollmentHistoryResponse> getEnrollmentHistory(
            @PathVariable Long userId) {
        return ResponseEntity.ok(enrollmentService.getEnrollmentHistory(userId));
    }
}
