"""[02] Pandas·Polars로 동일한 원천 데이터를 정제하고 결과를 교차 검증한다.

입력: data/raw의 월별 Yellow Taxi Parquet 파일
출력:
  - data/processed/trips_clean.csv
  - data/processed/trips_clean.parquet
  - outputs/tables/pandas_polars_comparison.json

Pandas와 Polars에 같은 필터·결측치·중복 처리·파생 컬럼 로직을 적용한 뒤
shape, 컬럼, 결측치, 논리 자료형, 주요 수치 요약을 비교한다.
"""
import json
import math
import time
import pandas as pd
import polars as pl
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "trips_clean.parquet"
OUT_CSV_PATH = ROOT / "data" / "processed" / "trips_clean.csv"
COMPARISON_PATH = ROOT / "outputs" / "tables" / "pandas_polars_comparison.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)

# 분석에 필요한 컬럼만 선택해 약 1,900만 행의 메모리 사용량을 줄인다.
COLS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
    "total_amount",
    "RatecodeID",
    "passenger_count",
]

RUSH_HOURS = set(range(7, 10)) | set(range(17, 20))  # 7-9시, 17-19시
RAW_FILES = sorted(RAW_DIR.glob("*.parquet"))

NUMERIC_COMPARE_COLS = [
    "trip_distance",
    "total_amount",
    "passenger_count",
    "trip_duration_minutes",
    "pickup_hour",
]


def normalize_pandas_dtype(dtype):
    """Pandas 자료형을 라이브러리 중립적인 논리 자료형으로 변환한다."""
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "datetime"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_integer_dtype(dtype):
        return "integer"
    if pd.api.types.is_float_dtype(dtype):
        return "float"
    if pd.api.types.is_string_dtype(dtype):
        return "string"
    return str(dtype)


def normalize_polars_dtype(dtype):
    """Polars 자료형을 Pandas와 비교 가능한 논리 자료형으로 변환한다."""
    dtype_name = str(dtype)
    if dtype_name.startswith("Datetime") or dtype_name == "Date":
        return "datetime"
    if dtype_name == "Boolean":
        return "boolean"
    if dtype_name.startswith(("Int", "UInt")):
        return "integer"
    if dtype_name.startswith("Float"):
        return "float"
    if dtype_name in {"String", "Utf8"}:
        return "string"
    return dtype_name

# --- 1. Pandas·Polars 원천 로딩 및 기본 EDA ---
# 같은 파일·컬럼을 각각 읽어 로딩 성능과 최초 shape를 함께 기록한다.
t0 = time.perf_counter()
pd_frames = [pd.read_parquet(f, columns=COLS) for f in RAW_FILES]
df = pd.concat(pd_frames, ignore_index=True)
pandas_load_sec = time.perf_counter() - t0

t0 = time.perf_counter()
pl_frames = [pl.read_parquet(f, columns=COLS) for f in RAW_FILES]
df_pl = pl.concat(pl_frames)
polars_load_sec = time.perf_counter() - t0

comparison = {
    "comparison_scope": "raw_load_shape_and_null_counts",
    "pandas_raw_shape": list(df.shape),
    "polars_raw_shape": [df_pl.height, df_pl.width],
    "same_raw_shape": list(df.shape) == [df_pl.height, df_pl.width],
    "same_raw_columns": list(df.columns) == df_pl.columns,
    "pandas_raw_null_counts": {key: int(value) for key, value in df.isna().sum().items()},
    "polars_raw_null_counts": {
        key: int(value) for key, value in df_pl.null_count().to_dicts()[0].items()
    },
}
comparison["same_raw_null_counts"] = (
    comparison["pandas_raw_null_counts"] == comparison["polars_raw_null_counts"]
)
print(f"pandas load: {pandas_load_sec:.2f}s, shape={df.shape}")
print(f"polars load: {polars_load_sec:.2f}s, shape={df_pl.shape}")
assert df.shape == df_pl.shape, "pandas/polars 로딩 결과 행/열 수가 다름"

