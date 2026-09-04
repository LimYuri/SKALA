-- 기존 실습 DB 볼륨을 GearHub Campus 스키마로 올리는 비파괴 마이그레이션.
-- MariaDB 11의 IF NOT EXISTS / IF EXISTS 문법을 사용한다.

CREATE TABLE IF NOT EXISTS campus_groups (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(80) NOT NULL UNIQUE,
    description VARCHAR(500),
    invite_code VARCHAR(12) NOT NULL UNIQUE,
    created_by BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME(6),
    updated_at DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_campus_group_creator (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS group_memberships (
    id BIGINT NOT NULL AUTO_INCREMENT,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'MEMBER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME(6),
    updated_at DATETIME(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_group_member (group_id, user_id),
    INDEX idx_membership_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS owner_group_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'ORGANIZATION',
    ADD COLUMN IF NOT EXISTS pickup_location VARCHAR(200) NULL,
    ADD COLUMN IF NOT EXISTS max_loan_days INT NOT NULL DEFAULT 7,
    ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 0;

ALTER TABLE enrollments
    ADD COLUMN IF NOT EXISTS group_id BIGINT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS requested_from DATE NULL,
    ADD COLUMN IF NOT EXISTS due_date DATE NULL,
    ADD COLUMN IF NOT EXISTS approved_at DATETIME(6) NULL,
    ADD COLUMN IF NOT EXISTS returned_at DATETIME(6) NULL,
    ADD COLUMN IF NOT EXISTS reviewed_by BIGINT NULL;

-- 기존 FK가 (user_id, course_id) 유니크 인덱스를 사용 중일 수 있으므로
-- 단일 FK 인덱스를 먼저 만든 뒤 반복 대여를 막던 유니크 인덱스를 제거한다.
CREATE INDEX IF NOT EXISTS idx_request_user ON enrollments (user_id);
CREATE INDEX IF NOT EXISTS idx_request_course ON enrollments (course_id);
DROP INDEX IF EXISTS uq_user_course ON enrollments;
DROP INDEX IF EXISTS UKg1muiskd02x66lpy6fqcj6b9q ON enrollments;

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS request_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS group_id BIGINT NULL;
