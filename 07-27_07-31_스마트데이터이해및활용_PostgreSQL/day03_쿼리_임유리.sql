/*
===============================================================================
첨부파일 먼저 실행 : PostgreSQL_day03_tuning_샘플_스키마_DDL_DML.sql
===============================================================================
===============================================================================
문제 풀이 공통 체크리스트
===============================================================================
채점은 실행시간의 절대값보다 다음 항목을 중심합니다.

	- 원래 쿼리와 결과가 동일한가?
	- 병목을 정확히 진단했는가?
	- 인덱스 컬럼 순서와 조건이 합리적인가?
	- 실제로 실행계획이 어떻게 변했는가?
	- 인덱스가 사용되지 않더라도 그 이유를 설명했는가?
===============================================================================
*/


-- ############################################################################
-- 문제 1. 기본 키 검색의 실행 계획 읽기 <<< 문제 해결 방법 제시문항(10점 보너스)
-- ############################################################################
/*
[문제]
 사원번호가 100인 사원을 검색하고 실행 계획을 해석한다.
 이미 빠른 쿼리도 튜닝 대상인지 판단한다.

[수행 과제]
 - 실제 사용된 Scan 노드를 확인한다.
 - estimated rows와 actual rows를 비교한다.
 - Buffers와 Execution Time을 기록한다.
 - 추가 인덱스가 필요한지 근거와 함께 답한다.
*/

-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING OFF)
SELECT *
FROM employees
WHERE employee_id = 100;
-- 	QUERY PLAN
--Index Scan using employees_pkey on day03_tuning.employees  (cost=0.29..8.31 rows=1 width=111) (actual rows=1.00 loops=1)
--  Output: employee_id, employee_no, first_name, last_name, full_name, email, department_id, job_code, branch_code, hire_date, salary, employment_status, phone, created_at
--  Index Cond: (employees.employee_id = 100)
--  Index Searches: 1
--  Buffers: shared hit=3
--Planning Time: 0.095 ms
--Execution Time: 0.046 ms


-- 개선안 <<< 이부분은 직접 작성합니다.(쿼리 재작성 또는 인덱스 생성 SQL)
--이 문제의 정답은 "계획을 확인하되 별도 튜닝하지 않는다"이다.


-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING OFF)
SELECT *
FROM employees
WHERE employee_id = 100;
-- 	QUERY PLAN
--Index Scan using employees_pkey on day03_tuning.employees  (cost=0.29..8.31 rows=1 width=111) (actual rows=1.00 loops=1)
--  Output: employee_id, employee_no, first_name, last_name, full_name, email, department_id, job_code, branch_code, hire_date, salary, employment_status, phone, created_at
--  Index Cond: (employees.employee_id = 100)
--  Index Searches: 1
--  Buffers: shared hit=3
--Planning Time: 0.095 ms
--Execution Time: 0.046 ms

/*
-- [개선 결과 해석]
-- 변경된 Plan Node:없음
-- Buffers 변화:없음(shared hit=3 -> shared hit=3)
-- Execution Time 변화: 없음(0.046 ms -> 0.046 ms, 동일 계획 재확인)
-- 개선된 이유:
 - employee_id는 PRIMARY KEY이므로 자동으로 B-tree 인덱스가 생성된다.
 - 일반적으로 Index Scan 또는 동등한 인덱스 기반 계획이 선택된다.
 - 단건 조회를 위해 employee_id에 중복 인덱스를 추가하는 것은 쓰기 비용과 저장 공간만 늘린다.
 - 따라서 이 문제의 정답은 "계획을 확인하되 별도 튜닝하지 않는다"이다.
 - Seq Scan이 보인다면 테이블 크기, 통계, 설정을 먼저 확인하고 무조건 인덱스를 추가하지 않는다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE UNIQUE INDEX employees_pkey ON day03_tuning.employees USING btree (employee_id)


-- ############################################################################
-- 문제 2. 함수가 적용된 이메일 검색: 표현식 인덱스 <<< 문제 해결 방법 제시문항(10점 보너스)
-- ############################################################################
/*
[문제]
 대소문자 구분 없이 user1234@corp.com을 검색한다.
 WHERE절의 lower(email) 때문에 일반 email 인덱스만으로는 같은 표현식을 바로 찾기 어렵다.

[개선 목표]
 쿼리의 검색 표현식과 동일한 lower(email) 표현식 인덱스를 설계한다.
*/


-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, email
FROM employees
WHERE lower(email) = 'user1234@corp.com';
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1658.00 rows=250 width=46) (actual rows=1.00 loops=1)
--  Filter: (lower((email)::text) = 'user1234@corp.com'::text)
--  Rows Removed by Filter: 49999
--  Buffers: shared hit=908
--Planning Time: 0.076 ms
--Execution Time: 8.551 ms

-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_employees_lower_email;

CREATE INDEX idx_employees_lower_email
    ON employees (lower(email));

ANALYZE employees;

-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, email
FROM employees
WHERE lower(email) = 'user1234@corp.com';
-- 	QUERY PLAN
--Index Scan using idx_employees_lower_email on employees  (cost=0.41..8.43 rows=1 width=46) (actual rows=1.00 loops=1)
--  Index Cond: (lower((email)::text) = 'user1234@corp.com'::text)
--  Index Searches: 1
--  Buffers: shared hit=4
--Planning Time: 0.062 ms
--Execution Time: 0.032 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node:Seq Scan -> Index Scan
-- Buffers 변화:shared hit=908 -> shared hit=4
-- Execution Time 변화: 8.551 ms -> 0.032 ms
-- 개선된 이유:
 - 일반 인덱스 ON employees(email)는 lower(email) 검색식과 구조가 다르다.
 - ON employees(lower(email))은 WHERE절 표현식과 일치하므로 인덱스 조건으로 사용할 수 있다.
 - 49,999건을 필터링하던 Seq Scan이 Index Searches=1의 단건 Index Scan으로 바뀌었다.
 - 대안: 저장 시 이메일을 항상 소문자로 정규화한다면 lower(email) 표현식 인덱스 대신
   email 컬럼에 대한 일반 인덱스와 email = '...' 조건만으로도 같은 효과를 낼 수 있다.
   다만 기존 데이터에 대소문자가 섞여 있다면 데이터 정규화(마이그레이션) 비용이 추가로 든다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_lower_email ON day03_tuning.employees USING btree (lower((email)::text))

