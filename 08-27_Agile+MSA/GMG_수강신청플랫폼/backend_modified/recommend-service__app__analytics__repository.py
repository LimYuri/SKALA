import json
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Optional

import pymysql
from pymysql.cursors import DictCursor

from app.config.settings import settings


class AnalyticsRepository:
    """분석 서비스가 논리적으로 소유하는 MariaDB 테이블 접근 계층."""

    @contextmanager
    def connection(self):
        connection = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def ensure_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS analytics_loan_events (
                event_id VARCHAR(64) NOT NULL,
                event_time DATETIME(6) NOT NULL,
                event_type VARCHAR(32) NOT NULL,
                request_id BIGINT,
                user_id BIGINT,
                group_id BIGINT NOT NULL,
                asset_id BIGINT,
                category VARCHAR(50) NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                loan_days INT,
                source VARCHAR(20) NOT NULL DEFAULT 'LIVE',
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (event_id),
                INDEX idx_analytics_event_time (event_time),
                INDEX idx_analytics_group_category (group_id, category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS analytics_forecast_runs (
                id BIGINT NOT NULL AUTO_INCREMENT,
                trained_at DATETIME(6) NOT NULL,
                model_name VARCHAR(80) NOT NULL,
                baseline_mae DECIMAL(12,4) NOT NULL,
                model_mae DECIMAL(12,4) NOT NULL,
                baseline_wape DECIMAL(12,4) NOT NULL,
                model_wape DECIMAL(12,4) NOT NULL,
                train_rows INT NOT NULL,
                test_rows INT NOT NULL,
                event_count INT NOT NULL,
                data_start DATE,
                data_end DATE,
                candidate_metrics LONGTEXT NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS analytics_forecasts (
                id BIGINT NOT NULL AUTO_INCREMENT,
                run_id BIGINT NOT NULL,
                group_id BIGINT NOT NULL,
                category VARCHAR(50) NOT NULL,
                week_start DATE NOT NULL,
                predicted_demand DECIMAL(12,4) NOT NULL,
                average_loan_days DECIMAL(8,2) NOT NULL,
                PRIMARY KEY (id),
                UNIQUE KEY uq_forecast_run_scope (run_id, group_id, category, week_start),
                INDEX idx_forecast_group (group_id, run_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ]
        with self.connection() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

    def upsert_event(self, event: dict, source: str = "LIVE") -> None:
        sql = """
            INSERT INTO analytics_loan_events (
                event_id, event_time, event_type, request_id, user_id,
                group_id, asset_id, category, quantity, loan_days, source
            ) VALUES (
                %(event_id)s, %(event_time)s, %(event_type)s, %(request_id)s,
                %(user_id)s, %(group_id)s, %(asset_id)s, %(category)s,
                %(quantity)s, %(loan_days)s, %(source)s
            )
            ON DUPLICATE KEY UPDATE
                event_time = VALUES(event_time),
                event_type = VALUES(event_type),
                loan_days = VALUES(loan_days)
        """
        params = {
            "event_id": event["event_id"],
            "event_time": self._as_datetime(event["event_time"]),
            "event_type": event["event_type"],
            "request_id": event.get("request_id"),
            "user_id": event.get("user_id"),
            "group_id": event["group_id"],
            "asset_id": event.get("asset_id"),
            "category": event["category"],
            "quantity": event.get("quantity", 1),
            "loan_days": event.get("loan_days"),
            "source": source,
        }
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)

    def insert_events(self, events: Iterable[dict], source: str = "SIMULATION") -> int:
        events = list(events)
        if not events:
            return 0
        sql = """
            INSERT INTO analytics_loan_events (
                event_id, event_time, event_type, request_id, user_id,
                group_id, asset_id, category, quantity, loan_days, source
            ) VALUES (
                %(event_id)s, %(event_time)s, %(event_type)s, %(request_id)s,
                %(user_id)s, %(group_id)s, %(asset_id)s, %(category)s,
                %(quantity)s, %(loan_days)s, %(source)s
            )
            ON DUPLICATE KEY UPDATE event_id = VALUES(event_id)
        """
        rows = []
        for event in events:
            rows.append({
                **event,
                "event_time": self._as_datetime(event["event_time"]),
                "source": source,
            })
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(sql, rows)
        return len(rows)

    def clear_simulation_events(self) -> int:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                return cursor.execute(
                    "DELETE FROM analytics_loan_events WHERE source = 'SIMULATION'"
                )

    def load_requested_events(self) -> list[dict]:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT event_id, event_time, group_id, category,
                           quantity, COALESCE(loan_days, 7) AS loan_days
                    FROM analytics_loan_events
                    WHERE event_type = 'REQUESTED'
                    ORDER BY event_time ASC
                """)
                return list(cursor.fetchall())

    def event_count(self) -> int:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS count FROM analytics_loan_events")
                row = cursor.fetchone()
                return int(row["count"])

    def save_forecast_run(self, result: dict) -> int:
        run_sql = """
            INSERT INTO analytics_forecast_runs (
                trained_at, model_name, baseline_mae, model_mae,
                baseline_wape, model_wape, train_rows, test_rows,
                event_count, data_start, data_end, candidate_metrics
            ) VALUES (
                %(trained_at)s, %(model_name)s, %(baseline_mae)s, %(model_mae)s,
                %(baseline_wape)s, %(model_wape)s, %(train_rows)s, %(test_rows)s,
                %(event_count)s, %(data_start)s, %(data_end)s, %(candidate_metrics)s
            )
        """
        forecast_sql = """
            INSERT INTO analytics_forecasts (
                run_id, group_id, category, week_start,
                predicted_demand, average_loan_days
            ) VALUES (
                %(run_id)s, %(group_id)s, %(category)s, %(week_start)s,
                %(predicted_demand)s, %(average_loan_days)s
            )
        """
        metrics = result["metrics"]
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(run_sql, {
                    "trained_at": result["trained_at"],
                    "model_name": result["model_name"],
                    "baseline_mae": metrics["baseline_mae"],
                    "model_mae": metrics["model_mae"],
                    "baseline_wape": metrics["baseline_wape"],
                    "model_wape": metrics["model_wape"],
                    "train_rows": result["train_rows"],
                    "test_rows": result["test_rows"],
                    "event_count": result["event_count"],
                    "data_start": result["data_start"],
                    "data_end": result["data_end"],
                    "candidate_metrics": json.dumps(
                        result["candidate_metrics"], ensure_ascii=False
                    ),
                })
                run_id = int(cursor.lastrowid)
                rows = [{**forecast, "run_id": run_id}
                        for forecast in result["forecasts"]]
                cursor.executemany(forecast_sql, rows)
                return run_id

    def latest_run(self) -> Optional[dict]:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM analytics_forecast_runs
                    ORDER BY id DESC LIMIT 1
                """)
                row = cursor.fetchone()
                if row is None:
                    return None
                row["candidate_metrics"] = json.loads(row["candidate_metrics"])
                return self._normalize_numbers(row)

    def load_forecasts(self, run_id: int, group_id: Optional[int] = None) -> list[dict]:
        sql = """
            SELECT group_id, category, week_start,
                   predicted_demand, average_loan_days
            FROM analytics_forecasts
            WHERE run_id = %(run_id)s
        """
        params = {"run_id": run_id}
        if group_id is not None:
            sql += " AND group_id = %(group_id)s"
            params["group_id"] = group_id
        sql += " ORDER BY group_id, category, week_start"
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return [self._normalize_numbers(row) for row in cursor.fetchall()]

    def _as_datetime(self, value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, (list, tuple)):
            parts = [int(part) for part in value]
            microsecond = parts[6] // 1000 if len(parts) > 6 else 0
            return datetime(
                parts[0], parts[1], parts[2],
                parts[3] if len(parts) > 3 else 0,
                parts[4] if len(parts) > 4 else 0,
                parts[5] if len(parts) > 5 else 0,
                microsecond,
            )
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)

    def _normalize_numbers(self, value):
        if isinstance(value, dict):
            return {key: self._normalize_numbers(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._normalize_numbers(item) for item in value]
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value
        return value


analytics_repository = AnalyticsRepository()
