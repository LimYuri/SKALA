package com.lecture.user.controller;

import com.lecture.user.dto.GroupDto;
import com.lecture.user.dto.UserDto;
import com.lecture.user.service.GroupService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users/groups")
@RequiredArgsConstructor
public class GroupController {

    private final GroupService groupService;

    @PostMapping
    public ResponseEntity<UserDto.ApiResponse<GroupDto.GroupResponse>> create(
            @RequestHeader("X-User-Id") Long userId,
            @Valid @RequestBody GroupDto.CreateRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(UserDto.ApiResponse.success(groupService.create(userId, request)));
    }

    @GetMapping("/my")
    public ResponseEntity<UserDto.ApiResponse<List<GroupDto.GroupResponse>>> getMyGroups(
            @RequestHeader("X-User-Id") Long userId) {
        return ResponseEntity.ok(UserDto.ApiResponse.success(groupService.getMyGroups(userId)));
    }

    @PostMapping("/join")
    public ResponseEntity<UserDto.ApiResponse<GroupDto.GroupResponse>> join(
            @RequestHeader("X-User-Id") Long userId,
            @Valid @RequestBody GroupDto.JoinRequest request) {
        return ResponseEntity.ok(UserDto.ApiResponse.success(groupService.join(userId, request)));
    }

    @GetMapping("/{groupId}")
    public ResponseEntity<UserDto.ApiResponse<GroupDto.GroupResponse>> getGroup(
            @RequestHeader("X-User-Id") Long userId,
            @PathVariable Long groupId) {
        return ResponseEntity.ok(UserDto.ApiResponse.success(groupService.getGroup(userId, groupId)));
    }

    @GetMapping("/{groupId}/members")
    public ResponseEntity<UserDto.ApiResponse<List<GroupDto.MemberResponse>>> getMembers(
            @RequestHeader("X-User-Id") Long userId,
            @PathVariable Long groupId) {
        return ResponseEntity.ok(UserDto.ApiResponse.success(groupService.getMembers(userId, groupId)));
    }

    @PatchMapping("/{groupId}/members/{memberId}/role")
    public ResponseEntity<UserDto.ApiResponse<GroupDto.MemberResponse>> changeRole(
            @RequestHeader("X-User-Id") Long userId,
            @PathVariable Long groupId,
            @PathVariable Long memberId,
            @Valid @RequestBody GroupDto.ChangeRoleRequest request) {
        return ResponseEntity.ok(UserDto.ApiResponse.success(
                groupService.changeMemberRole(userId, groupId, memberId, request)
        ));
    }

    @GetMapping("/internal/{groupId}/access/{userId}")
    public ResponseEntity<GroupDto.AccessResponse> getAccess(
            @PathVariable Long groupId,
            @PathVariable Long userId) {
        return ResponseEntity.ok(groupService.getAccess(groupId, userId));
    }
}
