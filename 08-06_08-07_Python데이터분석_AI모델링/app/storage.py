"""검증이 끝난 데이터를 CSV·Parquet 두 형식으로 저장하고, 각각의
쓰기/읽기 소요 시간과 파일 크기를 측정해 비교한다.
"""

import json
from pathlib import Path
from time import perf_counter  # 짧은 I/O 시간차 비교에 적합한 고정밀 타이머
from typing import Any

import pandas as pd

from app.models import WeatherReportRow


def save_json(data: Any, file_path: Path) -> None:
    """딕셔너리/리스트를 사람이 읽기 쉬운 JSON으로 저장한다."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def save_and_measure(
    rows: list[WeatherReportRow],
    csv_path: Path,
    parquet_path: Path,
    performance_path: Path,
) -> dict[str, Any]:
    """CSV/Parquet 각각의 쓰기·읽기 시간과 파일 크기를 측정해 JSON으로도 남긴다."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame([row.model_dump() for row in rows])

    # ---- CSV 쓰기 / 읽기 ----
    write_start = perf_counter()
    dataframe.to_csv(csv_path, index=False, encoding="utf-8-sig")
    csv_write_seconds = perf_counter() - write_start

    read_start = perf_counter()
    csv_reloaded = pd.read_csv(csv_path)
    csv_read_seconds = perf_counter() - read_start

    # ---- Parquet 쓰기 / 읽기 ----
    write_start = perf_counter()
    dataframe.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
    parquet_write_seconds = perf_counter() - write_start

    read_start = perf_counter()
    parquet_reloaded = pd.read_parquet(parquet_path, engine="pyarrow")
    parquet_read_seconds = perf_counter() - read_start

    performance: dict[str, Any] = {
        "rows": len(dataframe),
        "csv_write_seconds": round(csv_write_seconds, 6),
        "csv_read_seconds": round(csv_read_seconds, 6),
        "csv_bytes": csv_path.stat().st_size,
        "parquet_write_seconds": round(parquet_write_seconds, 6),
        "parquet_read_seconds": round(parquet_read_seconds, 6),
        "parquet_bytes": parquet_path.stat().st_size,
    }

    if len(csv_reloaded) != len(dataframe) or len(parquet_reloaded) != len(dataframe):
        raise ValueError("저장한 행 수와 재로딩한 행 수가 일치하지 않습니다.")

    save_json(performance, performance_path)
    return performance
