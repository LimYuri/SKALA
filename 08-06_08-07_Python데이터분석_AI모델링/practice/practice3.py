"""
================================================================================
프로그램명   : [실습 3] Pandas EDA · Polars Lazy · DuckDB SQL 비교
작성자       : 판교 7반 임유리
작성일       : 2026-08-07
설명         : sales_100k.csv(1,000,000행)를 region, category, amount 세 컬럼 중심으로 정제한 뒤 IQR 이상치를 제거하고,
               Pandas named aggregation · Polars Lazy API · DuckDB SQL 세 가지 방식으로 동일한 집계(지역·카테고리별 총매출/평균/건수)를 수행해 결과 일치 여부와 실행 시간을 비교한다.
               * resolve_data_file()이 실행 파일과 같은 폴더 또는 data/ 폴더의 sales_100k.csv를 모두 지원한다.
               * clean_pandas_data()에서 region/category 공백 제거 및 빈 문자열→NA 치환, amount 숫자 변환 실패→NA 처리를 먼저 수행한 뒤 결측 행을 제거한다(필수값 누락 또는 변환 실패 22,860건).
               * 이후 정제된 데이터의 amount로 Q1/Q3/IQR을 계산해 이상치를 제거한다(956,363행 유지, 20,777건 제거).
               * Polars는 scan_csv → strip/cast → filter → group_by → agg → sort → collect 체인으로, DuckDB는 all_varchar=true로 읽은 뒤 TRY_CAST로 숫자 변환하는 SQL로 동일 집계를 구현한다.
               * results_are_equal()로 세 결과를 pd.testing.assert_frame_equal (rtol=1e-9, atol=1e-6)로 비교하고, timeit(number=3)으로 세 도구의 실행 시간을 동일 조건에서 측정한다.
               * resolve_data_file/run_pandas_eda/calculate_iqr_bounds/pandas_aggregation/polars_aggregation/ duckdb_aggregation/results_are_equal/benchmark 등의 함수명을 사용했다.
================================================================================
"""


from __future__ import annotations # 최신 타입 힌트 문법 사용 지원

import sys # 시스템 제어 및 에러 종료 처리
import timeit # 코드 실행 속도 측정
from pathlib import Path # 파일 및 폴더 경로 조작
from typing import Callable # 함수 타입을 명시할 때 사용

try:
    import duckdb  # DuckDB SQL 인터페이스(SQL 기반 초고속 데이터 분석/엔진)
    import pandas as pd # 데이터 분석 표준 라이브러리
    import polars as pl # Polars 데이터프레임 라이브러리(RUST 기반 초고속 데이터 프레임)
except ModuleNotFoundError as error:
    print(f"[패키지 오류] {error}", file=sys.stderr)
    print("python -m pip install -r requirements.txt 명령을 실행하세요.", file=sys.stderr)
    raise SystemExit(1) from error # 에러 메시지 띄우고 강제 종료


BASE_DIR = Path(__file__).resolve().parent
REQUIRED_COLUMNS = {"region", "category", "amount"}
RESULT_COLUMNS = ["region", "category", "total", "mean", "count"]
BENCHMARK_NUMBER = 3 # 정확한 평균 시간 측정을 위한 timeit 함수 반복 실행 횟수


def resolve_data_file() -> Path:
    """실행 파일과 같은 폴더 또는 data 폴더에서 CSV를 찾습니다."""
    candidates = [ # 파일이 존재할 수 있는 예상 경로의 리스트 정의
        BASE_DIR / "sales_100k.csv",
        BASE_DIR / "data" / "sales_100k.csv",
    ]
    for candidate in candidates: # 경로를 하나씩 확인하며 실제 존재하는 파일을 발견하면 즉시 반환
        if candidate.exists():
            return candidate
    searched = "\n- ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"sales_100k.csv를 찾을 수 없습니다.\n- {searched}") # 모든 경로에 파일이 없으면 탐색했던 목록을 합쳐 에러 발생