-- ############################################################################
-- 문제 3. 접미사 LIKE 검색: pg_trgm GIN 인덱스
-- ############################################################################
/*
[문제]
 gmail.com 도메인을 사용하는 사원을 찾는다.
 '%@gmail.com'은 앞부분이 와일드카드이므로 일반 B-tree의 정렬 순서를 활용하기 어렵다.

[개선 목표]
 pg_trgm과 GIN 인덱스를 사용해 포함/접미사 검색을 개선한다.
*/


-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, email
FROM employees
WHERE email LIKE '%@gmail.com';
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1533.00 rows=5 width=46) (actual rows=500.00 loops=1)
--  Filter: ((email)::text ~~ '%@gmail.com'::text)
--  Rows Removed by Filter: 49500
--  Buffers: shared hit=908
--Planning Time: 0.117 ms
--Execution Time: 7.705 ms


-- 개선안 - 이부분은 직접작성합니다.
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
DROP INDEX IF EXISTS idx_employees_email_trgm;
CREATE INDEX idx_employees_email_trgm
    ON employees USING gin (email gin_trgm_ops);
ANALYZE employees;


-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, email
FROM employees
WHERE email LIKE '%@gmail.com';
-- 	QUERY PLAN
--Bitmap Heap Scan on employees  (cost=93.60..899.36 rows=505 width=46) (actual rows=500.00 loops=1)
--  Recheck Cond: ((email)::text ~~ '%@gmail.com'::text)
--  Heap Blocks: exact=500
--  Buffers: shared hit=577
--  ->  Bitmap Index Scan on idx_employees_email_trgm  (cost=0.00..93.48 rows=505 width=0) (actual rows=500.00 loops=1)
--        Index Cond: ((email)::text ~~ '%@gmail.com'::text)
--        Index Searches: 1
--        Buffers: shared hit=77
--Planning:
--  Buffers: shared hit=1
--Planning Time: 0.125 ms
--Execution Time: 3.396 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Seq Scan -> Bitmap Index Scan + Bitmap Heap Scan
-- Buffers 변화: shared hit=908 -> shared hit=577
-- Execution Time 변화: 7.705 ms -> 3.396 ms
-- 개선된 이유:
 - 선행 와일드카드 때문에 B-tree의 정렬된 접두 탐색은 사용할 수 없다.
 - pg_trgm의 GIN 인덱스가 문자열을 trigram으로 분해해 후보 500건을 찾았다.
 - 후보는 Recheck Cond로 재검사되므로 LIKE의 정확한 결과 500건을 유지한다.
 - 통계 추정은 505건으로 실제 500건과 거의 근접했다.
 - 결과 비율이 커지면 계획도 달라진다: 지금은 gmail 비율이 약 1%라 Bitmap Scan이 유리하지만,
   조건에 해당하는 행이 테이블의 상당 비율(예: 수십 %)을 차지하면 랜덤 I/O로 Heap을 흩어서
   읽는 Bitmap/Index 방식보다 Seq Scan 한 번이 더 싸지므로 옵티마이저가 다시 Seq Scan을 선택할 수 있다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_email_trgm ON day03_tuning.employees USING gin (email gin_trgm_ops)


-- ############################################################################
-- 문제 4. 필터 + ORDER BY + LIMIT: 부분 정렬 인덱스
-- ############################################################################
/*
[문제]
 재직 중이며 최근 365일 안에 입사한 사원을 연봉순으로 상위 100명 조회한다.

[개선 목표]
 - 재직자만 포함하는 부분 인덱스를 검토한다.
 - ORDER BY salary DESC와 LIMIT 100의 조기 종료를 유도한다.
*/


-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    employee_id,
    employee_no,
    full_name,
    hire_date,
    salary
FROM employees
WHERE employment_status = 'ACTIVE'
  AND hire_date >= current_date - 365
ORDER BY salary DESC
LIMIT 100;
-- 	QUERY PLAN
--Limit  (cost=2077.39..2077.64 rows=100 width=39) (actual rows=100.00 loops=1)
--  Buffers: shared hit=908
--  ->  Sort  (cost=2077.39..2088.47 rows=4432 width=39) (actual rows=100.00 loops=1)
--        Sort Key: salary DESC
--        Sort Method: top-N heapsort  Memory: 39kB
--        Buffers: shared hit=908
--        ->  Seq Scan on employees  (cost=0.00..1908.00 rows=4432 width=39) (actual rows=4411.00 loops=1)
--              Filter: (((employment_status)::text = 'ACTIVE'::text) AND (hire_date >= (CURRENT_DATE - 365)))
--              Rows Removed by Filter: 45589
--              Buffers: shared hit=908
--Planning Time: 0.139 ms
--Execution Time: 9.159 ms


-- 개선안 - 이부분은 직접작성합니다.
DROP INDEX IF EXISTS idx_employees_active_salary_hire;
CREATE INDEX idx_employees_active_salary_hire
    ON employees (salary DESC, hire_date)
    INCLUDE (employee_id, employee_no, full_name)
    WHERE employment_status = 'ACTIVE';
