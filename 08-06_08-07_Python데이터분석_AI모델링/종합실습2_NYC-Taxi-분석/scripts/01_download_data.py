"""[01] NYC Yellow Taxi 원천 데이터를 월별 Parquet 파일로 내려받는다.

입력: NYC TLC 공식 CloudFront의 2026년 1~5월 Yellow Taxi 데이터
출력: data/raw/yellow_tripdata_YYYY-MM.parquet

이미 내려받은 파일은 건너뛰므로 파이프라인을 반복 실행해도 불필요하게
대용량 파일을 다시 다운로드하지 않는다.
"""
import urllib.request
from pathlib import Path

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{}.parquet"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# 깨끗한 저장소에서 처음 실행해도 다운로드 폴더가 자동으로 준비되도록 한다.
RAW_DIR.mkdir(parents=True, exist_ok=True)

# 월별 파일을 독립적으로 처리해 일부 파일만 존재하는 경우에도 이어받을 수 있다.
for month in MONTHS:
    dest = RAW_DIR / f"yellow_tripdata_{month}.parquet"
    # 기존 파일을 덮어쓰지 않아 재실행 시간과 네트워크 사용량을 줄인다.
    if dest.exists():
        print(f"skip (exists): {dest.name}")
        continue
    url = BASE_URL.format(month)
    print(f"downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)
    print(f"  done: {dest.stat().st_size / 1e6:.1f} MB")
