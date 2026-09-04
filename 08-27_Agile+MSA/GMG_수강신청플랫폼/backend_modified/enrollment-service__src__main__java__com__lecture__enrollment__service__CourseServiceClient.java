package com.lecture.enrollment.service;

import com.lecture.enrollment.dto.EnrollmentDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class CourseServiceClient {

    private final WebClient.Builder webClientBuilder;

    /**
     * Course Service: 강의 존재 여부 확인 (동기 REST)
     */
    public boolean existsCourse(Long courseId) {
        try {
            Boolean exists = webClientBuilder.build()
                    .get()
                    .uri("http://asset-service/api/courses/internal/exists/{id}", courseId)
                    .retrieve()
                    .bodyToMono(Boolean.class)
                    .block();

            return Boolean.TRUE.equals(exists);
        } catch (Exception e) {
            log.error("[CourseServiceClient] 강의 존재 확인 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage());
            throw new RuntimeException("Course Service 연결 실패");
        }
    }

    /**
     * Course Service: 강의 상세 조회
     * - 내 수강 목록 응답에 course 정보를 붙일 때 사용
     * - asset-service 쪽에 GET /api/courses/internal/{id} 엔드포인트가 있어야 함
     */
    public Map<String, Object> getCourse(Long courseId) {
        try {
            Map<String, Object> responseBody = webClientBuilder.build()
                    .get()
                    .uri("http://asset-service/api/courses/internal/{id}", courseId)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();

            if (responseBody == null) {
                throw new RuntimeException("Course Service 응답 본문이 비어 있습니다.");
            }

            log.info("[CourseServiceClient] 강의 상세 조회 성공 - courseId: {}", courseId);
            log.debug("[CourseServiceClient] 강의 상세 응답 - courseId: {}, body: {}", courseId, responseBody);

            /*
             * 응답 형태가 다음 둘 중 하나일 수 있으므로 둘 다 처리
             *
             * 1) 래퍼 응답
             * {
             *   "success": true,
             *   "message": "성공",
             *   "data": { ...course fields... }
             * }
             *
             * 2) 바로 강의 객체 반환
             * {
             *   "id": 1,
             *   "title": "...",
             *   ...
             * }
             */
            Object data = responseBody.get("data");
            if (data instanceof Map<?, ?> dataMap) {
                @SuppressWarnings("unchecked")
                Map<String, Object> courseMap = (Map<String, Object>) dataMap;
                return courseMap;
            }

            return responseBody;
        } catch (Exception e) {
            log.error("[CourseServiceClient] 강의 상세 조회 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage());
            throw new RuntimeException("Course Service 강의 상세 조회 실패");
        }
    }

    /**
     * Course Service: 수강생 수 증가 (수강 활성화 시 호출)
     */
    public void increaseEnrollmentCount(Long courseId) {
        try {
            webClientBuilder.build()
                    .post()
                    .uri("http://asset-service/api/courses/internal/{id}/enrollment-count", courseId)
                    .retrieve()
                    .toBodilessEntity()
                    .block();

            log.info("[CourseServiceClient] 수강생 수 증가 완료 - courseId: {}", courseId);
        } catch (Exception e) {
            log.error("[CourseServiceClient] 수강생 수 증가 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage());
        }
    }

    /**
     * Course Service: 교보재 대여 승인 처리 (가용 수량 차감)
     */
    public void borrowCourse(Long courseId) {
        try {
            webClientBuilder.build()
                    .post()
                    .uri("http://asset-service/api/courses/internal/{id}/borrow", courseId)
                    .retrieve()
                    .toBodilessEntity()
                    .block();

            log.info("[CourseServiceClient] 교보재 재고 차감 완료 - courseId: {}", courseId);
        } catch (Exception e) {
            log.error("[CourseServiceClient] 교보재 재고 차감 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage());
            throw new IllegalStateException("교보재 재고를 확보하지 못했습니다");
        }
    }

    public void returnCourse(Long courseId) {
        try {
            webClientBuilder.build()
                    .post()
                    .uri("http://asset-service/api/courses/internal/{id}/return", courseId)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("[CourseServiceClient] 자산 재고 복구 완료 - courseId: {}", courseId);
        } catch (Exception e) {
            log.error("[CourseServiceClient] 자산 재고 복구 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage(), e);
            throw new IllegalStateException("자산 반납 재고를 복구하지 못했습니다");
        }
    }

    public Map<String, Object> receiveCourse(
            Long courseId,
            EnrollmentDto.ReceiveRequest request) {
        Map<String, Object> body = new HashMap<>();
        body.put("receivedQuantity", request.getReceivedQuantity());
        body.put("pickupLocation", request.getPickupLocation());
        body.put("visibility", request.getVisibility());
        try {
            Map<String, Object> response = webClientBuilder.build()
                    .post()
                    .uri("http://asset-service/api/courses/internal/{id}/receive", courseId)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
            if (response == null) {
                throw new IllegalStateException("입고 처리 응답이 비어 있습니다");
            }
            return response;
        } catch (Exception e) {
            log.error("[CourseServiceClient] 입고 처리 실패 - courseId: {}, error: {}",
                    courseId, e.getMessage(), e);
            throw new IllegalStateException("도입 장비를 자산으로 전환하지 못했습니다");
        }
    }

    /**
     * 신규 구매요청 상품을 비공개 Course로 생성한다.
     * 기존 POST /api/courses 엔드포인트를 그대로 재사용한다.
     */
    public Map<String, Object> createPurchaseCourse(
            Long userId,
            EnrollmentDto.PurchaseRequest request) {
        Map<String, Object> body = new HashMap<>();
        body.put("title", request.getTitle());
        body.put("description", request.getDescription() == null || request.getDescription().isBlank()
                ? request.getReason()
                : request.getDescription());
        body.put("category", request.getCategory());
        body.put("price", request.getUnitPrice());
        body.put("itemType", "PURCHASE_REQUEST");
        body.put("totalQuantity", request.getQuantity());
        body.put("purchaseUrl", request.getPurchaseUrl());
        body.put("ownerGroupId", request.getGroupId());
        body.put("requestedBy", userId);

        try {
            Map<String, Object> responseBody = webClientBuilder.build()
                    .post()
                    .uri("http://asset-service/api/courses/internal/acquisition-requests")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();

            if (responseBody == null) {
                throw new RuntimeException("Course Service 응답 본문이 비어 있습니다.");
            }

            Object data = responseBody.get("data");
            if (data instanceof Map<?, ?> dataMap) {
                @SuppressWarnings("unchecked")
                Map<String, Object> courseMap = (Map<String, Object>) dataMap;
                return courseMap;
            }
            return responseBody;
        } catch (Exception e) {
            log.error("[CourseServiceClient] 구매요청 상품 생성 실패 - userId: {}, error: {}",
                    userId, e.getMessage(), e);
            throw new RuntimeException("구매요청 상품을 등록하지 못했습니다");
        }
    }
}