# 결측치 EDA: RatecodeID는 NaN이 존재 -> 이후 ==1 필터로 자연히 제거되지만, 규모를 먼저 확인
print("\n결측치 개수 (pandas):")
print(df.isnull().sum())
print("\n결측치 개수 (polars):")
for column, count in df_pl.null_count().to_dicts()[0].items():
    print(f"{column}: {count}")

print(f"\nraw rows: {len(df):,}")

# --- 2. Pandas 정제 ---
# 기본 요금(RatecodeID==1, 공항 정액 등 특수 요금제 제외)과 평일 운행만 남긴다.
df = df[df["RatecodeID"] == 1]
df["pickup_weekday"] = df["tpep_pickup_datetime"].dt.weekday  # 0=월 ~ 6=일
df["is_weekday"] = df["pickup_weekday"] < 5
df = df[df["is_weekday"]]
print(f"after ratecode+weekday filter: {len(df):,}")

df["trip_duration_minutes"] = (
    df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
).dt.total_seconds() / 60

# 이상치 제거: 0분 이하/5시간 이상 운행, 음수·비현실적 거리(100마일+), 음수·비현실적 요금(500달러+)은
# 미터기 오류·데이터 입력 오류로 보고 제외 (임계값은 NYC TLC 공식 데이터 정제 가이드 기준 근사치)
df = df[
    (df["trip_duration_minutes"] > 0) & (df["trip_duration_minutes"] < 300)
    & (df["trip_distance"] > 0) & (df["trip_distance"] < 100)
    & (df["total_amount"] > 0) & (df["total_amount"] < 500)
]
print(f"after outlier removal: {len(df):,}")

missing_rows = int(df[COLS].isna().any(axis=1).sum())
# 필터 이후 남은 분석 컬럼의 결측 행을 명시적으로 제거한다.
df = df.dropna(subset=COLS).copy()
print(f"rows removed for missing values: {missing_rows:,}")

df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
df["is_rush_hour"] = df["pickup_hour"].isin(RUSH_HOURS)
df["analysis_group"] = df["is_rush_hour"].map({True: "출퇴근", False: "비출퇴근"})

duplicate_rows = int(df.duplicated().sum())
# 모든 원본·파생 컬럼이 동일한 완전 중복 행만 제거한다.
df = df.drop_duplicates().copy()
print(f"duplicate rows removed: {duplicate_rows:,}")

