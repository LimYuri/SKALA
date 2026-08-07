"""CSV/Parquet 저장 + 성능 측정 함수가 실제로 동작하는지 확인한다."""

from pathlib import Path

from app.models import WeatherReportRow
from app.storage import save_and_measure


def test_save_and_measure_creates_both_files_with_matching_row_counts(
    tmp_path: Path,
) -> None:
    """CSV/Parquet 파일이 모두 생성되고, 성능 결과 dict의 rows가 일치하는지 확인한다."""
    rows = [
        WeatherReportRow(
            time="2026-08-06T00:00:00",
            temperature_2m=25.0,
            precipitation_probability=10,
            country_name="Korea",
            capital="Seoul",
            country_population=51780579,
            ip_query="8.8.8.8",
            ip_city="Ashburn",
            ip_isp="Google LLC",
        )
    ]
    csv_path = tmp_path / "result.csv"
    parquet_path = tmp_path / "result.parquet"
    performance_path = tmp_path / "performance.json"

    performance = save_and_measure(rows, csv_path, parquet_path, performance_path)

    assert csv_path.exists()
    assert parquet_path.exists()
    assert performance_path.exists()
    assert performance["rows"] == 1
    assert performance["csv_write_seconds"] >= 0
    assert performance["parquet_read_seconds"] >= 0