VACUUM (ANALYZE) employees;


-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    employee_id,
    employee_no,
    full_name,
    hire_date,
    salary
FROM employees
WHERE employment_status = 'ACTIVE'
  AND hire_date >= current_date - 365
ORDER BY salary DESC
LIMIT 100;
-- 	QUERY PLAN
--Limit  (cost=0.42..41.81 rows=100 width=39) (actual rows=100.00 loops=1)
--  Buffers: shared hit=11
--  ->  Index Only Scan using idx_employees_active_salary_hire on employees  (cost=0.42..1834.74 rows=4432 width=39) (actual rows=100.00 loops=1)
--        Index Cond: (hire_date >= (CURRENT_DATE - 365))
--        Heap Fetches: 0
--        Index Searches: 1
--        Buffers: shared hit=11
--Planning Time: 0.172 ms
--Execution Time: 0.211 ms

/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Seq Scan + top-N Sort -> Index Only Scan
-- Buffers 변화: shared hit=908 -> shared hit=11
-- Execution Time 변화: 9.159 ms -> 0.211 ms
-- 개선된 이유:
 - 개선 전에는 Sort Method: top-N heapsort(Memory: 39kB)로 4,411건을 메모리에서 정렬한 뒤
   상위 100건만 골라냈다 — 정렬 자체는 빠르지만 그 앞단의 Seq Scan(전체 스캔+필터)이 병목이었다.
 - ACTIVE 행만 담은 부분 인덱스가 불필요한 상태 행을 제외한다.
 - salary DESC 순서로 읽어 별도 Sort 없이 LIMIT 100에서 조기 종료한다.
 - 필요한 출력 열을 INCLUDE하고 VACUUM (ANALYZE)로 visibility map을 갱신하여 Heap Fetches=0의 커버링 조회가 가능했다.
 - hire_date는 두 번째 키라 범위를 건너뛰며 검사하지만 LIMIT 조기 종료 효과가 더 컸다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_active_salary_hire ON day03_tuning.employees USING btree (salary DESC, hire_date) INCLUDE (employee_id, employee_no, full_name) WHERE ((employment_status)::text = 'ACTIVE'::text)

-- ############################################################################
-- 문제 5. OR 조건과 IN 조건 비교
-- ############################################################################
/*
[문제]
 지점 코드가 B003, B004, B005 중 하나인 사원을 검색한다.
 OR 조건을 IN으로 바꾸었을 때 가독성과 실행 계획이 어떻게 달라지는지 확인한다.

[개선 목표]
 branch_code 인덱스를 추가하고 OR/IN 두 쿼리의 계획을 비교한다.
*/


-- 개선 전: 인덱스 없음
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, branch_code
FROM employees
WHERE branch_code = 'B003'
   OR branch_code = 'B004'
   OR branch_code = 'B005';
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1783.00 rows=1498 width=33) (actual rows=1500.00 loops=1)
--  Filter: (((branch_code)::text = 'B003'::text) OR ((branch_code)::text = 'B004'::text) OR ((branch_code)::text = 'B005'::text))
--  Rows Removed by Filter: 48500
--  Buffers: shared hit=908
--Planning Time: 0.177 ms
--Execution Time: 9.002 ms

-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_employees_branch_code;
CREATE INDEX idx_employees_branch_code
    ON employees (branch_code);

ANALYZE employees;


-- 개선 후 A: OR
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, branch_code
FROM employees
WHERE branch_code = 'B003'
   OR branch_code = 'B004'
   OR branch_code = 'B005';
-- 	QUERY PLAN
--Bitmap Heap Scan on employees  (cost=24.68..990.98 rows=1508 width=33) (actual rows=1500.00 loops=1)
--  Recheck Cond: (((branch_code)::text = 'B003'::text) OR ((branch_code)::text = 'B004'::text) OR ((branch_code)::text = 'B005'::text))
--  Heap Blocks: exact=506
--  Buffers: shared hit=510
--  ->  Bitmap Index Scan on idx_employees_branch_code  (cost=0.00..24.30 rows=1523 width=0) (actual rows=1500.00 loops=1)
--        Index Cond: ((branch_code)::text = ANY ('{B003,B004,B005}'::text[]))
--        Index Searches: 1
--        Buffers: shared hit=4
--Planning Time: 0.209 ms
--Execution Time: 1.418 ms


-- 개선 후 B: IN
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, branch_code
FROM employees
WHERE branch_code IN ('B003', 'B004', 'B005');
-- 	QUERY PLAN
--Bitmap Heap Scan on employees  (cost=24.68..985.27 rows=1523 width=33) (actual rows=1500.00 loops=1)
--  Recheck Cond: ((branch_code)::text = ANY ('{B003,B004,B005}'::text[]))
--  Heap Blocks: exact=506
--  Buffers: shared hit=510
--  ->  Bitmap Index Scan on idx_employees_branch_code  (cost=0.00..24.30 rows=1523 width=0) (actual rows=1500.00 loops=1)
--        Index Cond: ((branch_code)::text = ANY ('{B003,B004,B005}'::text[]))
--        Index Searches: 1
--        Buffers: shared hit=4
--Planning Time: 0.199 ms
--Execution Time: 0.842 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Seq Scan -> (OR/IN 모두 동일) Bitmap Index Scan + Bitmap Heap Scan
-- Buffers 변화: shared hit=908 -> OR shared hit=510 / IN shared hit=510 (완전히 동일)
-- Execution Time 변화: 9.002 ms -> OR 1.418 ms / IN 0.842 ms
-- 개선된 이유:
 - branch_code 인덱스로 48,500건을 버리는 전체 스캔을 제거했다.
 - 이번 실행에서는 PostgreSQL 옵티마이저가 OR 체인(=,=,=)을 자동으로 IN과 동일한 `= ANY ('{B003,B004,B005}')` 조건으로 변환했다. 
   그 결과 OR와 IN의 실행 계획(Recheck Cond, Bitmap Index Scan, Buffers)이 완전히 동일하게 나왔고, 
   Execution Time 차이(1.418ms vs 0.842ms)는 계획 차이가 아니라 실행 시점의 캐시/변동에 의한 것이다.
 - 두 쿼리 모두 1,500건으로 결과가 동일하다.
 - 이 결과는 "OR와 IN이 항상 다른 계획을 만든다"는 통념과 달리, 값 목록이 짧고 동일 컬럼에 대한 등호 비교일 때는 
   옵티마이저가 이미 동등하게 최적화한다는 것을 보여준다. 
   IN은 그래도 가독성 면에서 더 간결하므로 작성 스타일로는 IN을 권장한다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_branch_code ON day03_tuning.employees USING btree (branch_code)


