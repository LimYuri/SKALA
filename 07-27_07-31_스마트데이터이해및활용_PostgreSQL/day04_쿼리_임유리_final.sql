/*
===============================================================================
 PostgreSQL Day 04 — 함수·프로시저·트리거 종합평가 문제
===============================================================================
 선행 파일
   PostgreSQL_day04_프로시저_함수_샘플_스키마_DDL_DML.sql

 평가 구성
   함수       3문제 : 35점
   프로시저    3문제 : 45점
   트리거      2문제 : 20점
   총점            : 100점

 제출 방법
   1. 선행 DDL/DML 스크립트를 먼저 실행한다.
   2. 아래 문제 순서대로 함수·프로시저·트리거를 작성한다.
   3. 각 객체의 생성문과 호출·검증 SQL을 하나의 SQL 파일로 제출한다.
   4. 객체는 반드시 proc_lab 스키마에 생성한다.
   5. 테이블명은 가능한 한 proc_lab.테이블명으로 명시한다.

 주의
   - 정답 스크립트를 실행하기 전에는 이 파일에 정답이 포함되어 있지 않다.
   - 테스트 DML은 BEGIN ... ROLLBACK으로 검증하면 샘플 데이터를 보존할 수 있다.
===============================================================================
*/

SET search_path TO proc_lab, public;


-- ============================================================================
-- 문제 1. [함수·10점] 고객 등급별 할인율 계산
-- ============================================================================

/*
  함수명
    proc_lab.fn_grade_discount_rate(p_grade text)

  요구사항
    1. numeric 타입의 할인율을 반환한다.
    2. 등급은 대소문자와 양쪽 공백을 무시한다.
    3. 등급별 할인율은 다음과 같다.

         BASIC   → 0
         SILVER  → 0.05
         GOLD    → 0.10
         VIP     → 0.15
         그 외   → 0

    4. LANGUAGE sql로 작성한다.
    5. IMMUTABLE, STRICT, PARALLEL SAFE 속성을 지정한다.
    6. customers 테이블과 함께 호출하여 모든 고객의 할인율을 확인한다.

  검증 예
    SELECT proc_lab.fn_grade_discount_rate(' gold ');
    예상값: 0.10
*/

-- 아래에 함수 정의와 호출문을 작성하세요.
-- 아래 예시처럼 고객들 정보 검색시 "고객 등급별 할인율" 컬럼을 함수 호출로 구현하세요.
--customer_id|customer_name|customer_grade|고객 등급별 할인율|
-------------+-------------+--------------+----------+
--          1|김민준          |GOLD          |      0.10|
--          2|이서연          |VIP           |      0.15|
--          3|박지훈          |SILVER        |      0.05|
--          4|최유리          |BASIC         |         0|
--          5|정도윤          |GOLD          |      0.10|


CREATE OR REPLACE FUNCTION proc_lab.fn_grade_discount_rate(p_grade text)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog, pg_temp
AS $function$
    SELECT CASE upper(btrim(p_grade))
             WHEN 'GOLD'   THEN 0.10::numeric
             WHEN 'VIP'    THEN 0.15::numeric
             WHEN 'SILVER' THEN 0.05::numeric
             ELSE               0::numeric
           END;
$function$;

-- 공식 검증 예: 공백/소문자 입력도 정상 처리되는지 확인
SELECT proc_lab.fn_grade_discount_rate(' gold ') AS check_trim_and_case;
-- 실행결과: check_trim_and_case = 0.10

-- 기대: 고객 1~5의 할인율 = 0.10, 0.15, 0.05, 0, 0.10
SELECT c.customer_id,
       c.customer_name,
       c.customer_grade,
       proc_lab.fn_grade_discount_rate(c.customer_grade) AS "고객 등급별 할인율"
  FROM proc_lab.customers AS c
 ORDER BY c.customer_id;




-- ============================================================================
-- 문제 2. [함수·12점] 기준 재고 미만 상품 목록 반환
-- ============================================================================

