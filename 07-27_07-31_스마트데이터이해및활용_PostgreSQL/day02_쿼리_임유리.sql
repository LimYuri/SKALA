-- # 학사관리 시스템 DQL 종합실습문제
-- 수정 이력 1: 문제 3 정렬 조건에서 학생명 2차 정렬을 제거하고 등급 ASC만 남김
-- 수정 이력 2: 문제 2의 COALESCE + CASE WHEN 병기 이유를 주석으로 추가함
-- 수정 이력 3: 문제 3 정렬을 '등급 ASC, 학번, 과목코드'로 보강하여 등급 내 순서를 결정적으로 고정함
--             (요건인 '등급 오름차순'은 1차 정렬로 유지하고, 학번·과목코드는 동점 처리용 tie-breaker)
-- 수정 이력 4: 2학기 데이터 4건을 PDF 안내에 따라 별도 INSERT + ON CONFLICT DO NOTHING 형태로 분리함
-- 작성자: 임유리
-- 데이터베이스: skala_db
-- 스키마: app

-- 실행 안내
-- 1. postgres 데이터베이스에서 CREATE DATABASE skala_db; 를 먼저 실행합니다.
-- 2. DBeaver에서 skala_db 데이터베이스로 접속합니다.
-- 3. 아래 쿼리를 평가 PDF 순서에 맞춰 확인합니다.
-- 4. 더미데이터 INSERT는 PDF 안내에 맞춰 파일 맨 마지막에 작성했습니다.

-- 이미 skala_db를 생성했다면 아래 문장은 다시 실행하지 않습니다.
-- CREATE DATABASE skala_db;

---------------------------------------------------------------------------------------------------------
-- 1. CREATE SCHEMA
---------------------------------------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS app;

---------------------------------------------------------------------------------------------------------
-- 2. CREATE TABLE DDL
---------------------------------------------------------------------------------------------------------

