package com.lecture.user.service;

import com.lecture.user.dto.GroupDto;
import com.lecture.user.entity.CampusGroup;
import com.lecture.user.entity.GroupMembership;
import com.lecture.user.entity.User;
import com.lecture.user.repository.CampusGroupRepository;
import com.lecture.user.repository.GroupMembershipRepository;
import com.lecture.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class GroupService {

    private final CampusGroupRepository groupRepository;
    private final GroupMembershipRepository membershipRepository;
    private final UserRepository userRepository;

    @Transactional
    public GroupDto.GroupResponse create(Long userId, GroupDto.CreateRequest request) {
        User creator = findUser(userId);
        if (creator.getRole() != User.Role.INSTRUCTOR) {
            throw new IllegalStateException("학교 관리자만 그룹을 생성할 수 있습니다");
        }

        CampusGroup group = groupRepository.save(CampusGroup.builder()
                .name(request.getName().trim())
                .description(normalize(request.getDescription()))
                .slug(generateUniqueSlug())
                .inviteCode(generateInviteCode())
                .createdBy(userId)
                .build());

        membershipRepository.save(GroupMembership.builder()
                .groupId(group.getId())
                .userId(userId)
                .role(GroupMembership.Role.MANAGER)
                .build());

        return GroupDto.GroupResponse.from(group, GroupMembership.Role.MANAGER);
    }

    public List<GroupDto.GroupResponse> getMyGroups(Long userId) {
        User user = findUser(userId);
        if (user.getRole() == User.Role.INSTRUCTOR) {
            return groupRepository.findByStatusOrderByNameAsc(CampusGroup.Status.ACTIVE).stream()
                    .map(group -> GroupDto.GroupResponse.from(group, GroupMembership.Role.MANAGER))
                    .toList();
        }

        Map<Long, GroupMembership> memberships = membershipRepository
                .findByUserIdAndStatus(userId, GroupMembership.Status.ACTIVE).stream()
                .collect(Collectors.toMap(GroupMembership::getGroupId, Function.identity()));

        return groupRepository.findAllById(memberships.keySet()).stream()
                .filter(group -> group.getStatus() == CampusGroup.Status.ACTIVE)
                .sorted((a, b) -> a.getName().compareToIgnoreCase(b.getName()))
                .map(group -> GroupDto.GroupResponse.from(
                        group,
                        memberships.get(group.getId()).getRole()
                ))
                .toList();
    }

    public GroupDto.GroupResponse getGroup(Long requesterId, Long groupId) {
        GroupDto.AccessResponse access = getAccess(groupId, requesterId);
        if (!access.isMember()) {
            throw new IllegalStateException("이 그룹에 접근할 권한이 없습니다");
        }
        CampusGroup group = findGroup(groupId);
        return GroupDto.GroupResponse.from(group, access.getGroupRole());
    }

    @Transactional
    public GroupDto.GroupResponse join(Long userId, GroupDto.JoinRequest request) {
        findUser(userId);
        String inviteCode = request.getInviteCode().trim().toUpperCase(Locale.ROOT);
        CampusGroup group = groupRepository
                .findByInviteCodeAndStatus(inviteCode, CampusGroup.Status.ACTIVE)
                .orElseThrow(() -> new IllegalArgumentException("유효하지 않은 초대코드입니다"));

        GroupMembership membership = membershipRepository
                .findByGroupIdAndUserId(group.getId(), userId)
                .map(existing -> {
                    existing.activate();
                    return existing;
                })
                .orElseGet(() -> GroupMembership.builder()
                        .groupId(group.getId())
                        .userId(userId)
                        .role(GroupMembership.Role.MEMBER)
                        .build());

        membershipRepository.save(membership);
        return GroupDto.GroupResponse.from(group, membership.getRole());
    }

    public List<GroupDto.MemberResponse> getMembers(Long requesterId, Long groupId) {
        assertManager(groupId, requesterId);
        List<GroupMembership> memberships = membershipRepository
                .findByGroupIdAndStatusOrderByCreatedAtAsc(groupId, GroupMembership.Status.ACTIVE);
        Map<Long, User> users = userRepository.findAllById(
                        memberships.stream().map(GroupMembership::getUserId).toList()
                ).stream()
                .collect(Collectors.toMap(User::getId, Function.identity()));

        return memberships.stream()
                .filter(membership -> users.containsKey(membership.getUserId()))
                .map(membership -> GroupDto.MemberResponse.from(
                        users.get(membership.getUserId()), membership
                ))
                .toList();
    }

    @Transactional
    public GroupDto.MemberResponse changeMemberRole(
            Long requesterId,
            Long groupId,
            Long userId,
            GroupDto.ChangeRoleRequest request) {
        assertManager(groupId, requesterId);
        GroupMembership membership = membershipRepository.findByGroupIdAndUserId(groupId, userId)
                .orElseThrow(() -> new IllegalArgumentException("그룹 구성원을 찾을 수 없습니다"));
        membership.changeRole(request.getRole());
        return GroupDto.MemberResponse.from(findUser(userId), membership);
    }

    public GroupDto.AccessResponse getAccess(Long groupId, Long userId) {
        findGroup(groupId);
        User user = findUser(userId);
        if (user.getRole() == User.Role.INSTRUCTOR) {
            return GroupDto.AccessResponse.builder()
                    .groupId(groupId)
                    .userId(userId)
                    .member(true)
                    .manager(true)
                    .groupRole(GroupMembership.Role.MANAGER)
                    .organizationRole(user.getRole())
                    .build();
        }

        GroupMembership membership = membershipRepository.findByGroupIdAndUserId(groupId, userId)
                .filter(value -> value.getStatus() == GroupMembership.Status.ACTIVE)
                .orElse(null);

        return GroupDto.AccessResponse.builder()
                .groupId(groupId)
                .userId(userId)
                .member(membership != null)
                .manager(membership != null && membership.getRole() == GroupMembership.Role.MANAGER)
                .groupRole(membership == null ? null : membership.getRole())
                .organizationRole(user.getRole())
                .build();
    }

    private void assertManager(Long groupId, Long userId) {
        if (!getAccess(groupId, userId).isManager()) {
            throw new IllegalStateException("그룹 관리자 권한이 필요합니다");
        }
    }

    private CampusGroup findGroup(Long id) {
        return groupRepository.findById(id)
                .filter(group -> group.getStatus() == CampusGroup.Status.ACTIVE)
                .orElseThrow(() -> new IllegalArgumentException("그룹을 찾을 수 없습니다: " + id));
    }

    private User findUser(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + id));
    }

    private String generateUniqueSlug() {
        String slug;
        do {
            slug = "group-" + UUID.randomUUID().toString().substring(0, 8);
        } while (groupRepository.existsBySlug(slug));
        return slug;
    }

    private String generateInviteCode() {
        return UUID.randomUUID().toString()
                .replace("-", "")
                .substring(0, 8)
                .toUpperCase(Locale.ROOT);
    }

    private String normalize(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
