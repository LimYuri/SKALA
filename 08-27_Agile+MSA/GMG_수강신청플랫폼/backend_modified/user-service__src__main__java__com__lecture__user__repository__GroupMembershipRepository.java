package com.lecture.user.repository;

import com.lecture.user.entity.GroupMembership;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface GroupMembershipRepository extends JpaRepository<GroupMembership, Long> {
    Optional<GroupMembership> findByGroupIdAndUserId(Long groupId, Long userId);
    List<GroupMembership> findByUserIdAndStatus(Long userId, GroupMembership.Status status);
    List<GroupMembership> findByGroupIdAndStatusOrderByCreatedAtAsc(Long groupId, GroupMembership.Status status);
}
