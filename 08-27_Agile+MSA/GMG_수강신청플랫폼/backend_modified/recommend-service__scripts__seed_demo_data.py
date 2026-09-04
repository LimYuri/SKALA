"""GearHub Campus 시연용 운영 데이터와 분석 이력을 분리해 생성한다."""

import argparse
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymysql
import bcrypt
from pymysql.cursors import DictCursor

from app.analytics.forecast import DemandForecaster
from app.analytics.repository import analytics_repository
from app.analytics.simulation import generate_simulation_events
from app.config.settings import settings


GROUPS = [
    ("컴퓨터공학과", "computer-science", "CSE2026A", "수업과 캡스톤 프로젝트 장비를 운영합니다."),
    ("AI 연구실", "ai-lab", "AILAB26A", "GPU 노트북과 데이터 수집 장비를 공유합니다."),
    ("방송영상 동아리", "media-club", "MEDIA26A", "촬영·음향·편집 장비를 운영합니다."),
    ("메이커스 클럽", "makers-club", "MAKER26", "제작과 프로토타이핑 장비를 공유합니다."),
    ("전자공학 실습실", "electronics-lab", "EE2026AA", "회로·IoT 실습 장비를 관리합니다."),
    ("창업지원단", "startup-center", "START26A", "창업팀의 발표와 개발 장비를 지원합니다."),
    ("건축학과 설계실", "architecture-studio", "ARCH26AA", "설계·측정·제작 장비를 운영합니다."),
    ("학생회 행사팀", "student-events", "EVENT26A", "교내 행사에 필요한 음향과 발표 장비를 공유합니다."),
]

DEMO_PASSWORD = "GearHub123!"
DEMO_ADMIN_EMAIL = "campus.admin@demo.local"
DEMO_MEMBER_EMAIL = "campus.member@demo.local"

ASSET_CATALOG = [
    ("COMPUTER", "MacBook Pro 14 M3", 2890000, "고성능 개발·영상 편집 노트북"),
    ("COMPUTER", "LG gram 16", 1790000, "수업과 팀 프로젝트용 경량 노트북"),
    ("COMPUTER", "Dell Precision 워크스테이션", 3200000, "3D·AI 연산용 모바일 워크스테이션"),
    ("DEVICE", "iPad Pro 12.9", 1590000, "디자인 검토와 모바일 테스트 태블릿"),
    ("DEVICE", "iPhone 15 Pro", 1550000, "iOS 앱 테스트 기기"),
    ("DEVICE", "Galaxy S24", 1150000, "Android 앱 테스트 기기"),
    ("CAMERA_AUDIO", "Sony A7 IV 카메라", 3090000, "행사·콘텐츠 촬영용 미러리스 카메라"),
    ("CAMERA_AUDIO", "DJI Pocket 3", 790000, "이동 촬영용 짐벌 카메라"),
    ("CAMERA_AUDIO", "Rode Wireless GO II", 420000, "인터뷰·발표 녹음용 무선 마이크"),
    ("PRESENTATION", "Epson 레이저 프로젝터", 2100000, "강의·행사용 고광량 프로젝터"),
    ("PRESENTATION", "휴대용 스크린 100인치", 280000, "행사용 이동식 스크린"),
    ("PRESENTATION", "Logitech 프레젠터", 89000, "발표용 무선 포인터"),
    ("ELECTRONICS_IOT", "Raspberry Pi 5 키트", 180000, "IoT·임베디드 프로젝트 키트"),
    ("ELECTRONICS_IOT", "Arduino 센서 키트", 120000, "회로·센서 실습용 키트"),
    ("ELECTRONICS_IOT", "디지털 오실로스코프", 680000, "전자회로 측정 장비"),
    ("MAKER", "Bambu Lab 3D 프린터", 980000, "프로토타입 제작용 3D 프린터"),
    ("MAKER", "Bosch 레이저 거리측정기", 190000, "공간·구조 측정 장비"),
    ("MAKER", "정밀 공구 세트", 240000, "제작·조립용 공구 세트"),
    ("ACCESSORY", "USB-C 멀티 허브", 79000, "노트북 연결용 멀티 허브"),
    ("ACCESSORY", "Anker 보조배터리", 99000, "현장 활동용 대용량 배터리"),
    ("ACCESSORY", "삼각대·조명 세트", 230000, "촬영과 발표용 조명 세트"),
    ("COMPUTER", "NVIDIA RTX 개발 PC", 4100000, "AI·렌더링 실습용 데스크톱"),
    ("CAMERA_AUDIO", "Zoom H6 레코더", 520000, "다채널 현장 음향 레코더"),
    ("PRESENTATION", "JBL 이동식 PA 스피커", 890000, "행사용 이동식 음향 장비"),
]

