package com.lecture.user.repository;

import com.lecture.user.entity.CampusGroup;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface CampusGroupRepository extends JpaRepository<CampusGroup, Long> {
    Optional<CampusGroup> findByInviteCodeAndStatus(String inviteCode, CampusGroup.Status status);
    boolean existsBySlug(String slug);
    List<CampusGroup> findByStatusOrderByNameAsc(CampusGroup.Status status);
}