-- ############################################################################
-- 문제 6. 비-SARGable 날짜 조건: 함수 대신 범위 검색
-- ############################################################################
/*
[문제]
 2025년에 입사한 사원을 찾는다.
 EXTRACT 함수가 컬럼에 적용된 조건과 원본 컬럼의 범위 조건을 비교한다.

[개선 목표]
 인덱스가 사용할 수 있는 반개구간 [2025-01-01, 2026-01-01)으로 재작성한다.
*/


-- 개선 전: 인덱스 없음

-- 비교 A: 컬럼에 함수 적용
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, hire_date
FROM employees
WHERE extract(year FROM hire_date) = 2025;
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1658.00 rows=250 width=32) (actual rows=5003.00 loops=1)
--  Filter: (EXTRACT(year FROM hire_date) = '2025'::numeric)
--  Rows Removed by Filter: 44997
--  Buffers: shared hit=908
--Planning Time: 0.141 ms
--Execution Time: 9.567 ms


-- 비교 B: SARGable 범위 조건 <<< 이부분은 직접 작성합니다.
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, hire_date
FROM employees
WHERE hire_date >= date '2025-01-01'
  AND hire_date <  date '2026-01-01';
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1658.00 rows=5014 width=32) (actual rows=5003.00 loops=1)
--  Filter: ((hire_date >= '2025-01-01'::date) AND (hire_date < '2026-01-01'::date))
--  Rows Removed by Filter: 44997
--  Buffers: shared hit=908
--Planning Time: 0.061 ms
--Execution Time: 4.651 ms


-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_employees_hire_date;
CREATE INDEX idx_employees_hire_date
    ON employees (hire_date);

ANALYZE employees;


-- 개선 후
-- 비교 A: 컬럼에 함수 적용
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, hire_date
FROM employees
WHERE extract(year FROM hire_date) = 2025;
-- 	QUERY PLAN
--Seq Scan on employees  (cost=0.00..1658.00 rows=250 width=32) (actual rows=5003.00 loops=1)
--  Filter: (EXTRACT(year FROM hire_date) = '2025'::numeric)
--  Rows Removed by Filter: 44997
--  Buffers: shared hit=908
--Planning Time: 0.072 ms
--Execution Time: 7.688 ms


-- 비교 B: SARGable 범위 조건 <<< 이부분은 직접 작성합니다.
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, hire_date
FROM employees
WHERE hire_date >= date '2025-01-01'
  AND hire_date <  date '2026-01-01';
-- 	QUERY PLAN
--Bitmap Heap Scan on employees  (cost=75.17..1057.63 rows=4964 width=32) (actual rows=5003.00 loops=1)
--  Recheck Cond: ((hire_date >= '2025-01-01'::date) AND (hire_date < '2026-01-01'::date))
--  Heap Blocks: exact=586
--  Buffers: shared hit=594
--  ->  Bitmap Index Scan on idx_employees_hire_date  (cost=0.00..73.93 rows=4964 width=0) (actual rows=5003.00 loops=1)
--        Index Cond: ((hire_date >= '2025-01-01'::date) AND (hire_date < '2026-01-01'::date))
--        Index Searches: 1
--        Buffers: shared hit=8
--Planning Time: 0.076 ms
--Execution Time: 1.569 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node: 함수 조건은 Seq Scan 유지(Rows Removed by Filter: 44997 그대로),
--                    범위 조건은 Seq Scan -> Bitmap Index/Heap Scan
-- Buffers 변화: 함수 908 유지 / 범위 908 -> shared hit=594
-- Execution Time 변화: 함수 9.567 -> 7.688 ms(인덱스 미사용, 측정 변동 범위) / 범위 4.651 -> 1.569 ms
-- 개선된 이유:
 - extract(year FROM hire_date)는 원본 인덱스 키에 함수를 적용해 SARGable하지 않다.
   인덱스 생성 후에도 Index Cond가 생기지 않고 Seq Scan+Filter가 그대로 유지된다.
 - 반개구간은 2025년 전체를 정확히 표현하면서 hire_date B-tree 범위 탐색이 가능하다.
 - 두 쿼리 모두 5,003건으로 결과가 동일하다.
 - 함수 조건의 실행 시간 변화(9.567→7.688ms)는 인덱스를 실제로 쓰지 못했기 때문에 생긴 측정 변동일 뿐 개선 효과가 아니다.
   반면 범위 조건은 Bitmap Index Scan으로 908→594buf, 4.651→1.569ms(약 3배)로 확실히 개선됐다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_hire_date ON day03_tuning.employees USING btree (hire_date)


