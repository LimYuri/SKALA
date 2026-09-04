import json
import logging
import threading
from datetime import date

from kafka import KafkaConsumer

from app.analytics.repository import analytics_repository
from app.config.settings import settings

logger = logging.getLogger(__name__)


class RentalEventConsumer:
    """기존 완료 이벤트와 신규 대여 생명주기 이벤트를 함께 수신한다."""

    def __init__(self):
        self.topics = [
            settings.kafka_topic_enrollment_completed,
            settings.kafka_topic_rental_lifecycle,
        ]
        self.consumer = None
        self._running = False

    def start(self):
        """별도 스레드로 Kafka Consumer 시작"""
        self._running = True
        thread = threading.Thread(target=self._consume, daemon=True)
        thread.start()
        logger.info("[KafkaConsumer] 시작 - topics: %s", self.topics)

    def stop(self):
        self._running = False
        if self.consumer:
            self.consumer.close()

    def _consume(self):
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_consumer_group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=1000,
            )

            while self._running:
                for message in self.consumer:
                    if not self._running:
                        break
                    self._handle_message(message.topic, message.value)

        except Exception as e:
            logger.error(f"[KafkaConsumer] 오류 발생: {e}")
        finally:
            if self.consumer:
                self.consumer.close()

    def _handle_message(self, topic: str, event: dict):
        try:
            if topic == settings.kafka_topic_rental_lifecycle:
                analytics_repository.upsert_event({
                    "event_id": event["eventId"],
                    "event_time": event["occurredAt"],
                    "event_type": event["eventType"],
                    "request_id": event.get("requestId"),
                    "user_id": event.get("userId"),
                    "group_id": event["groupId"],
                    "asset_id": event.get("assetId"),
                    "category": event["category"],
                    "quantity": event.get("quantity", 1),
                    "loan_days": self._loan_days(
                        event.get("requestedFrom"), event.get("dueDate")
                    ),
                })
                logger.info(
                    "[KafkaConsumer] rental.lifecycle 저장 - type: %s, requestId: %s",
                    event.get("eventType"),
                    event.get("requestId"),
                )
                return

            logger.info(
                "[KafkaConsumer] enrollment.completed 수신 - enrollmentId: %s",
                event.get("enrollmentId"),
            )

        except Exception as e:
            logger.error(f"[KafkaConsumer] 메시지 처리 실패: {e}, event: {event}")

    @staticmethod
    def _loan_days(requested_from, due_date) -> int | None:
        if not requested_from or not due_date:
            return None
        start = RentalEventConsumer._as_date(requested_from)
        end = RentalEventConsumer._as_date(due_date)
        return max(1, (end - start).days + 1)

    @staticmethod
    def _as_date(value) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, (list, tuple)):
            return date(int(value[0]), int(value[1]), int(value[2]))
        return date.fromisoformat(str(value))


enrollment_consumer = RentalEventConsumer()