/*
  함수명
    proc_lab.fn_products_below_stock(p_threshold integer)

  반환 테이블 컬럼
    product_id    bigint
    product_name  varchar
    stock_qty     integer
    shortage_qty  integer
    unit_price    numeric

  요구사항
    1. active=true인 상품만 대상으로 한다.
    2. stock_qty가 p_threshold보다 작은 상품만 반환한다.
    3. shortage_qty는 p_threshold - stock_qty로 계산한다.
    4. 재고가 적은 상품부터 정렬하고, 재고가 같으면 product_id로 정렬한다.
    5. RETURNS TABLE, LANGUAGE sql, STABLE, STRICT를 사용한다.
    6. 기준 재고 70으로 호출하여 결과를 확인한다.

  샘플 데이터 기준 예상 대상
product_id|product_name|stock_qty|shortage_qty|unit_price|
----------+------------+---------+------------+----------+
         3|27인치 모니터    |       40|          30| 329000.00|
         5|웹캠          |       60|          10|  79000.00|
*/

-- 아래에 함수 정의와 호출문을 작성하세요.

CREATE OR REPLACE FUNCTION proc_lab.fn_products_below_stock(p_threshold integer)
RETURNS TABLE (
    product_id   bigint,
    product_name varchar,
    stock_qty    integer,
    shortage_qty integer,
    unit_price   numeric
)
LANGUAGE sql
STABLE
STRICT
AS $function$
    SELECT p.product_id,
           p.product_name,
           p.stock_qty,
           p_threshold - p.stock_qty AS shortage_qty,
           p.unit_price
      FROM proc_lab.products AS p
     WHERE p.active = true
       AND p.stock_qty < p_threshold
     ORDER BY p.stock_qty, p.product_id;
$function$;

SELECT * FROM proc_lab.fn_products_below_stock(70);

-- ============================================================================
-- 문제 3. [함수·13점] 고객 주문 요약 JSONB 반환
-- ============================================================================

/*
  함수명
    proc_lab.fn_customer_order_summary_json(p_customer_id bigint)

  요구사항
    1. 다음 구조의 JSONB를 반환한다.

       {
         "customer": {
           "customer_id": ...,
           "name": ...,
           "email": ...,
           "grade": ...
         },
         "order_count": ...,
         "total_amount": ...
       }

    2. CANCELLED 주문은 주문 수와 누적금액에서 모두 제외한다.
    3. 주문이 없는 고객은 order_count=0, total_amount=0을 반환한다.
    4. 존재하지 않는 고객번호는 SQLSTATE P0002 예외를 발생시킨다.
    5. LANGUAGE plpgsql, STABLE, STRICT를 사용한다.
    6. 고객번호 1로 호출하고 jsonb_pretty()로 출력한다.

  샘플 데이터 기준 고객 1 예상값
    order_count  = 2
    total_amount = 305000.00
*/