-- ############################################################################
-- 문제 7. 복합 인덱스와 왼쪽 우선 규칙
-- ############################################################################
/*
[문제]
 부서 5의 DEV 직무 사원을 연봉순으로 상위 20명 조회한다.
 복합 인덱스의 컬럼 순서를 설계하고 왼쪽 선두 컬럼이 빠진 검색도 비교한다.

[개선 목표]
 등호 조건을 앞에, 정렬 컬럼을 뒤에 배치한다.
*/



-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, salary
FROM employees
WHERE department_id = 5
  AND job_code = 'DEV'
ORDER BY salary DESC
LIMIT 20;
-- 	QUERY PLAN
--Limit  (cost=1664.55..1664.60 rows=20 width=35) (actual rows=20.00 loops=1)
--  Buffers: shared hit=908
--  ->  Sort  (cost=1664.55..1665.16 rows=246 width=35) (actual rows=20.00 loops=1)
--        Sort Key: salary DESC
--        Sort Method: top-N heapsort  Memory: 27kB
--        Buffers: shared hit=908
--        ->  Seq Scan on employees  (cost=0.00..1658.00 rows=246 width=35) (actual rows=250.00 loops=1)
--              Filter: ((department_id = 5) AND ((job_code)::text = 'DEV'::text))
--              Rows Removed by Filter: 49750
--              Buffers: shared hit=908
--Planning Time: 0.148 ms
--Execution Time: 4.599 ms


-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_employees_dept_job_salary;
CREATE INDEX idx_employees_dept_job_salary
    ON employees (department_id, job_code, salary DESC)
    INCLUDE (employee_id, employee_no, full_name);
VACUUM (ANALYZE) employees;



-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, salary
FROM employees
WHERE department_id = 5
  AND job_code = 'DEV'
  ORDER BY salary DESC --개선 후 별도 Sort가 제거되는지 확인한다
LIMIT 20;
-- 	QUERY PLAN
--Limit  (cost=0.41..1.76 rows=20 width=35) (actual rows=20.00 loops=1)
--  Buffers: shared hit=4
--  ->  Index Only Scan using idx_employees_dept_job_salary on employees  (cost=0.41..17.52 rows=255 width=35) (actual rows=20.00 loops=1)
--        Index Cond: ((department_id = 5) AND (job_code = 'DEV'::text))
--        Heap Fetches: 0
--        Index Searches: 1
--        Buffers: shared hit=4
--Planning Time: 0.148 ms
--Execution Time: 0.051 ms


-- 조건 컬럼 department_id를 생략한 비교 쿼리
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_id, employee_no, full_name, salary
FROM employees
WHERE job_code = 'DEV'
ORDER BY salary DESC
LIMIT 20;
-- 	QUERY PLAN
--Limit  (cost=465.50..465.55 rows=20 width=35) (actual rows=20.00 loops=1)
--  Buffers: shared hit=129
--  ->  Sort  (cost=465.50..478.02 rows=5007 width=35) (actual rows=20.00 loops=1)
--        Sort Key: salary DESC
--        Sort Method: top-N heapsort  Memory: 26kB
--        Buffers: shared hit=129
--        ->  Index Only Scan using idx_employees_dept_job_salary on employees  (cost=0.41..332.27 rows=5007 width=35) (actual rows=5000.00 loops=1)
--              Index Cond: (job_code = 'DEV'::text)
--              Heap Fetches: 0
--              Index Searches: 22
--              Buffers: shared hit=129
--Planning Time: 0.144 ms
--Execution Time: 1.313 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Seq Scan + Sort -> Index Only Scan(별도 Sort 제거, ORDER BY 자체를 제외한 비교)
-- Buffers 변화: shared hit=908 -> shared hit=4
-- Execution Time 변화: 4.599 ms -> 0.051 ms
-- 개선된 이유:
 - 두 등호 조건을 선두에 두고 salary DESC를 뒤에 둬 필터와 정렬을 함께 만족한다.
 - INCLUDE 열과 VACUUM (ANALYZE)로 갱신된 visibility map 덕분에 Heap Fetches=0이다.
   (개선 후 쿼리는 ORDER BY를 주석 처리해 Sort 노드 자체가 사라졌는지 확인했다.)
 - department_id를 빼면 왼쪽 선두 컬럼(등호 조건)이 없어져 Seq Scan으로 완전히 되돌아가지는 않았지만, 
   대신 department_id별로 인덱스를 22번 나눠서 훑는 Index Searches=22가 발생했고
   salary 순서를 보장할 수 없어 별도 Sort(top-N heapsort)가 다시 필요해졌다(Buffers도 4 -> 129로 증가). 
   즉 왼쪽 선두 컬럼이 빠지면 인덱스를 아예 못 쓰는 게 아니라, 여러 번 나눠 훑고 정렬까지 다시 해야 해서 효율이 크게 떨어진다.
 - 따라서 복합 인덱스는 대표 쿼리의 조건 순서(등호 컬럼을 선두에)에 맞춰 설계해야 한다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_dept_job_salary ON day03_tuning.employees USING btree (department_id, job_code, salary DESC) INCLUDE (employee_id, employee_no, full_name)

-- ############################################################################
-- 문제 8. 커버링 인덱스와 Index Only Scan
-- ############################################################################
/*
[문제]
 특정 사번 구간의 이름과 이메일을 조회한다.
 검색 컬럼과 출력 컬럼을 구분하여 INCLUDE 커버링 인덱스를 설계한다.

[개선 목표]
 Heap Fetches가 적은 Index Only Scan 가능성을 높인다.
*/

-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_no, full_name, email
FROM employees
WHERE employee_no >= 'EMP040000'
  AND employee_no <  'EMP040051'
