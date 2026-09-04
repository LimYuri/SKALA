from datetime import datetime

from app.analytics.repository import AnalyticsRepository


def test_java_local_datetime_array_is_supported():
    value = AnalyticsRepository()._as_datetime([2026, 8, 27, 10, 20, 30, 123456789])
    assert value == datetime(2026, 8, 27, 10, 20, 30, 123456)
