package com.lecture.enrollment.service;

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

    public void assertMember(Long groupId, Long userId) {
        if (!getGroupAccess(groupId, userId).isMember()) {
            throw new IllegalStateException("이 그룹에 접근할 권한이 없습니다");
        }
    }

    public void assertManager(Long groupId, Long userId) {
        if (!getGroupAccess(groupId, userId).isManager()) {
            throw new IllegalStateException("그룹 관리자 권한이 필요합니다");
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
}
