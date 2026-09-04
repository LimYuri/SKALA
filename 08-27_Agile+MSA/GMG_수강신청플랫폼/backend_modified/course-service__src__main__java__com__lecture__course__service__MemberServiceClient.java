package com.lecture.course.service;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

@Component
@RequiredArgsConstructor
public class MemberServiceClient {

    private final WebClient.Builder webClientBuilder;

    @Value("${service.member-service.url:http://member-service:8081}")
    private String memberServiceUrl;

    public GroupAccess getGroupAccess(Long groupId, Long userId) {
        try {
            GroupAccess response = webClientBuilder.build()
                    .get()
                    .uri(memberServiceUrl + "/api/users/groups/internal/{groupId}/access/{userId}",
                            groupId, userId)
                    .retrieve()
                    .bodyToMono(GroupAccess.class)
                    .block();
            if (response == null) {
                throw new IllegalStateException("그룹 권한 응답이 비어 있습니다");
            }
            return response;
        } catch (Exception exception) {
            throw new IllegalStateException("그룹 권한을 확인하지 못했습니다", exception);
        }
    }

    public boolean isOrganizationAdmin(Long userId) {
        try {
            UserResponse response = webClientBuilder.build()
                    .get()
                    .uri(memberServiceUrl + "/api/users/internal/{userId}", userId)
                    .retrieve()
                    .bodyToMono(UserResponse.class)
                    .block();
            return response != null && "INSTRUCTOR".equals(response.getRole());
        } catch (Exception exception) {
            throw new IllegalStateException("사용자 권한을 확인하지 못했습니다", exception);
        }
    }

    @Getter
    @NoArgsConstructor
    public static class GroupAccess {
        private Long groupId;
        private Long userId;
        private boolean member;
        private boolean manager;
        private String groupRole;
        private String organizationRole;
    }

    @Getter
    @NoArgsConstructor
    public static class UserResponse {
        private Long id;
        private String role;
    }
}