ORDER BY employee_no;
-- 	QUERY PLAN
--Sort  (cost=1658.27..1658.30 rows=14 width=38) (actual rows=51.00 loops=1)
--  Sort Key: employee_no
--  Sort Method: quicksort  Memory: 27kB
--  Buffers: shared hit=908
--  ->  Seq Scan on employees  (cost=0.00..1658.00 rows=14 width=38) (actual rows=51.00 loops=1)
--        Filter: (((employee_no)::text >= 'EMP040000'::text) AND ((employee_no)::text < 'EMP040051'::text))
--        Rows Removed by Filter: 49949
--        Buffers: shared hit=908
--Planning Time: 0.143 ms
--Execution Time: 4.470 ms


-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_employees_no_cover;
CREATE INDEX idx_employees_no_cover
    ON employees (employee_no)
    INCLUDE (full_name, email);
VACUUM (ANALYZE) employees;



-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT employee_no, full_name, email
FROM employees
WHERE employee_no >= 'EMP040000'
  AND employee_no <  'EMP040051'
ORDER BY employee_no;
-- 	QUERY PLAN
--Index Only Scan using idx_employees_no_cover on employees  (cost=0.41..4.43 rows=1 width=38) (actual rows=51.00 loops=1)
--  Index Cond: ((employee_no >= 'EMP040000'::text) AND (employee_no < 'EMP040051'::text))
--  Heap Fetches: 0
--  Index Searches: 1
--  Buffers: shared hit=5
--Planning Time: 0.155 ms
--Execution Time: 0.052 ms


/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Seq Scan + Sort -> Index Only Scan
-- Buffers 변화: shared hit=908 -> shared hit=5
-- Execution Time 변화: 4.470 ms -> 0.052 ms
-- 개선된 이유:
 - 범위 조건과 ORDER BY의 employee_no를 B-tree 키로 사용했다.
 - full_name과 email은 탐색 키가 아니므로 INCLUDE에 두어 인덱스 크기를 절제했다.
 - VACUUM (ANALYZE)로 visibility map을 갱신한 뒤 Heap Fetches=0을 확인했다.
 - 인덱스 순서가 정렬도 만족해 별도 Sort가 사라지고 동일한 51건을 반환했다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employees'
ORDER BY indexname;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_employees_no_cover ON day03_tuning.employees USING btree (employee_no) INCLUDE (full_name, email)

-- ############################################################################
-- 문제 9. 조인, loops, 근무 기록 복합 인덱스
-- ############################################################################
/*
[문제]
 부서 5의 재직자 중 최근 30일 초과근무 합계가 큰 사원 20명을 조회한다.
 5만 사원과 50만 근무 기록의 조인 계획을 읽는다.

[개선 목표]
 외부 사원 행마다 반복되는 work_logs 탐색 비용과 loops를 줄인다.
*/

-- 개선 전
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    e.employee_id,
    e.employee_no,
    e.full_name,
    sum(w.overtime_minutes) AS total_overtime_minutes
FROM employees AS e
JOIN employee_work_logs AS w
  ON w.employee_id = e.employee_id
WHERE e.department_id = 5
  AND e.employment_status = 'ACTIVE'
  AND w.work_date >= current_date - 30
GROUP BY
    e.employee_id,
    e.employee_no,
    e.full_name
ORDER BY total_overtime_minutes DESC
LIMIT 20;
-- 	QUERY PLAN
--Limit  (cost=10682.03..10682.08 rows=20 width=36) (actual rows=20.00 loops=1)
--  Buffers: shared hit=6907
--  ->  Sort  (cost=10682.03..10684.32 rows=915 width=36) (actual rows=20.00 loops=1)
--        Sort Key: (sum(w.overtime_minutes)) DESC
--        Sort Method: top-N heapsort  Memory: 27kB
--        Buffers: shared hit=6907
--        ->  GroupAggregate  (cost=10537.39..10657.68 rows=915 width=36) (actual rows=616.00 loops=1)
--              Group Key: e.employee_id
--              Buffers: shared hit=6907
--              ->  Gather Merge  (cost=10537.39..10643.96 rows=915 width=32) (actual rows=1026.00 loops=1)
--                    Workers Planned: 2
--                    Workers Launched: 2
--                    Buffers: shared hit=6907
--                    ->  Sort  (cost=9537.37..9538.32 rows=381 width=32) (actual rows=342.00 loops=3)
--                          Sort Key: e.employee_id
--                          Sort Method: quicksort  Memory: 47kB
--                          Buffers: shared hit=6907
--                          Worker 0:  Sort Method: quicksort  Memory: 38kB
--                          Worker 1:  Sort Method: quicksort  Memory: 36kB
--                          ->  Hash Join  (cost=1685.24..9521.03 rows=381 width=32) (actual rows=342.00 loops=3)
--                                Hash Cond: (w.employee_id = e.employee_id)
--                                Buffers: shared hit=6891
--                                ->  Parallel Seq Scan on employee_work_logs w  (cost=0.00..7812.83 rows=8748 width=12) (actual rows=7077.33 loops=3)
--                                      Filter: (work_date >= (CURRENT_DATE - 30))
--                                      Rows Removed by Filter: 159589
--                                      Buffers: shared hit=4167
--                                ->  Hash  (cost=1658.00..1658.00 rows=2179 width=28) (actual rows=2500.00 loops=3)
--                                      Buckets: 4096  Batches: 1  Memory Usage: 179kB
--                                      Buffers: shared hit=2724
--                                      ->  Seq Scan on employees e  (cost=0.00..1658.00 rows=2179 width=28) (actual rows=2500.00 loops=3)
--                                            Filter: ((department_id = 5) AND ((employment_status)::text = 'ACTIVE'::text))
--                                            Rows Removed by Filter: 47500
--                                            Buffers: shared hit=2724
--Planning:
--  Buffers: shared hit=6
--Planning Time: 0.205 ms
--Execution Time: 25.365 ms


