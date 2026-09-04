-- GearHub Campus 초기 스키마
-- 각 서비스는 자신의 테이블을 논리적으로 소유하며 실습 환경에서는 하나의 MariaDB를 공유한다.

CREATE TABLE IF NOT EXISTS users (
    id          BIGINT          NOT NULL AUTO_INCREMENT,
    email       VARCHAR(255)    NOT NULL UNIQUE,
    password    VARCHAR(255)    NOT NULL,
    name        VARCHAR(100)    NOT NULL,
    role        VARCHAR(20)     NOT NULL COMMENT 'STUDENT | INSTRUCTOR',
    created_at  DATETIME(6),
    updated_at  DATETIME(6),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS campus_groups (
    id          BIGINT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(120)    NOT NULL,
    slug        VARCHAR(80)     NOT NULL UNIQUE,
    description VARCHAR(500),
    invite_code VARCHAR(12)     NOT NULL UNIQUE,
    created_by  BIGINT          NOT NULL,
    status      VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    created_at  DATETIME(6),
    updated_at  DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_campus_group_creator (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS group_memberships (
    id          BIGINT          NOT NULL AUTO_INCREMENT,
    group_id    BIGINT          NOT NULL,
    user_id     BIGINT          NOT NULL,
    role        VARCHAR(20)     NOT NULL DEFAULT 'MEMBER' COMMENT 'MEMBER | MANAGER',
    status      VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    created_at  DATETIME(6),
    updated_at  DATETIME(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_group_member (group_id, user_id),
    INDEX idx_membership_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기존 강의 템플릿의 courses 물리 테이블을 자산 카탈로그로 재사용한다.
CREATE TABLE IF NOT EXISTS courses (
    id                  BIGINT          NOT NULL AUTO_INCREMENT,
    title               VARCHAR(255)    NOT NULL,
    description         TEXT,
    category            VARCHAR(50)     NOT NULL,
    price               DECIMAL(10,2)   NOT NULL,
    item_type           VARCHAR(30)     NOT NULL DEFAULT 'OWNED' COMMENT 'OWNED | PURCHASE_REQUEST',
    total_quantity      INT             NOT NULL DEFAULT 1,
    available_quantity  INT             NOT NULL DEFAULT 1,
    purchase_url        VARCHAR(1000),
    owner_group_id      BIGINT,
    visibility          VARCHAR(20)     NOT NULL DEFAULT 'ORGANIZATION' COMMENT 'ORGANIZATION | GROUP',
    pickup_location     VARCHAR(200),
    max_loan_days       INT             NOT NULL DEFAULT 7,
    instructor_id       BIGINT          NOT NULL,
    enrollment_count    INT             NOT NULL DEFAULT 0,
    status              VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    version             BIGINT          NOT NULL DEFAULT 0,
    created_at          DATETIME(6),
    updated_at          DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_asset_group (owner_group_id),
    INDEX idx_asset_scope (visibility, status, item_type),
    FOREIGN KEY (instructor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기존 enrollments 물리 테이블을 대여 및 도입 요청 워크플로로 재사용한다.
CREATE TABLE IF NOT EXISTS enrollments (
    id              BIGINT      NOT NULL AUTO_INCREMENT,
    user_id         BIGINT      NOT NULL,
    course_id       BIGINT      NOT NULL,
    group_id        BIGINT      NOT NULL,
    request_type    VARCHAR(20) NOT NULL DEFAULT 'LOAN' COMMENT 'LOAN | PURCHASE',
    reason          TEXT,
    review_comment  VARCHAR(500),
    requested_from  DATE,
    due_date        DATE,
    approved_at     DATETIME(6),
    returned_at     DATETIME(6),
    reviewed_by     BIGINT,
    status          VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    created_at      DATETIME(6),
    updated_at      DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_request_user (user_id),
    INDEX idx_request_course (course_id),
    INDEX idx_request_group_status (group_id, request_type, status),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기존 payments 물리 테이블은 학교 예산 검토로 재사용한다.
CREATE TABLE IF NOT EXISTS payments (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    user_id         BIGINT          NOT NULL,
    course_id       BIGINT          NOT NULL,
    request_id      BIGINT,
    group_id        BIGINT,
    amount          DECIMAL(10,2)   NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    transaction_id  VARCHAR(255)    UNIQUE COMMENT '예산 승인번호',
    created_at      DATETIME(6),
    updated_at      DATETIME(6),
    PRIMARY KEY (id),
    INDEX idx_budget_group_status (group_id, status),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