-- 아래에 함수 정의와 호출문을 작성하세요.
CREATE OR REPLACE FUNCTION proc_lab.fn_customer_order_summary_json(
    p_customer_id bigint
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
STRICT
SET search_path = pg_catalog, proc_lab, pg_temp
AS $function$
DECLARE
    v_customer proc_lab.customers%ROWTYPE;
    v_order_count bigint;
    v_total_amount numeric(14,2);
BEGIN
    SELECT *
      INTO v_customer
      FROM proc_lab.customers
     WHERE customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = format('고객 ID %s가 존재하지 않습니다.', p_customer_id);
    END IF;

    SELECT count(*), coalesce(sum(o.total_amount), 0)::numeric(14,2)
      INTO v_order_count, v_total_amount
      FROM proc_lab.orders AS o
     WHERE o.customer_id = p_customer_id
       AND o.order_status <> 'CANCELLED';

    RETURN jsonb_build_object(
        'customer', jsonb_build_object(
            'name',        v_customer.customer_name,
            'email',       v_customer.email,
            'grade',       v_customer.customer_grade,
            'customer_id', v_customer.customer_id
        ),
        'order_count',  v_order_count,
        'total_amount', v_total_amount
    );
END;
$function$;

-- 기대: order_count=2, total_amount=305000.00 (jsonb_pretty()로 보기 좋게 출력)
SELECT jsonb_pretty(proc_lab.fn_customer_order_summary_json(1)) AS customer_order_summary;
SELECT (s.summary ->> 'order_count')::bigint AS actual_order_count,
       (s.summary ->> 'total_amount')::numeric(14,2) AS actual_total_amount,
       (s.summary ->> 'order_count')::bigint = 2
       AND (s.summary ->> 'total_amount')::numeric(14,2) = 305000.00
           AS matches_expected
  FROM (
        SELECT proc_lab.fn_customer_order_summary_json(1) AS summary
       ) AS s;


-- ============================================================================
-- 문제 4. [프로시저·15점] 상품 한 종류 주문 생성
-- ============================================================================

/*
  프로시저명
    proc_lab.pr_create_order(
        IN    p_customer_id bigint,
        IN    p_product_id  bigint,
        IN    p_quantity    integer,
        INOUT p_order_id    bigint DEFAULT NULL
    )

  요구사항
    1. 주문수량은 1 이상이어야 한다.
    2. 활성 고객과 활성 상품만 주문할 수 있다.
    3. 상품 행을 SELECT ... FOR UPDATE로 잠근다.
    4. 재고가 부족하면 예외를 발생시킨다.
    5. 상품 재고를 주문수량만큼 차감한다.
    6. orders에 PENDING 상태의 주문을 입력한다.
    7. total_amount는 상품 단가 × 주문수량으로 계산한다.
    8. 생성된 order_id를 RETURNING ... INTO로 p_order_id에 반환한다.
    9. order_items에 주문 상세를 입력한다.
   10. 고객 1, 상품 2, 수량 3으로 호출하고 결과를 확인한다.

  테스트 권장
    BEGIN;
    CALL proc_lab.pr_create_order(1, 2, 3, NULL);
    -- orders, order_items, products 확인
    ROLLBACK;
*/

-- 아래에 프로시저 정의와 호출·검증문을 작성하세요.
-- 가장 최근 주문 확인
CREATE OR REPLACE PROCEDURE proc_lab.pr_create_order(
    IN    p_customer_id bigint,
    IN    p_product_id  bigint,
    IN    p_quantity    integer,
    INOUT p_order_id    bigint DEFAULT NULL
)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_customer_active boolean;
    v_product_active  boolean;
    v_stock_qty       integer;
    v_unit_price      numeric(12,2);
    v_total_amount    numeric(14,2);
BEGIN
    IF p_quantity IS NULL OR p_quantity < 1 THEN
        RAISE EXCEPTION '주문 수량은 1 이상이어야 합니다. 입력값: %', p_quantity
            USING ERRCODE = '22023';
    END IF;

    SELECT c.active
      INTO v_customer_active
      FROM proc_lab.customers AS c
     WHERE c.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION '고객 ID %가 존재하지 않습니다.', p_customer_id
            USING ERRCODE = 'P0002';
    ELSIF NOT v_customer_active THEN
        RAISE EXCEPTION '고객 ID %는 비활성 상태입니다.', p_customer_id
            USING ERRCODE = 'P0001';
    END IF;

    SELECT p.active, p.stock_qty, p.unit_price
      INTO v_product_active, v_stock_qty, v_unit_price
      FROM proc_lab.products AS p
     WHERE p.product_id = p_product_id
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '상품 ID %가 존재하지 않습니다.', p_product_id
            USING ERRCODE = 'P0002';
    ELSIF NOT v_product_active THEN
        RAISE EXCEPTION '상품 ID %는 비활성 상태입니다.', p_product_id
            USING ERRCODE = 'P0001';
    ELSIF v_stock_qty < p_quantity THEN
        RAISE EXCEPTION '상품 ID %의 재고가 부족합니다. 현재 재고: %, 요청 수량: %',
            p_product_id, v_stock_qty, p_quantity
            USING ERRCODE = 'P0001';
    END IF;

    v_total_amount := (v_unit_price * p_quantity)::numeric(14,2);

    UPDATE proc_lab.products
       SET stock_qty = stock_qty - p_quantity
     WHERE product_id = p_product_id;

    INSERT INTO proc_lab.orders (customer_id, order_status, total_amount)
    VALUES (p_customer_id, 'PENDING', v_total_amount)
    RETURNING order_id INTO p_order_id;

    INSERT INTO proc_lab.order_items (order_id, product_id, quantity, unit_price)
    VALUES (p_order_id, p_product_id, p_quantity, v_unit_price);
END;
$procedure$;

-- 테스트: 원본 상품 2 재고=150
BEGIN;
CALL proc_lab.pr_create_order(1, 2, 3, NULL);
-- 실행결과: p_order_id = 6

SELECT product_id, stock_qty FROM proc_lab.products WHERE product_id = 2;
-- 실행결과: product_id=2, stock_qty=147 (150-3)

SELECT o.order_id, o.customer_id, o.order_status, o.total_amount,
       oi.product_id, oi.quantity, oi.unit_price, oi.line_amount
  FROM proc_lab.orders AS o
  JOIN proc_lab.order_items AS oi ON oi.order_id = o.order_id
 WHERE o.order_id = currval(pg_get_serial_sequence('proc_lab.orders', 'order_id'));
-- 실행결과: order_id=6, customer_id=1, order_status=PENDING, total_amount=147000.00,
--          product_id=2, quantity=3, unit_price=49000.00, line_amount=147000.00
ROLLBACK;


-- ============================================================================
-- 문제 5. [프로시저·15점] 주문 상태 전환 및 이력 저장
-- ============================================================================

/*
  프로시저명
    proc_lab.pr_change_order_status(
        IN  p_order_id   bigint,
        IN  p_new_status text,
        OUT p_message    text
    )

  허용 상태 전환
    PENDING  → PAID 또는 CANCELLED
    PAID     → SHIPPING 또는 CANCELLED
    SHIPPING → COMPLETED
    COMPLETED, CANCELLED → 더 이상 변경 불가

  요구사항
    1. 새로운 상태는 PENDING, PAID, SHIPPING, COMPLETED, CANCELLED 중 하나다.
    2. 주문을 SELECT ... FOR UPDATE로 조회한다.
    3. 존재하지 않는 주문은 SQLSTATE P0002 예외를 발생시킨다.
    4. 현재 상태와 새 상태가 같으면 변경하지 않고 안내 메시지를 반환한다.
    5. 허용되지 않은 상태 전환은 SQLSTATE P0001 예외를 발생시킨다.
    6. 정상 전환이면 orders의 order_status와 updated_at을 변경한다.
    7. order_status_history에 이전 상태와 새 상태를 저장한다.
    8. 주문 2를 COMPLETED로 변경하여 결과와 이력을 확인한다.

  테스트 권장
    BEGIN;
    CALL proc_lab.pr_change_order_status(2, 'COMPLETED', NULL);
    -- orders, order_status_history 확인
    ROLLBACK;
*/

-- 아래에 프로시저 정의와 호출·검증문을 작성하세요.
CREATE OR REPLACE PROCEDURE proc_lab.pr_change_order_status(
    IN  p_order_id   bigint,
    IN  p_new_status text,
    OUT p_message    text
)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_old_status varchar(20);
    v_new_status text := upper(btrim(p_new_status));
BEGIN
    IF p_new_status IS NULL OR v_new_status NOT IN
       ('PENDING', 'PAID', 'SHIPPING', 'COMPLETED', 'CANCELLED') THEN
        RAISE EXCEPTION '유효하지 않은 주문 상태입니다: %', p_new_status
            USING ERRCODE = '22023';
    END IF;

    SELECT o.order_status
      INTO v_old_status
      FROM proc_lab.orders AS o
     WHERE o.order_id = p_order_id
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0002',
            MESSAGE = format('주문 ID %s가 존재하지 않습니다.', p_order_id);
    END IF;

    IF v_old_status = v_new_status THEN
        p_message := format('주문 %s은(는) 이미 %s 상태입니다.', p_order_id, v_old_status);
        RETURN;
    END IF;

    IF NOT (
           (v_old_status = 'PENDING'  AND v_new_status IN ('PAID', 'CANCELLED'))
        OR (v_old_status = 'PAID'     AND v_new_status IN ('SHIPPING', 'CANCELLED'))
        OR (v_old_status = 'SHIPPING' AND v_new_status = 'COMPLETED')
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = 'P0001',
            MESSAGE = format(
                '허용되지 않은 주문 상태 전환입니다: %s -> %s',
                v_old_status, v_new_status
            );
    END IF;

    UPDATE proc_lab.orders
       SET order_status = v_new_status,
           updated_at = clock_timestamp()
     WHERE order_id = p_order_id;

    INSERT INTO proc_lab.order_status_history
           (order_id, old_status, new_status, changed_by)
    VALUES (p_order_id, v_old_status, v_new_status, session_user);

    p_message := format(
        '주문 %s의 상태가 %s에서 %s(으)로 변경되었습니다.',
        p_order_id, v_old_status, v_new_status
    );
END;
$procedure$;

-- 테스트: 주문 2는 SHIPPING
BEGIN;
CALL proc_lab.pr_change_order_status(2, 'COMPLETED', NULL);
-- 실행결과: p_message = '주문 2의 상태가 SHIPPING에서 COMPLETED(으)로 변경되었습니다.'

SELECT order_id, order_status FROM proc_lab.orders WHERE order_id = 2;
-- 실행결과: order_id=2, order_status=COMPLETED

SELECT order_id, old_status, new_status
  FROM proc_lab.order_status_history
 WHERE order_id = 2
 ORDER BY history_id DESC LIMIT 1;
-- 실행결과: order_id=2, old_status=SHIPPING, new_status=COMPLETED
ROLLBACK;


-- ============================================================================
-- 문제 6. [프로시저·15점] 멱등성이 보장되는 일괄 할인
-- ============================================================================

/*
  프로시저명
    proc_lab.pr_bulk_discount_once(
        IN  p_batch_key        text,
        IN  p_discount_percent numeric,
        IN  p_min_price        numeric,
        OUT p_affected         integer
    )

  요구사항
    1. p_batch_key는 NULL 또는 빈 문자열일 수 없다.
    2. 할인율은 0 초과 50 이하이어야 한다.
    3. 최소가격은 0 이상이어야 한다.
    4. bulk_discount_runs에 batch_key를 먼저 등록한다.
    5. ON CONFLICT DO NOTHING과 ROW_COUNT를 이용해 최초 요청인지 판단한다.
    6. 최초 요청일 때만 active=true이고 최소가격 이상인 상품에 할인을 적용한다.
    7. 할인 가격은 소수점 둘째 자리까지 반올림한다.
    8. 처리 건수와 COMPLETED 상태를 bulk_discount_runs에 저장한다.
    9. 같은 batch_key와 같은 조건으로 다시 호출하면 할인하지 않고
       최초 처리 건수를 반환한다.
   10. 같은 batch_key를 다른 할인 조건으로 재사용하면 예외를 발생시킨다.

  호출 예
    CALL proc_lab.pr_bulk_discount_once(
        'DAY04-SALE-001', 10, 70000, NULL
    );

    -- 같은 키로 한 번 더 호출하여 가격이 재할인되지 않는지 확인한다.
*/

-- 아래에 프로시저 정의와 호출·검증문을 작성하세요.
CREATE OR REPLACE PROCEDURE proc_lab.pr_bulk_discount_once(
    IN  p_batch_key        text,
    IN  p_discount_percent numeric,
    IN  p_min_price        numeric,
    OUT p_affected         integer
)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_run      proc_lab.bulk_discount_runs%ROWTYPE;
    v_inserted integer;
BEGIN
    IF p_batch_key IS NULL OR btrim(p_batch_key) = '' THEN
        RAISE EXCEPTION 'batch_key는 비어 있을 수 없습니다.'
            USING ERRCODE = '22023';
    END IF;
    IF p_discount_percent IS NULL
       OR p_discount_percent <= 0
       OR p_discount_percent > 50 THEN
        RAISE EXCEPTION '할인율은 0 초과 50 이하여야 합니다. 입력값: %',
            p_discount_percent USING ERRCODE = '22023';
    END IF;
    IF p_min_price IS NULL OR p_min_price < 0 THEN
        RAISE EXCEPTION '최소 가격은 0 이상이어야 합니다. 입력값: %',
            p_min_price USING ERRCODE = '22023';
    END IF;

    INSERT INTO proc_lab.bulk_discount_runs
           (batch_key, discount_percent, min_price)
    VALUES (btrim(p_batch_key), p_discount_percent, p_min_price)
    ON CONFLICT (batch_key) DO NOTHING;

    GET DIAGNOSTICS v_inserted = ROW_COUNT;

    IF v_inserted = 1 THEN
        -- active=true 이고 최소가격 이상인 상품에만 할인 적용
        UPDATE proc_lab.products
           SET unit_price = round(
               unit_price * (1 - p_discount_percent / 100.0), 2
           )
         WHERE active
           AND unit_price >= p_min_price;

        GET DIAGNOSTICS p_affected = ROW_COUNT;

        UPDATE proc_lab.bulk_discount_runs
           SET affected_count = p_affected,
               run_status = 'COMPLETED',
               completed_at = clock_timestamp()
         WHERE batch_key = btrim(p_batch_key);
    ELSE
        SELECT r.*
          INTO v_run
          FROM proc_lab.bulk_discount_runs AS r
         WHERE r.batch_key = btrim(p_batch_key)
           FOR UPDATE;

        IF v_run.discount_percent IS DISTINCT FROM p_discount_percent
           OR v_run.min_price IS DISTINCT FROM p_min_price THEN
            RAISE EXCEPTION
                'batch_key "%"가 다른 조건으로 이미 사용되었습니다. 기존(할인율 %, 최소가격 %), 요청(할인율 %, 최소가격 %)',
                btrim(p_batch_key),
                v_run.discount_percent, v_run.min_price,
                p_discount_percent, p_min_price
                USING ERRCODE = 'P0001';
        END IF;

        IF v_run.run_status <> 'COMPLETED' THEN
            RAISE EXCEPTION 'batch_key "%"의 최초 실행이 아직 완료되지 않았습니다.',
                btrim(p_batch_key) USING ERRCODE = 'P0001';
        END IF;

        p_affected := v_run.affected_count;
    END IF;
END;
$procedure$;

-- 테스트: min_price=70000 -> 키보드(89000)/모니터(329000)/웹캠(79000) 3개 대상
BEGIN;
CALL proc_lab.pr_bulk_discount_once('DAY04-SALE-001', 10, 70000, NULL);
-- 실행결과: p_affected = 3

SELECT product_id, product_name, unit_price FROM proc_lab.products ORDER BY product_id;
-- 실행결과:
-- 1 기계식 키보드  80100.00  (89000 * 0.9)
-- 2 무선 마우스    49000.00  (대상 아님, 변경 없음)
-- 3 27인치 모니터 296100.00  (329000 * 0.9)
-- 4 USB-C 허브     59000.00  (대상 아님, 변경 없음)
-- 5 웹캠           71100.00  (79000 * 0.9)

CALL proc_lab.pr_bulk_discount_once('DAY04-SALE-001', 10, 70000, NULL);
-- 실행결과: p_affected = 3 (같은 값 재반환, 재할인 없음)

SELECT batch_key, affected_count, run_status FROM proc_lab.bulk_discount_runs;
-- 실행결과: DAY04-SALE-001, affected_count=3, run_status=COMPLETED

SELECT product_id, unit_price FROM proc_lab.products WHERE product_id IN (1,3,5);
-- 실행결과: 1=80100.00, 3=296100.00, 5=71100.00 (두 번째 호출 후에도 동일 = 중복 할인 안 됨)
ROLLBACK;


-- ============================================================================
-- 문제 7. [트리거·10점] orders 변경 자동 감사
-- ============================================================================

/*
  트리거 반환 함수명
    proc_lab.fn_audit_orders()

  트리거명
    trg_orders_audit

  요구사항
    1. orders 테이블의 INSERT, UPDATE, DELETE를 감사한다.
    2. AFTER, FOR EACH ROW 트리거로 만든다.
    3. TG_TABLE_NAME과 TG_OP를 audit_log에 저장한다.
    4. INSERT는 new_data, DELETE는 old_data,
       UPDATE는 old_data와 new_data를 모두 JSONB로 저장한다.
    5. row_id에는 변경된 order_id를 저장한다.
    6. changed_by에는 실제 접속 사용자인 session_user를 저장한다.
    7. 함수는 SECURITY DEFINER로 만들고 search_path를
       pg_catalog, proc_lab, pg_temp 순서로 고정한다.
    8. 주문 1의 note를 변경한 뒤 audit_log를 확인한다.

  테스트 권장
    BEGIN;
    UPDATE proc_lab.orders
       SET note = '문제 7 감사 테스트'
     WHERE order_id = 1;
    SELECT * FROM proc_lab.audit_log ORDER BY audit_id DESC;
    ROLLBACK;
*/

-- 아래에 트리거 함수, 트리거, 테스트문을 작성하세요.
CREATE OR REPLACE FUNCTION proc_lab.fn_audit_orders()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, proc_lab, pg_temp
AS $function$
DECLARE
    v_row_id bigint;
BEGIN
    v_row_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.order_id ELSE NEW.order_id END;

    INSERT INTO proc_lab.audit_log
           (table_name, operation, row_id, old_data, new_data, changed_by)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        v_row_id,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END,
        session_user
    );

    RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER trg_orders_audit
AFTER INSERT OR UPDATE OR DELETE ON proc_lab.orders
FOR EACH ROW
EXECUTE FUNCTION proc_lab.fn_audit_orders();

-- 테스트: 주문 1의 note 변경
BEGIN;
UPDATE proc_lab.orders
   SET note = '문제 7 감사 테스트'
 WHERE order_id = 1;

SELECT operation, row_id,
       old_data ->> 'note' AS old_note,
       new_data ->> 'note' AS new_note
  FROM proc_lab.audit_log
 ORDER BY audit_id DESC
 LIMIT 1;
-- 실행결과: operation=UPDATE, row_id=1,
--          old_note='오전 배송 희망', new_note='문제 7 감사 테스트'
ROLLBACK;


-- ============================================================================
-- 문제 8. [트리거·10점] 주문 상세 변경 시 주문 총액 자동 재계산
-- ============================================================================

/*
  트리거 함수명
    proc_lab.fn_sync_order_total()

  트리거명
    trg_order_items_sync_total

  요구사항
    1. order_items의 INSERT, UPDATE, DELETE 후 실행한다.
    2. FOR EACH ROW 트리거로 만든다.
    3. 해당 주문의 line_amount 합계를 orders.total_amount에 저장한다.
    4. 주문 상세가 하나도 없으면 total_amount를 0으로 저장한다.
    5. total_amount 변경과 함께 updated_at도 현재 시각으로 변경한다.
    6. INSERT/UPDATE에서는 NEW.order_id를 사용한다.
    7. DELETE에서는 OLD.order_id를 사용한다.
    8. UPDATE로 order_id 자체가 바뀔 가능성까지 고려하여,
       OLD.order_id와 NEW.order_id가 다르면 양쪽 주문을 모두 재계산한다.
    9. 주문 3에 상품 1을 추가·수정·삭제하면서 총액 변화를 확인한다.

  샘플 데이터 기준 주문 3
    기존 총액                  : 118000
    상품 1, 수량 2 추가 후    : 296000
    추가 상품 수량을 3으로 수정: 385000
    추가 상품 삭제 후          : 118000
*/

-- 아래에 트리거 함수, 트리거, 테스트문을 작성하세요.
CREATE OR REPLACE FUNCTION proc_lab.fn_sync_order_total()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    v_old_order_id bigint;
    v_new_order_id bigint;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_old_order_id := OLD.order_id;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_new_order_id := NEW.order_id;
    END IF;

    IF v_old_order_id IS NOT NULL THEN
        UPDATE proc_lab.orders AS o
           SET total_amount = coalesce(
                   (SELECT sum(oi.line_amount)
                      FROM proc_lab.order_items AS oi
                     WHERE oi.order_id = v_old_order_id),
                   0
               ),
               updated_at = clock_timestamp()
         WHERE o.order_id = v_old_order_id;
    END IF;

    IF v_new_order_id IS NOT NULL
       AND v_new_order_id IS DISTINCT FROM v_old_order_id THEN
        UPDATE proc_lab.orders AS o
           SET total_amount = coalesce(
                   (SELECT sum(oi.line_amount)
                      FROM proc_lab.order_items AS oi
                     WHERE oi.order_id = v_new_order_id),
                   0
               ),
               updated_at = clock_timestamp()
         WHERE o.order_id = v_new_order_id;
    END IF;

    RETURN NULL;
END;
$function$;

CREATE OR REPLACE TRIGGER trg_order_items_sync_total
AFTER INSERT OR UPDATE OR DELETE ON proc_lab.order_items
FOR EACH ROW
EXECUTE FUNCTION proc_lab.fn_sync_order_total();

-- 테스트: 주문 3 시작 총액 118000
BEGIN;
INSERT INTO proc_lab.order_items (order_id, product_id, quantity, unit_price)
VALUES (3, 1, 2, 89000);
SELECT order_id, total_amount FROM proc_lab.orders WHERE order_id = 3;
-- 실행결과: total_amount = 296000.00 (118000 + 89000*2)

UPDATE proc_lab.order_items
   SET quantity = 3
 WHERE order_id = 3
   AND product_id = 1;
SELECT order_id, total_amount FROM proc_lab.orders WHERE order_id = 3;
-- 실행결과: total_amount = 385000.00 (118000 + 89000*3)

DELETE FROM proc_lab.order_items
 WHERE order_id = 3
   AND product_id = 1;
SELECT order_id, total_amount FROM proc_lab.orders WHERE order_id = 3;
-- 실행결과: total_amount = 118000.00 (원상 복구)
ROLLBACK;


-- ============================================================================
-- 제출 전 최종 점검
-- ============================================================================

/*
  □ 함수 3개를 CREATE OR REPLACE FUNCTION으로 작성했는가?
  □ 함수마다 요구된 반환 타입과 변동성 속성을 지정했는가?
  □ 프로시저 3개를 CALL로 실행하고 결과를 검증했는가?
  □ 동시 변경 가능성이 있는 주문·상품 행에 FOR UPDATE를 사용했는가?
  □ 일괄 할인에 같은 batch_key를 두 번 호출해 멱등성을 확인했는가?
  □ 트리거 함수 2개와 실제 트리거 2개를 모두 생성했는가?
  □ OLD, NEW, TG_OP를 작업 종류에 맞게 사용했는가?
  □ 테스트 DML을 ROLLBACK하여 초기 샘플 데이터를 보존했는가?
  □ 제출 SQL이 위에서 아래로 오류 없이 실행되는가?
*/