-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_work_logs_employee_date;
CREATE INDEX idx_work_logs_employee_date
    ON employee_work_logs (employee_id, work_date)
    INCLUDE (overtime_minutes);
ANALYZE employee_work_logs;


-- 개선 후
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    e.employee_id,
    e.employee_no,
    e.full_name,
    sum(w.overtime_minutes) AS total_overtime_minutes
FROM employees AS e
JOIN employee_work_logs AS w
  ON w.employee_id = e.employee_id
WHERE e.department_id = 5
  AND e.employment_status = 'ACTIVE'
  AND w.work_date >= current_date - 30
GROUP BY
    e.employee_id,
    e.employee_no,
    e.full_name
ORDER BY total_overtime_minutes DESC
LIMIT 20;
---- 	QUERY PLAN
--Limit  (cost=8316.19..8316.24 rows=20 width=36) (actual rows=20.00 loops=1)
--  Buffers: shared hit=8413
--  ->  Sort  (cost=8316.19..8318.57 rows=954 width=36) (actual rows=20.00 loops=1)
--        Sort Key: (sum(w.overtime_minutes)) DESC
--        Sort Method: top-N heapsort  Memory: 27kB
--        Buffers: shared hit=8413
--        ->  GroupAggregate  (cost=8274.11..8290.80 rows=954 width=36) (actual rows=616.00 loops=1)
--              Group Key: e.employee_id
--              Buffers: shared hit=8413
--              ->  Sort  (cost=8274.11..8276.49 rows=954 width=32) (actual rows=1026.00 loops=1)
--                    Sort Key: e.employee_id
--                    Sort Method: quicksort  Memory: 97kB
--                    Buffers: shared hit=8413
--                    ->  Nested Loop  (cost=0.43..8226.89 rows=954 width=32) (actual rows=1026.00 loops=1)
--                          Buffers: shared hit=8413
--                          ->  Seq Scan on employees e  (cost=0.00..1658.00 rows=2179 width=28) (actual rows=2500.00 loops=1)
--                                Filter: ((department_id = 5) AND ((employment_status)::text = 'ACTIVE'::text))
--                                Rows Removed by Filter: 47500
--                                Buffers: shared hit=908
--                          ->  Index Only Scan using idx_work_logs_employee_date on employee_work_logs w  (cost=0.43..3.00 rows=1 width=12) (actual rows=0.41 loops=2500)
--                                Index Cond: ((employee_id = e.employee_id) AND (work_date >= (CURRENT_DATE - 30)))
--                                Heap Fetches: 0
--                                Index Searches: 2500
--                                Buffers: shared hit=7505
--Planning:
--  Buffers: shared hit=14
--Planning Time: 0.223 ms
--Execution Time: 11.649 ms




/*
-- [개선 결과 해석]
-- 변경된 Plan Node: Gather Merge(Parallel Hash Join + Parallel Seq Scan on employee_work_logs) -> Nested Loop + Index Only Scan(loops=2500)
-- Buffers 변화: shared hit=6907 -> shared hit=8413 (오히려 증가)
-- Execution Time 변화: 25.365 ms -> 11.649 ms (개선)
-- 개선된 이유 : 선두 employee_id는 조인 등호, 뒤 work_date는 최근 30일 범위 조건에 맞춘 순서다.
			  외부의 대상 사원(department_id=5, ACTIVE) 2,500행마다 내부 Index Only Scan이 loops=2500으로 실행되며, 
			  각 loop는 해당 사원의 최근 30일 구간만 정확히 짚어 읽는다.
			  반면 개선 전은 employee_work_logs 50만 행 전체를 Parallel Seq Scan으로 훑으며 work_date 조건을 행 단위로 필터링했다
			  (Rows Removed by Filter: 159,589).
			  Buffers 총량은 6907 -> 8413으로 오히려 늘었다. 
			  loops=2500번의 작은 인덱스 탐색이 누적되면서 총 블록 접근 수 자체는 커질 수 있다는 뜻이다. 
			  그런데도 Execution Time은 25.365ms -> 11.649ms로 개선됐는데, 
			  이는 "총 Buffers 수"보다 "각 접근이 얼마나 값싼가"가 더 중요하다는 것을 보여준다 
			  — Parallel Seq Scan은 50만 행을 읽고 필터링하는 비용이 크고, Index Only Scan의 각 loop는 매우 짧은 B-tree 탐색 한 번으로 끝나기 때문이다.
			  overtime_minutes를 INCLUDE해 Heap Fetches=0이며, 그룹 결과는 616건으로 개선 전후 동일하다.
*/


--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Tables/ANALYZE테이블명/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employee_work_logs'
ORDER BY indexname desc;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_work_logs_employee_date ON day03_tuning.employee_work_logs USING btree (employee_id, work_date) INCLUDE (overtime_minutes)

-- ############################################################################
-- 문제 10. NOT IN의 NULL 함정과 NOT EXISTS 안티 조인
-- ############################################################################
/*
[문제]
 완료된 교육 이력이 없는 사원을 찾는다.
 서브쿼리에 NULL이 포함된 NOT IN의 결과를 확인하고 정확한 쿼리로 수정한다.

[개선 목표]
 정확성을 먼저 회복하고, NOT EXISTS와 부분 인덱스로 안티 조인을 지원한다.
*/