# --- 3. Polars 동일 정제 ---
# Pandas와 같은 순서와 조건을 적용해 비교 가능한 최종 스키마를 만든다.
df_pl_clean = (
    df_pl
    .filter(pl.col("RatecodeID") == 1)
    .with_columns(
        (pl.col("tpep_pickup_datetime").dt.weekday() - 1).alias("pickup_weekday")
    )
    .with_columns((pl.col("pickup_weekday") < 5).alias("is_weekday"))
    .filter(pl.col("is_weekday"))
    .with_columns(
        (
            (pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime"))
            .dt.total_seconds()
            / 60
        ).alias("trip_duration_minutes")
    )
    .filter(
        (pl.col("trip_duration_minutes") > 0)
        & (pl.col("trip_duration_minutes") < 300)
        & (pl.col("trip_distance") > 0)
        & (pl.col("trip_distance") < 100)
        & (pl.col("total_amount") > 0)
        & (pl.col("total_amount") < 500)
    )
    .drop_nulls(COLS)
    .with_columns(
        pl.col("RatecodeID").cast(pl.Float64),
        pl.col("passenger_count").cast(pl.Float64),
    )
    .with_columns(pl.col("tpep_pickup_datetime").dt.hour().alias("pickup_hour"))
    .with_columns(
        pl.col("pickup_hour").is_in(list(RUSH_HOURS)).alias("is_rush_hour")
    )
    .with_columns(
        pl.when(pl.col("is_rush_hour"))
        .then(pl.lit("출퇴근"))
        .otherwise(pl.lit("비출퇴근"))
        .alias("analysis_group")
    )
    .unique(maintain_order=True)
    .select(list(df.columns))
)

# --- 4. 정제 결과 교차 검증 ---
# 전체 행 값을 직접 비교하는 대신 평가에 필요한 구조·결측치·자료형·수치 요약을 검증한다.
comparison.update(
    {
        "comparison_scope": "raw_load_and_cleaned_result",
        "pandas_cleaned_shape": list(df.shape),
        "polars_cleaned_shape": [df_pl_clean.height, df_pl_clean.width],
        "same_cleaned_shape": list(df.shape)
        == [df_pl_clean.height, df_pl_clean.width],
        "pandas_cleaned_columns": list(df.columns),
        "polars_cleaned_columns": df_pl_clean.columns,
        "same_cleaned_columns": list(df.columns) == df_pl_clean.columns,
        "pandas_cleaned_null_counts": {
            key: int(value) for key, value in df.isna().sum().items()
        },
        "polars_cleaned_null_counts": {
            key: int(value)
            for key, value in df_pl_clean.null_count().to_dicts()[0].items()
        },
    }
)
comparison["same_cleaned_null_counts"] = (
    comparison["pandas_cleaned_null_counts"]
    == comparison["polars_cleaned_null_counts"]
)
comparison["pandas_cleaned_dtypes"] = {
    key: normalize_pandas_dtype(value) for key, value in df.dtypes.items()
}
comparison["polars_cleaned_dtypes"] = {
    key: normalize_polars_dtype(value) for key, value in df_pl_clean.schema.items()
}
comparison["same_cleaned_dtypes"] = (
    comparison["pandas_cleaned_dtypes"] == comparison["polars_cleaned_dtypes"]
)

comparison["cleaned_numeric_summary"] = {}
# 부동소수점 집계 순서 차이를 고려해 허용오차 내 평균·합계 일치를 확인한다.
for column in NUMERIC_COMPARE_COLS:
    pandas_summary = {
        "mean": float(df[column].mean()),
        "sum": float(df[column].sum()),
    }
    polars_summary = {
        "mean": float(df_pl_clean[column].mean()),
        "sum": float(df_pl_clean[column].sum()),
    }
    comparison["cleaned_numeric_summary"][column] = {
        "pandas": pandas_summary,
        "polars": polars_summary,
        "mean_close": math.isclose(
            pandas_summary["mean"], polars_summary["mean"], rel_tol=1e-6, abs_tol=1e-6
        ),
        "sum_close": math.isclose(
            pandas_summary["sum"], polars_summary["sum"], rel_tol=1e-6, abs_tol=1e-6
        ),
    }
comparison["same_cleaned_numeric_summary"] = all(
    item["mean_close"] and item["sum_close"]
    for item in comparison["cleaned_numeric_summary"].values()
)
comparison["all_cleaned_checks_passed"] = all(
    comparison[key]
    for key in (
        "same_cleaned_shape",
        "same_cleaned_columns",
        "same_cleaned_null_counts",
        "same_cleaned_dtypes",
        "same_cleaned_numeric_summary",
    )
)
COMPARISON_PATH.write_text(
    json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
)

# --- 5. 최종 산출물 저장 ---
# CSV는 Windows Excel 호환을 위해 UTF-8 BOM을 사용하고, Parquet은 분석 재사용용으로 저장한다.
df.to_csv(OUT_CSV_PATH, index=False, encoding="utf-8-sig")
df.to_parquet(OUT_PATH, index=False)
print(f"saved: {OUT_CSV_PATH} ({len(df):,} rows)")
print(f"saved: {OUT_PATH} ({len(df):,} rows)")
print(f"saved: {COMPARISON_PATH}")
print(df["analysis_group"].value_counts())
