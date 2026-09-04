from app.kafka.consumer import RentalEventConsumer


def test_loan_days_are_inclusive():
    assert RentalEventConsumer._loan_days("2026-08-27", "2026-08-29") == 3
    assert RentalEventConsumer._loan_days([2026, 8, 27], [2026, 8, 29]) == 3
    assert RentalEventConsumer._loan_days(None, "2026-08-29") is None