-- 잘못된 쿼리: 서브쿼리 결과에 NULL이 있어 전체 결과가 0건이 될 수 있다.
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT e.employee_id, e.employee_no, e.full_name
FROM employees AS e
WHERE e.employee_id NOT IN (
    SELECT t.employee_id
    FROM employee_training AS t
    WHERE t.completion_status = 'COMPLETED'
);
-- 	QUERY PLAN
--Seq Scan on employees e  (cost=1028.43..2561.43 rows=25000 width=28) (actual rows=0.00 loops=1)
--  Filter: (NOT (ANY (employee_id = (hashed SubPlan 1).col1)))
--  Rows Removed by Filter: 50000
--  Buffers: shared hit=1284
--  SubPlan 1
--    ->  Seq Scan on employee_training t  (cost=0.00..938.51 rows=35966 width=8) (actual rows=36001.00 loops=1)
--          Filter: ((completion_status)::text = 'COMPLETED'::text)
--          Rows Removed by Filter: 9000
--          Buffers: shared hit=376
--Planning Time: 0.105 ms
--Execution Time: 18.303 ms



SELECT count(*) AS wrong_result_count
FROM employees AS e
WHERE e.employee_id NOT IN (
    SELECT t.employee_id
    FROM employee_training AS t
    WHERE t.completion_status = 'COMPLETED'
);
--wrong_result_count = 0



-- 개선안 <<< 이부분은 직접 작성합니다.
DROP INDEX IF EXISTS idx_training_completed_employee;
CREATE INDEX idx_training_completed_employee
    ON employee_training (employee_id)
    WHERE completion_status = 'COMPLETED';
ANALYZE employee_training;



-- 정확한 쿼리
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT e.employee_id, e.employee_no, e.full_name
FROM employees AS e
WHERE NOT EXISTS (
    SELECT 1
    FROM employee_training AS t
    WHERE t.employee_id = e.employee_id
      AND t.completion_status = 'COMPLETED'
);
-- 	QUERY PLAN
--Hash Anti Join  (cost=1389.73..3108.62 rows=13904 width=28) (actual rows=14000.00 loops=1)
--  Hash Cond: (e.employee_id = t.employee_id)
--  Buffers: shared hit=1284
--  ->  Seq Scan on employees e  (cost=0.00..1408.00 rows=50000 width=28) (actual rows=50000.00 loops=1)
--        Buffers: shared hit=908
--  ->  Hash  (cost=938.51..938.51 rows=36097 width=8) (actual rows=36000.00 loops=1)
--        Buckets: 65536  Batches: 1  Memory Usage: 1919kB
--        Buffers: shared hit=376
--        ->  Seq Scan on employee_training t  (cost=0.00..938.51 rows=36097 width=8) (actual rows=36001.00 loops=1)
--              Filter: ((completion_status)::text = 'COMPLETED'::text)
--              Rows Removed by Filter: 9000
--              Buffers: shared hit=376
--Planning:
--  Buffers: shared hit=3
--Planning Time: 0.183 ms
--Execution Time: 15.773 ms


SELECT count(*) AS correct_result_count
FROM employees AS e
WHERE NOT EXISTS (
    SELECT 1
    FROM employee_training AS t
    WHERE t.employee_id = e.employee_id
      AND t.completion_status = 'COMPLETED'
);
--correct_result_count = 14000



/*
-- [개선 결과 해석]
-- 변경된 Plan Node: hashed SubPlan을 쓰는 Seq Scan(0건, 잘못된 결과) -> Hash Anti Join(14000건, 정확한 결과)
-- Buffers 변화: shared hit=1284 -> shared hit=1284(동일 - 정확성 회복이 목적이지 버퍼 절감이 목적이 아니었음)
-- Execution Time 변화: 18.303 ms(잘못된 0건) -> 15.773 ms(정확한 14,000건)
-- 개선된 이유:
 - NOT IN 집합에 완료 행의 NULL 1건이 들어가 모든 비교가 UNKNOWN이 되어 0건이 됐다.
 - NOT EXISTS는 상관 조건의 일치 행 존재 여부만 검사하므로 NULL에 안전하다.
 - wrong_result_count=0, correct_result_count=14000으로 정확성이 회복됐다.
 - 부분 인덱스(idx_training_completed_employee)는 생성됐지만 완료 행이 36,001/45,001로 선택도가 낮아(전체의 80%) 
   플래너가 인덱스 대신 전체 Seq Scan + Hash Anti Join을 선택했다.
   이는 "인덱스를 만들었다고 항상 쓰이는 건 아니다"를 보여주는 사례이며, 
   선택도가 낮을 때는 Seq Scan 기반 Hash 계열 조인이 더 합리적인 선택이다.
*/

--[인덱스 정의 확인 쿼리 - DBeaver/Schema/day03_tuning/Tables/ANALYZE테이블명/Indexes/해당 인덱스 더블클릭/Access Method 로도 확인가능]
select indexname,indexdef FROM pg_indexes
WHERE schemaname = 'day03_tuning' AND tablename = 'employee_training'
ORDER BY indexname desc;

--[인덱스 정의 확인] <<< select결과 indexdef컬럼 내용을 복붙한다.
-- CREATE INDEX idx_training_completed_employee ON day03_tuning.employee_training USING btree (employee_id) WHERE ((completion_status)::text = 'COMPLETED'::text)



--======[최종 제출 내용]=================================================================================
/*
 - -- 개선전 QUERY PLAN << 복붙
 - -- 개선안 <<< 이부분은 직접 작성합니다.
 - -- 개선후 QUERY PLAN << 복붙
 - -- [개선 결과 해석] <<< 이부분은 직접 작성합니다.
 - -- [인덱스 정의 확인] << 복붙


=========[최종 제출 파일]======================================================================
-- day03_쿼리_홍길동.sql
-- Slack > 다이렉트 메시지

*/