def print_title(title: str) -> None: 
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def clean_pandas_data(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """필수 컬럼을 정리하고 결측 행을 제거합니다."""
    missing = sorted(REQUIRED_COLUMNS - set(dataframe.columns)) # 필수 컬럼 중 누락된 열이 있는지 확인
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {', '.join(missing)}")

    cleaned = dataframe[["region", "category", "amount"]].copy() # 필요한 3가지 열만 선택해 복사본 생성
    for column in ["region", "category"]: # 문자열 열 데이터 타입 변환 및 앞뒤 공백 제거(빈 문자열은 결측치 처리)
        cleaned[column] = cleaned[column].astype("string").str.strip()
        cleaned.loc[cleaned[column] == "", column] = pd.NA

    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce") # 금액 열을 숫자 타입으로 변환(변환 실패 시 결측치 처리)
    before_drop = len(cleaned) # 삭제 전체 데이터 개수 기록
    cleaned = cleaned.dropna(subset=["region", "category", "amount"]).copy() # 세 열 중 하나라도 결측치가 있는 행을 모두 제거

    if cleaned.empty: # 데이터가 전부 지워져서 비어있다면 에러 발생
        raise ValueError("정제 후 분석할 데이터가 없습니다.")
    return cleaned, before_drop - len(cleaned) # 정제된 데이터프레임과 삭제된 행의 총 개수를 반환


def calculate_iqr_bounds(amount: pd.Series) -> tuple[float, float, float, float, float]: # IQR bounds 계산 함수
    """Q1, Q3, IQR, 하한값, 상한값을 계산합니다."""
    q1 = float(amount.quantile(0.25))
    q3 = float(amount.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0: # 모든 데이터가 동일해 IQR이 0이 되면 에러 처리
        raise ValueError("IQR이 0이므로 amount 분포를 확인하세요.")
    lower = q1 - 1.5 * iqr # 하한값
    upper = q3 + 1.5 * iqr # 상한값
    return q1, q3, iqr, lower, upper


def run_pandas_eda(file_path: Path) -> tuple[float, float]:
    """Pandas 기본 EDA와 IQR 이상치 처리를 수행합니다."""
    raw = pd.read_csv(file_path)

    print_title("0. 실행 환경")
    print(f"pandas: {pd.__version__}")
    print(f"polars: {pl.__version__}")
    print(f"duckdb: {duckdb.__version__}")

    print_title("1. Pandas 기본 EDA")
    print(f"파일 경로: {file_path}")
    print(f"원본 행 수: {len(raw):,}")
    print(f"원본 열 수: {len(raw.columns):,}")
    print("\n[상위 5행]")
    print(raw.head().to_string(index=False))
    print("\n[df.info()]")
    raw.info()
    print("\n[컬럼별 결측치 수]")
    print(raw.isnull().sum().to_string())

    cleaned, invalid_rows = clean_pandas_data(raw) # 이전 단계에서 정의한 함수를 호출해 데이터 정제(결측치 등 제거)
    q1, q3, iqr, lower, upper = calculate_iqr_bounds(cleaned["amount"]) # 금액 열을 기준으로 IQR 통계치 및 상/하한선 계산
    normal = cleaned[cleaned["amount"].between(lower, upper, inclusive="both")] # 상한선과 하한선 사이에 있는 정상 범위 데이터만 필터링

    print_title("2. IQR 이상치 처리")
    print(f"필수값 누락 또는 변환 실패 행 수: {invalid_rows:,}")
    print(f"정제 후 행 수: {len(cleaned):,}")
    print(f"Q1: {q1:,.2f}")
    print(f"Q3: {q3:,.2f}")
    print(f"IQR: {iqr:,.2f}")
    print(f"하한값: {lower:,.2f}")
    print(f"상한값: {upper:,.2f}")
    print(f"이상치 제거 전 행 수: {len(cleaned):,}")
    print(f"이상치 제거 후 행 수: {len(normal):,}")
    print(f"제거된 이상치 행 수: {len(cleaned) - len(normal):,}")

    if normal.empty: # 이상치 처리 후 남은 데이터가 없다면 예외를 발생시키고 정상범위(하한, 상한) 반환
        raise ValueError("IQR 이상치 처리 후 분석할 데이터가 없습니다.")
    return lower, upper


def pandas_aggregation(file_path: Path, lower: float, upper: float) -> pd.DataFrame:
    """Pandas named aggregation으로 집계합니다."""
    cleaned, _ = clean_pandas_data(pd.read_csv(file_path)) 
    normal = cleaned[cleaned["amount"].between(lower, upper, inclusive="both")] # 미리 계산된 하한값과 상한값 사이의 정상 범위 데이터만 필터링
    return ( # 그룹화 및 Named Aggregation 수행 후 정렬하여 반환
        normal.groupby(["region", "category"], as_index=False) # 지역과 카테고리별로 그룹화
        .agg(
            total=("amount", "sum"),
            mean=("amount", "mean"),
            count=("amount", "count"),
        )
        .sort_values(["total", "region", "category"], ascending=[False, True, True])
        .reset_index(drop=True) # 정렬 후 뒤섞인 데이터프레임의 인덱스를 0부터 다시 재정렬
    )


def polars_aggregation(file_path: Path, lower: float, upper: float) -> pd.DataFrame:
    """scan_csv에서 collect까지 Polars Lazy 체인으로 집계합니다."""
    result = (
        pl.scan_csv( # 데이터를 즉시 읽지 않고 쿼리 계획만 세우는 lazy 모드로 csv 탐색
            str(file_path),
            schema_overrides={
                "region": pl.String,
                "category": pl.String,
                "amount": pl.String,
            },
        )
        .with_columns( 
            pl.col("region").str.strip_chars(),
            pl.col("category").str.strip_chars(),
            pl.col("amount").cast(pl.Float64, strict=False),
        )
        .filter( # 결측치 제거 및 이상치 필터링
            pl.col("region").is_not_null()
            & pl.col("category").is_not_null()
            & (pl.col("region") != "")
            & (pl.col("category") != "")
            & pl.col("amount").is_not_null()
            & (pl.col("amount") >= lower)
            & (pl.col("amount") <= upper)
        )
        .group_by(["region", "category"]) 
        .agg(
            pl.col("amount").sum().alias("total"),
            pl.col("amount").mean().alias("mean"),
            pl.len().alias("count"),
        )
        .sort(["total", "region", "category"], descending=[True, False, False])
        .collect() # 지금까지 쌓인 연산 계획(lazy)을 멀티스레드로 실제 실행해 결과를 메모리에 로드
    )
    return pd.DataFrame(result.to_dicts(), columns=RESULT_COLUMNS) # 타 라이브러리와 결과 비교를 위해 Polars 결과를 Pandas 데이터프레임으로 변환하여 반환


def duckdb_aggregation(file_path: Path, lower: float, upper: float) -> pd.DataFrame:
    """DuckDB에서 CSV 파일을 직접 읽어 SQL로 집계합니다."""
    sql_path = str(file_path).replace("\\", "/").replace("'", "''")
    #데이터 정제, 집계, 정렬을 수행하는 전체 SQL 쿼리문 정의
    query = f""" 
        WITH cleaned AS (
            SELECT
                TRIM(region) AS region,
                TRIM(category) AS category,
                TRY_CAST(amount AS DOUBLE) AS amount
            FROM read_csv('{sql_path}', header = true, all_varchar = true)
        )
        SELECT
            region,
            category,
            SUM(amount) AS total,
            AVG(amount) AS mean,
            COUNT(amount) AS count
        FROM cleaned
        WHERE region IS NOT NULL
          AND category IS NOT NULL
          AND region <> ''
          AND category <> ''
          AND amount IS NOT NULL
          AND amount BETWEEN ? AND ?
        GROUP BY region, category
        ORDER BY total DESC, region ASC, category ASC
    """
    with duckdb.connect(database=":memory:") as connection: # 파일 저장 없이 고속 처리가 가능한 가상의 인메모리 데이터베이스에 연결
        return connection.execute(query, [lower, upper]).df() # SQL 쿼리에 하한값/상한값을 넘겨 실행한 후, 최종 결과물을 Pandas 데이터프레임으로 변환


def normalize_result(dataframe: pd.DataFrame) -> pd.DataFrame:
    """세 결과의 컬럼, 자료형, 정렬을 비교 가능한 형태로 맞춥니다."""
    normalized = dataframe[RESULT_COLUMNS].copy()
    normalized["region"] = normalized["region"].astype("string")
    normalized["category"] = normalized["category"].astype("string")
    normalized["total"] = pd.to_numeric(normalized["total"])
    normalized["mean"] = pd.to_numeric(normalized["mean"])
    normalized["count"] = pd.to_numeric(normalized["count"]).astype("int64") # 개수는 64비트 정수형 지정
    return normalized.sort_values(["region", "category"]).reset_index(drop=True)


def results_are_equal(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    """평균값의 미세한 부동소수점 차이를 허용하여 비교합니다."""
    try:
        pd.testing.assert_frame_equal( # Pandas 검증 툴을 사용해 두 데이터프레임의 내용이 같은지 비교
            normalize_result(left), # 왼쪽 데이터프레임 규격화
            normalize_result(right), # 오른쪽 데이터프레임 규격화
            check_dtype=False, # 세부 데이터 타입 불일치는 무시
            check_exact=False, # 소수점 아래 자리가 완벽히 일치하지 않아도 허용
            rtol=1e-9, # 허용 가능한 상대 오차 범위 설정(10억분의 1)
            atol=1e-6, # 허용 가능한 절대 오차 범위 설정(100만분의 1)
        )
        return True # 오차 범위 내에서 내용이 완전히 일치하면 True 반환
    except AssertionError:
        return False # 데이터 내용이 다르거나 오차 범위를 벗어나면 False 반환


def print_result(title: str, dataframe: pd.DataFrame) -> None: # 결과 출력
    print_title(title)
    print(f"전체 그룹 수: {len(dataframe):,}")
    with pd.option_context("display.float_format", lambda value: f"{value:,.2f}"):
        print(dataframe.to_string(index=False))


def benchmark(name: str, function: Callable[[], pd.DataFrame]) -> dict[str, float | str]:
    """동일한 number 값으로 한 번 실행할 때의 평균 시간을 계산합니다."""
    seconds = timeit.timeit(function, number=BENCHMARK_NUMBER) # 설정된 반복 횟수만큼 함수를 실행해 총 걸린 시간
    return {"tool": name, "seconds": seconds / BENCHMARK_NUMBER} # 도구 이름과 전체 걸린 시간을 실행 횟수로 나눈 1회 평균 시간을 딕셔너리로 반환


def main() -> None: #
    data_file = resolve_data_file()
    lower, upper = run_pandas_eda(data_file) # Pandas로 기본 탐색을 수행하고 IQR 기반 이상치 필터링용 상/하한선 얻음

    # 세 라이브러리로 각각 데이터 집계 연산 실행
    pandas_result = pandas_aggregation(data_file, lower, upper)
    polars_result = polars_aggregation(data_file, lower, upper)
    duckdb_result = duckdb_aggregation(data_file, lower, upper)

    print_result("3. Pandas named aggregation 결과", pandas_result)
    print_result("4. Polars Lazy API 결과", polars_result)
    print_result("5. DuckDB SQL 결과", duckdb_result)

    # 부동 소수점 오차를 감안해 세 라이브러리 연산 결과 내용이 똑같은지 교차 검증   
    pandas_polars_match = results_are_equal(pandas_result, polars_result)
    pandas_duckdb_match = results_are_equal(pandas_result, duckdb_result)
    print_title("6. 세 도구 집계 결과 비교")
    print(f"Pandas와 Polars 결과 일치: {pandas_polars_match}")
    print(f"Pandas와 DuckDB 결과 일치: {pandas_duckdb_match}")
    if not pandas_polars_match or not pandas_duckdb_match: # 하나라도 결과가 다르면 연산 로직에 문제가 있는 것이므로 예외 발생
        raise ValueError("세 도구의 집계 결과가 일치하지 않습니다.")

    # 정합성 검증 통과시, timeit 이용해 본격적인 속도 측정
    print_title("7. timeit 실행 시간 비교")
    print(f"공통 측정 조건: number={BENCHMARK_NUMBER}")
    times = [
        benchmark("Pandas", lambda: pandas_aggregation(data_file, lower, upper)),
        benchmark("Polars Lazy", lambda: polars_aggregation(data_file, lower, upper)),
        benchmark("DuckDB SQL", lambda: duckdb_aggregation(data_file, lower, upper)),
    ]
    result = pd.DataFrame(times).sort_values("seconds") # 시간이 빠른 순서대로 정렬
    print(result.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\n실습이 정상적으로 완료되었습니다.")


if __name__ == "__main__": # 예외처리
    try:
        main()
    except FileNotFoundError as error:
        print(f"[파일 오류] {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        print(f"[CSV 읽기 오류] {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except ValueError as error:
        print(f"[데이터 오류] {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except Exception as error:
        print(f"[실행 오류] {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1) from error



#이번 실습에서 가장 어려웠던 부분은 IQR 계산 순서였다. 
#처음에는 결측치를 그냥 두고 IQR부터 계산했지만, 계산하는 과정에서 region/category/amount 결측·변환실패 행을 먼저 제거한 뒤 IQR을 계산해야 한다는 걸 알게 되었다.
#원본 1,000,000행 → 정제 977,140행 → 이상치 제거 956,363행까지 기대값과 정확히 맞아떨어졌다. 이를 통해 순서 하나 차이가 최종 집계값 전체를 흔든다는 걸 체감했다.
#Polars는 scan_csv로 시작해서 마지막에 collect()를 호출하는 Lazy 체인을 쓰니 100만 행을 다 메모리에 올리지 않고도 필터·집계 계획을 먼저 세운 뒤 한 번에 실행하기 때문에
#timeit 결과에서 Pandas보다 훨씬 빨랐다(Pandas 1.5초대 vs Polars 0.1초대). 
# DuckDB는 SQL의 TRY_CAST와 all_varchar=true 조합으로 타입 변환 실패까지 안전하게 처리하는 방식이 인상적이었다.
# 세 도구 결과를 pd.testing.assert_frame_equal로 오차 허용 비교(results_are_equal)한 것도 좋았다. 
# 단순히 "눈으로 보기에 비슷하다"가 아니라 자동으로 True/False를 확인할 수 있어서 좋았다.