-- majors: 전공 기준정보
CREATE TABLE app.majors (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

-- students: 학생 기본정보
CREATE TABLE app.students (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    major_id INTEGER REFERENCES app.majors(id) ON DELETE SET NULL,
    grade SMALLINT NOT NULL CHECK (grade BETWEEN 1 AND 4),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- courses: 과목 기준정보
CREATE TABLE app.courses (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    credit SMALLINT NOT NULL CHECK (credit BETWEEN 1 AND 6)
);

-- enrollments: 수강신청과 성적
CREATE TABLE app.enrollments (
    student_id BIGINT NOT NULL REFERENCES app.students(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES app.courses(id) ON DELETE CASCADE,
    score NUMERIC(5,2) CHECK (score BETWEEN 0 AND 100),
    enrolled_at DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (student_id, course_id)
);

---------------------------------------------------------------------------------------------------------
-- ## 문제 1. 전체 학생 기본정보 조회
-- 모든 학생의 학번, 학생명, 이메일, 학년을 조회하세요.
-- 조회 컬럼: 학번, 학생명, 이메일, 학년구분
-- 정렬 조건: 학번 기준 오름차순
-- 반드시 사용할 함수: CASE WHEN THEN ELSE END
---------------------------------------------------------------------------------------------------------
-- ## 정답 1. 작성영역

SELECT
    student_no AS 학번,
    name AS 학생명,
    email AS 이메일,
    CASE
        WHEN grade = 1 THEN 'Freshman'
        WHEN grade = 2 THEN 'Sophomore'
        WHEN grade = 3 THEN 'Junior'
        WHEN grade = 4 THEN 'Senior'
        ELSE 'Unknown'
    END AS 학년구분
FROM app.students
ORDER BY student_no;

---------------------------------------------------------------------------------------------------------
-- ## 문제 2. 학생테이블에서 미배정 학과 처리
-- 학생을 조회하되, 학과가 지정되지 않은 학생은 학과명을 '학과 미배정'으로 표시하세요.
-- 조회 컬럼: 학번, 학생명, 학과명
-- 정렬 조건: 학번 기준 오름차순
-- 반드시 사용할 함수: COALESCE(), CASE WHEN THEN ELSE END
---------------------------------------------------------------------------------------------------------
-- ## 정답 2. 작성영역

SELECT
    s.student_no AS 학번,
    s.name AS 학생명,
    -- LEFT JOIN 특성상 COALESCE(m.name, '학과 미배정')만으로 충분하나,
    -- 과제 요건(COALESCE와 CASE WHEN 모두 사용)에 따라 CASE를 병기함
    COALESCE(
        CASE
            WHEN s.major_id IS NULL THEN NULL
            ELSE m.name
        END,
        '학과 미배정'
    ) AS 학과명
FROM app.students s
LEFT JOIN app.majors m
ON s.major_id = m.id
ORDER BY s.student_no;

---------------------------------------------------------------------------------------------------------
-- ## 문제 3. CASE WHEN을 이용한 학점 등급 계산
-- 수강생의 점수를 기준에 따라 등급으로 변환하세요.
-- 조회 컬럼: 학생명, 과목명, 점수, 등급, 수강신청일, 수강연도, 수강월, 학기구분, 오늘날짜, 경과일수
-- 정렬 조건: 등급 오름차순
---------------------------------------------------------------------------------------------------------
-- ## 정답 3. 작성영역

SELECT
    s.name AS 학생명,
    c.name AS 과목명,
    e.score AS 점수,
    CASE
        WHEN e.score IS NULL THEN '미입력'
        WHEN e.score >= 90 THEN 'A'
        WHEN e.score >= 80 THEN 'B'
        WHEN e.score >= 70 THEN 'C'
        WHEN e.score >= 60 THEN 'D'
        ELSE 'F'
    END AS 등급,
    e.enrolled_at AS 수강신청일,
    EXTRACT(YEAR FROM e.enrolled_at) AS 수강연도,
    EXTRACT(MONTH FROM e.enrolled_at) AS 수강월,
    CASE
        WHEN EXTRACT(MONTH FROM e.enrolled_at) BETWEEN 3 AND 8 THEN '1학기'
        ELSE '2학기'
    END AS 학기구분,
    CURRENT_DATE AS 오늘날짜,
    CURRENT_DATE - e.enrolled_at AS 경과일수
FROM app.enrollments e
INNER JOIN app.students s
    ON e.student_id = s.id
INNER JOIN app.courses c
    ON e.course_id = c.id
-- 요건: 등급 오름차순(1차 정렬). 학번·과목코드는 등급이 같을 때 순서를 고정하는 tie-breaker.
-- (2차 정렬을 두지 않으면 같은 등급 안의 행 순서가 실행마다 달라질 수 있어 결과 재현이 보장되지 않음)
ORDER BY
    등급 ASC,
    s.student_no ASC,
    c.course_code ASC;

---------------------------------------------------------------------------------------------------------
-- 3. 테이블별 더미 데이터 입력
-- PDF 안내에 맞춰 더미데이터는 앞선 DDL 및 DQL 작성 영역 아래, 파일 맨 마지막에 작성했습니다.
---------------------------------------------------------------------------------------------------------

-- 학과 데이터: majors
INSERT INTO app.majors (code, name)
VALUES
    ('CS', '컴퓨터공학과'),
    ('AI', '인공지능학과'),
    ('EE', '전자공학과'),
    ('BA', '경영학과'),
    ('ME', '기계공학과'),
    ('DS', '데이터사이언스학과'),
    ('SE', '소프트웨어학과'),
    ('CE', '건축공학과'),
    ('BI', '바이오공학과'),
    ('DE', '디자인학과');

-- 학생 데이터: students
-- 문제 2 확인을 위해 2024009, 2024010 학생은 학과 미배정(NULL)으로 입력합니다.
INSERT INTO app.students
    (student_no, name, email, major_id, grade)
VALUES
    ('2024001', '김철수', 'kim1@test.com', 1, 1),
    ('2024002', '이영희', 'lee2@test.com', 1, 2),
    ('2024003', '박민수', 'park3@test.com', 2, 3),
    ('2024004', '최유리', 'choi4@test.com', 2, 4),
    ('2024005', '정우성', 'jung5@test.com', 3, 2),
    ('2024006', '한지민', 'han6@test.com', 3, 1),
    ('2024007', '오세훈', 'oh7@test.com', 4, 3),
    ('2024008', '김나영', 'kim8@test.com', 4, 4),
    ('2024009', '서지훈', 'seo9@test.com', NULL, 2),
    ('2024010', '윤아름', 'yoon10@test.com', NULL, 1);

-- 과목 데이터: courses
INSERT INTO app.courses
    (course_code, name, credit)
VALUES
    ('CS101', '프로그래밍 기초', 3),
    ('CS102', '자료구조', 3),
    ('DB201', '데이터베이스', 3),
    ('AI301', '인공지능 개론', 3),
    ('WEB101', '웹 프로그래밍', 3),
    ('NET201', '컴퓨터 네트워크', 3),
    ('OS201', '운영체제', 3),
    ('DS101', '데이터 분석 기초', 3),
    ('SE202', '소프트웨어 공학', 3),
    ('UX101', '사용자 경험 디자인', 2);

-- 수강 데이터: enrollments
-- A/B/C/D/F/미입력 등급이 모두 나오도록 점수를 다양하게 입력합니다.
INSERT INTO app.enrollments
    (student_id, course_id, score, enrolled_at)
VALUES
    (1, 1, 95.5, DATE '2025-03-02'),
    (1, 3, 88.0, DATE '2025-03-02'),
    (2, 2, 86.0, DATE '2025-03-02'),
    (2, 4, 92.5, DATE '2025-03-02'),
    (3, 1, 76.0, DATE '2025-03-02'),
    (3, 5, 83.5, DATE '2025-03-02'),
    (4, 3, 59.0, DATE '2025-03-02'),
    (4, 6, 67.5, DATE '2025-03-02'),
    (5, 2, 72.0, DATE '2025-03-02'),
    (5, 7, NULL, DATE '2025-03-02'),
    (6, 4, 98.0, DATE '2025-03-02'),
    (6, 8, 81.0, DATE '2025-03-02'),
    (7, 5, 64.0, DATE '2025-03-02'),
    (7, 9, 90.0, DATE '2025-03-02'),
    (8, 6, 78.5, DATE '2025-03-02'),
    (8, 10, NULL, DATE '2025-03-02'),
    (9, 7, 55.0, DATE '2025-03-02'),
    (9, 8, 84.0, DATE '2025-03-02'),
    (10, 9, 91.5, DATE '2025-03-02'),
    (10, 10, 69.0, DATE '2025-03-02');

-- 2학기 데이터 (PDF 안내에 따라 별도 INSERT로 분리하고 ON CONFLICT DO NOTHING 적용)
-- 같은 (student_id, course_id) 조합이 이미 있으면 오류 없이 건너뜀 → 중복 입력 방지
INSERT INTO app.enrollments
    (student_id, course_id, score, enrolled_at)
VALUES
    (1, 2, 88.0, DATE '2025-09-01'),
    (1, 4, 92.5, DATE '2025-09-01'),
    (2, 1, 95.5, DATE '2025-09-01'),
    (2, 3, 91.0, DATE '2025-09-01')
ON CONFLICT (student_id, course_id) DO NOTHING;

-- 입력 건수 확인
SELECT 'majors' AS table_name, COUNT(*) AS row_count
FROM app.majors
UNION ALL
SELECT 'students', COUNT(*)
FROM app.students
UNION ALL
SELECT 'courses', COUNT(*)
FROM app.courses
UNION ALL
SELECT 'enrollments', COUNT(*)
FROM app.enrollments;

---------------------------------------------------------------------------------------------------------