package com.lecture.user.dto;

import com.lecture.user.entity.CampusGroup;
import com.lecture.user.entity.GroupMembership;
import com.lecture.user.entity.User;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.time.LocalDateTime;

public class GroupDto {

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreateRequest {
        @NotBlank(message = "그룹 이름은 필수입니다")
        private String name;
        private String description;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class JoinRequest {
        @NotBlank(message = "초대코드는 필수입니다")
        private String inviteCode;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChangeRoleRequest {
        @NotNull(message = "그룹 역할은 필수입니다")
        private GroupMembership.Role role;
    }

    @Getter
    @Builder
    public static class GroupResponse {
        private Long id;
        private String name;
        private String slug;
        private String description;
        private String inviteCode;
        private Long createdBy;
        private CampusGroup.Status status;
        private GroupMembership.Role currentRole;
        private LocalDateTime createdAt;

        public static GroupResponse from(CampusGroup group, GroupMembership.Role currentRole) {
            return GroupResponse.builder()
                    .id(group.getId())
                    .name(group.getName())
                    .slug(group.getSlug())
                    .description(group.getDescription())
                    .inviteCode(currentRole == GroupMembership.Role.MANAGER
                            ? group.getInviteCode()
                            : null)
                    .createdBy(group.getCreatedBy())
                    .status(group.getStatus())
                    .currentRole(currentRole)
                    .createdAt(group.getCreatedAt())
                    .build();
        }
    }

    @Getter
    @Builder
    public static class MemberResponse {
        private Long userId;
        private String name;
        private String email;
        private User.Role organizationRole;
        private GroupMembership.Role groupRole;
        private GroupMembership.Status status;

        public static MemberResponse from(User user, GroupMembership membership) {
            return MemberResponse.builder()
                    .userId(user.getId())
                    .name(user.getName())
                    .email(user.getEmail())
                    .organizationRole(user.getRole())
                    .groupRole(membership.getRole())
                    .status(membership.getStatus())
                    .build();
        }
    }

    @Getter
    @Builder
    public static class AccessResponse {
        private Long groupId;
        private Long userId;
        private boolean member;
        private boolean manager;
        private GroupMembership.Role groupRole;
        private User.Role organizationRole;
    }
}
