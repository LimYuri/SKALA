package com.lecture.payment.controller;

import com.lecture.payment.dto.PaymentDto;
import com.lecture.payment.entity.Payment;
import com.lecture.payment.service.PaymentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/payments")
@RequiredArgsConstructor
public class PaymentController {

    private final PaymentService paymentService;

    /**
     * POST /payments/internal/request - 내부 결제 요청 (Enrollment Service 호출)
     */
    @PostMapping("/internal/request")
    public ResponseEntity<PaymentDto.InternalPaymentResult> processInternalPayment(
            @Valid @RequestBody PaymentDto.InternalPaymentRequest request) {

        PaymentDto.InternalPaymentResult result = paymentService.processInternalPayment(request);
        return ResponseEntity.ok(result);
    }

    /**
     * GET /payments?status=PENDING - 운영진 예산 검토 목록
     */
    @GetMapping
    public ResponseEntity<PaymentDto.ApiResponse<List<PaymentDto.PaymentResponse>>> getPayments(
            @RequestParam(required = false) Payment.Status status,
            @RequestParam(required = false) Long groupId,
            @RequestHeader(value = "X-User-Role", required = false) String userRole) {
        assertOrganizationAdmin(userRole);
        return ResponseEntity.ok(
                PaymentDto.ApiResponse.success(paymentService.getPayments(status, groupId)));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<PaymentDto.ApiResponse<PaymentDto.PaymentResponse>> approveBudget(
            @PathVariable Long id,
            @RequestHeader(value = "X-User-Role", required = false) String userRole) {
        assertOrganizationAdmin(userRole);
        return ResponseEntity.ok(
                PaymentDto.ApiResponse.success(paymentService.approveBudget(id)));
    }

    @PostMapping("/{id}/reject")
    public ResponseEntity<PaymentDto.ApiResponse<PaymentDto.PaymentResponse>> rejectBudget(
            @PathVariable Long id,
            @RequestHeader(value = "X-User-Role", required = false) String userRole) {
        assertOrganizationAdmin(userRole);
        return ResponseEntity.ok(
                PaymentDto.ApiResponse.success(paymentService.rejectBudget(id)));
    }

    /**
     * GET /payments/{id} - 결제 단건 조회
     */
    @GetMapping("/{id}")
    public ResponseEntity<PaymentDto.ApiResponse<PaymentDto.PaymentResponse>> getPayment(
            @PathVariable Long id) {

        return ResponseEntity.ok(
                PaymentDto.ApiResponse.success(paymentService.getPayment(id)));
    }

    /**
     * GET /payments/user/{userId} - 사용자 결제 내역 조회
     */
    @GetMapping("/user/{userId}")
    public ResponseEntity<PaymentDto.ApiResponse<List<PaymentDto.PaymentResponse>>> getPaymentsByUser(
            @PathVariable Long userId) {

        return ResponseEntity.ok(
                PaymentDto.ApiResponse.success(paymentService.getPaymentsByUser(userId)));
    }

    private void assertOrganizationAdmin(String userRole) {
        if (userRole != null && !"INSTRUCTOR".equals(userRole)) {
            throw new IllegalStateException("학교 예산 관리자 권한이 필요합니다");
        }
    }
}