ACQUISITIONS = [
    ("고성능 GPU 노트북", "COMPUTER", 3600000, 2),
    ("열화상 카메라", "CAMERA_AUDIO", 1850000, 1),
    ("휴대용 빔프로젝터", "PRESENTATION", 920000, 2),
    ("LiDAR 거리 센서", "ELECTRONICS_IOT", 430000, 4),
    ("레이저 커터", "MAKER", 5900000, 1),
    ("VR 헤드셋", "DEVICE", 780000, 3),
    ("무선 핀마이크 세트", "CAMERA_AUDIO", 640000, 2),
    ("Thunderbolt 도킹스테이션", "ACCESSORY", 390000, 5),
]


def connect():
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def seed_operational_data(seed: int = 42) -> dict:
    rng = random.Random(seed)
    now = datetime.now().replace(microsecond=0)
    marker = "https://demo.gearhub.local/"

    with connect() as connection:
        with connection.cursor() as cursor:
            password_hash = bcrypt.hashpw(
                DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=10)
            ).decode("utf-8")
            cursor.executemany(
                """
                INSERT INTO users (email,password,name,role,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE password=VALUES(password), name=VALUES(name),
                    role=VALUES(role), updated_at=VALUES(updated_at)
                """,
                [
                    (DEMO_ADMIN_EMAIL, password_hash, "캠퍼스 관리자", "INSTRUCTOR", now, now),
                    (DEMO_MEMBER_EMAIL, password_hash, "캠퍼스 구성원", "STUDENT", now, now),
                ],
            )
            cursor.execute("SELECT id,password FROM users WHERE email=%s", (DEMO_ADMIN_EMAIL,))
            instructor = cursor.fetchone()
            cursor.execute("SELECT id,password FROM users WHERE email=%s", (DEMO_MEMBER_EMAIL,))
            student = cursor.fetchone()
            instructor_id, student_id = int(instructor["id"]), int(student["id"])
            demo_password = student["password"]

            group_ids = []
            for name, slug, invite_code, description in GROUPS:
                cursor.execute(
                    """
                    INSERT INTO campus_groups
                        (name, slug, description, invite_code, created_by, status, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,'ACTIVE',%s,%s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description),
                        invite_code=VALUES(invite_code), status='ACTIVE', updated_at=VALUES(updated_at)
                    """,
                    (name, slug, description, invite_code, instructor_id, now, now),
                )
                cursor.execute("SELECT id FROM campus_groups WHERE slug=%s", (slug,))
                group_ids.append(int(cursor.fetchone()["id"]))

            demo_user_ids = []
            for index in range(1, 33):
                email = f"demo.student{index:02d}@gearhub.local"
                cursor.execute(
                    """
                    INSERT INTO users (email,password,name,role,created_at,updated_at)
                    VALUES (%s,%s,%s,'STUDENT',%s,%s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name), updated_at=VALUES(updated_at)
                    """,
                    (email, demo_password, f"데모학생 {index:02d}", now, now),
                )
                cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                demo_user_ids.append(int(cursor.fetchone()["id"]))

            memberships = []
            for group_id in group_ids:
                memberships.extend([
                    (group_id, instructor_id, "MANAGER", "ACTIVE", now, now),
                    (group_id, student_id, "MEMBER", "ACTIVE", now, now),
                ])
            for index, user_id in enumerate(demo_user_ids):
                memberships.append((group_ids[index % len(group_ids)], user_id, "MEMBER", "ACTIVE", now, now))
            cursor.executemany(
                """
                INSERT INTO group_memberships (group_id,user_id,role,status,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE role=VALUES(role), status='ACTIVE', updated_at=VALUES(updated_at)
                """,
                memberships,
            )

            cursor.execute("SELECT id FROM courses WHERE purchase_url LIKE %s", (marker + "%",))
            old_course_ids = [row["id"] for row in cursor.fetchall()]
            if old_course_ids:
                placeholders = ",".join(["%s"] * len(old_course_ids))
                cursor.execute(f"DELETE FROM payments WHERE course_id IN ({placeholders})", old_course_ids)
                cursor.execute(f"DELETE FROM enrollments WHERE course_id IN ({placeholders})", old_course_ids)
                cursor.execute(f"DELETE FROM courses WHERE id IN ({placeholders})", old_course_ids)

            asset_rows = []
            locations = ["중앙도서관 1층", "공학관 301호", "학생회관 장비실", "창의공방", "미디어센터"]
            # 학교 공용 24개
            for index, (category, title, price, description) in enumerate(ASSET_CATALOG, start=1):
                quantity = rng.randint(2, 4)
                asset_rows.append((title, description, category, price, "OWNED", quantity, quantity,
                                   f"{marker}assets/org/{index}", None, "ORGANIZATION",
                                   locations[index % len(locations)], rng.choice([3, 5, 7, 14]),
                                   instructor_id, 0, "ACTIVE", 0, now, now))
            # 그룹별 12개, 총 96개
            for group_pos, group_id in enumerate(group_ids):
                for offset in range(12):
                    category, title, price, description = ASSET_CATALOG[(group_pos * 3 + offset) % len(ASSET_CATALOG)]
                    quantity = rng.randint(2, 4)
                    asset_rows.append((f"{title} · {GROUPS[group_pos][0]}", description, category, price,
                                       "OWNED", quantity, quantity,
                                       f"{marker}assets/group-{group_id}/{offset + 1}", group_id, "GROUP",
                                       f"{GROUPS[group_pos][0]} 운영실", rng.choice([3, 5, 7, 14]),
                                       instructor_id, 0, "ACTIVE", 0, now, now))
            cursor.executemany(
                """
                INSERT INTO courses
                    (title,description,category,price,item_type,total_quantity,available_quantity,
                     purchase_url,owner_group_id,visibility,pickup_location,max_loan_days,
                     instructor_id,enrollment_count,status,version,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                asset_rows,
            )
            cursor.execute("SELECT id,owner_group_id,total_quantity,max_loan_days FROM courses WHERE purchase_url LIKE %s AND item_type='OWNED'", (marker + "assets/%",))
            assets = list(cursor.fetchall())

            users_by_group = {group_id: [student_id] for group_id in group_ids}
            for index, user_id in enumerate(demo_user_ids):
                users_by_group[group_ids[index % len(group_ids)]].append(user_id)
            organization_assets = [asset for asset in assets if asset["owner_group_id"] is None]
            group_assets = {group_id: [asset for asset in assets if asset["owner_group_id"] == group_id] for group_id in group_ids}
            statuses = (["RETURNED"] * 112 + ["ACTIVE"] * 36 + ["RETURN_REQUESTED"] * 12
                        + ["PENDING"] * 24 + ["REJECTED"] * 16)
            rng.shuffle(statuses)
            loan_rows = []
            borrowed_counts = {}
            enrollment_counts = {}
            for index, status in enumerate(statuses):
                group_id = group_ids[index % len(group_ids)]
                asset = rng.choice(organization_assets + group_assets[group_id])
                course_id = int(asset["id"])
                user_id = rng.choice(users_by_group[group_id])
                created = now - timedelta(days=rng.randint(1, 150), hours=rng.randint(0, 10))
                max_days = max(1, int(asset["max_loan_days"] or 7))
                requested_from = created.date() + timedelta(days=rng.randint(0, 3))
                loan_days = rng.randint(1, max_days)
                due_date = requested_from + timedelta(days=loan_days - 1)
                approved_at = None
                returned_at = None
                reviewed_by = None
                review_comment = None
                if status in {"ACTIVE", "RETURN_REQUESTED", "RETURNED"}:
                    approved_at = created + timedelta(hours=rng.randint(2, 30))
                    reviewed_by = instructor_id
                    enrollment_counts[course_id] = enrollment_counts.get(course_id, 0) + 1
                if status == "RETURNED":
                    returned_at = datetime.combine(due_date, datetime.min.time()) + timedelta(hours=16)
                elif status in {"ACTIVE", "RETURN_REQUESTED"}:
                    # 일부 활성 대여를 의도적으로 연체 상태로 만든다.
                    if index % 4:
                        requested_from = date.today() - timedelta(days=rng.randint(1, 4))
                        due_date = date.today() + timedelta(days=rng.randint(1, max_days))
                    else:
                        requested_from = date.today() - timedelta(days=max_days + 3)
                        due_date = date.today() - timedelta(days=rng.randint(1, 4))
                    borrowed_counts[course_id] = borrowed_counts.get(course_id, 0) + 1
                elif status == "PENDING":
                    requested_from = date.today() + timedelta(days=rng.randint(0, 5))
                    due_date = requested_from + timedelta(days=min(max_days, rng.randint(2, 7)) - 1)
                elif status == "REJECTED":
                    reviewed_by = instructor_id
                    review_comment = rng.choice(["같은 일정에 예약이 겹칩니다.", "사용 목적과 장소를 보완해 주세요.", "현재 그룹 운영 범위를 벗어난 요청입니다."])
                loan_rows.append((user_id, course_id, group_id, "LOAN", rng.choice([
                    "캡스톤 프로젝트 구현 및 발표", "전공 수업 실습", "동아리 행사 운영",
                    "연구 데이터 수집", "프로토타입 제작과 사용자 테스트",
                ]), review_comment, requested_from, due_date, approved_at, returned_at,
                    reviewed_by, status, created, created))
            cursor.executemany(
                """
                INSERT INTO enrollments
                    (user_id,course_id,group_id,request_type,reason,review_comment,
                     requested_from,due_date,approved_at,returned_at,reviewed_by,status,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                loan_rows,
            )
            for asset in assets:
                course_id = int(asset["id"])
                available = max(0, int(asset["total_quantity"]) - borrowed_counts.get(course_id, 0))
                cursor.execute(
                    "UPDATE courses SET available_quantity=%s,enrollment_count=%s WHERE id=%s",
                    (available, enrollment_counts.get(course_id, 0), course_id),
                )

            acquisition_statuses = ["PENDING", "PENDING", "PENDING", "GROUP_APPROVED",
                                    "GROUP_APPROVED", "BUDGET_APPROVED", "BUDGET_APPROVED", "REJECTED"]
            for index, ((title, category, unit_price, quantity), status) in enumerate(zip(ACQUISITIONS, acquisition_statuses)):
                group_id = group_ids[index]
                cursor.execute(
                    """
                    INSERT INTO courses
                        (title,description,category,price,item_type,total_quantity,available_quantity,
                         purchase_url,owner_group_id,visibility,pickup_location,max_loan_days,
                         instructor_id,enrollment_count,status,version,created_at,updated_at)
                    VALUES (%s,%s,%s,%s,'PURCHASE_REQUEST',%s,0,%s,%s,'GROUP',NULL,7,%s,0,'INACTIVE',0,%s,%s)
                    """,
                    (title, "그룹 프로젝트 일정에 필요한 신규 장비", category, unit_price, quantity,
                     f"{marker}acquisitions/{index + 1}", group_id, student_id, now, now),
                )
                course_id = int(cursor.lastrowid)
                created = now - timedelta(days=8 - index)
                review_comment = "예산 대비 활용 계획을 보완해 주세요." if status == "REJECTED" else None
                reviewed_by = instructor_id if status != "PENDING" else None
                approved_at = created + timedelta(days=1) if status in {"GROUP_APPROVED", "BUDGET_APPROVED"} else None
                cursor.execute(
                    """
                    INSERT INTO enrollments
                        (user_id,course_id,group_id,request_type,reason,review_comment,
                         reviewed_by,approved_at,status,created_at,updated_at)
                    VALUES (%s,%s,%s,'PURCHASE',%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (student_id, course_id, group_id,
                     "다음 학기 프로젝트 수요가 예상되어 공동 장비 도입이 필요합니다.",
                     review_comment, reviewed_by, approved_at, status, created, created),
                )
                request_id = int(cursor.lastrowid)
                if status in {"GROUP_APPROVED", "BUDGET_APPROVED"}:
                    payment_status = "COMPLETED" if status == "BUDGET_APPROVED" else "PENDING"
                    transaction = f"DEMO-BUDGET-{index + 1:03d}" if payment_status == "COMPLETED" else None
                    cursor.execute(
                        """
                        INSERT INTO payments
                            (user_id,course_id,request_id,group_id,amount,status,transaction_id,created_at,updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (student_id, course_id, request_id, group_id, unit_price * quantity,
                         payment_status, transaction, created + timedelta(days=1), now),
                    )
        connection.commit()
    return {"groups": group_ids, "assets": len(asset_rows), "loans": len(loan_rows), "acquisitions": len(ACQUISITIONS)}


def seed_analytics(group_ids: list[int], seed: int = 42) -> dict:
    analytics_repository.ensure_schema()
    analytics_repository.clear_simulation_events()
    events = generate_simulation_events(group_ids, weeks=78, random_seed=seed)
    analytics_repository.insert_events(events)
    with analytics_repository.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM analytics_forecasts")
            cursor.execute("DELETE FROM analytics_forecast_runs")
    result = DemandForecaster(settings.forecast_horizon_weeks).train_and_forecast(events)
    run_id = analytics_repository.save_forecast_run(result)
    return {
        "events": len(events),
        "run_id": run_id,
        "model": result["model_name"],
        "baseline_wape": result["metrics"]["baseline_wape"],
        "model_wape": result["metrics"]["model_wape"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-analytics", action="store_true")
    args = parser.parse_args()
    operational = seed_operational_data(args.seed)
    print("운영 데이터:", operational)
    if not args.skip_analytics:
        analytics = seed_analytics(operational["groups"], args.seed)
        print("분석 데이터:", analytics)


if __name__ == "__main__":
    main()
