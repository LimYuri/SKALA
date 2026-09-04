package com.lecture.user.entity;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class GroupMembershipTests {

    @Test
    void managerRoleCanBeChangedAndMembershipReactivated() {
        GroupMembership membership = GroupMembership.builder()
                .groupId(1L)
                .userId(2L)
                .role(GroupMembership.Role.MEMBER)
                .status(GroupMembership.Status.INACTIVE)
                .build();

        membership.changeRole(GroupMembership.Role.MANAGER);
        membership.activate();

        assertThat(membership.getRole()).isEqualTo(GroupMembership.Role.MANAGER);
        assertThat(membership.getStatus()).isEqualTo(GroupMembership.Status.ACTIVE);
    }
}
