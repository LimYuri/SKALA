"""API 주소·요청 파라미터, 산출물 저장 경로를 한 곳에서 관리한다.

설정값을 코드 곳곳에 흩어두지 않고 이 파일로 모아야 나중에 좌표나
조회 IP를 바꿀 때 여기 한 곳만 고치면 된다.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# 1) 실습에서 지정한 API 3종 (임의 변경 금지: 과제 명세 그대로 사용)
# --------------------------------------------------------------------------
# ① Open-Meteo : 서울 3일치 시간대별 기온 / 강수확률
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_PARAMS = {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "hourly": "temperature_2m,precipitation_probability",
    "forecast_days": 3,
    "timezone": "Asia/Seoul",  # UTC 대신 한국 시간으로 받으려고 지정
}

# ② Countries.dev : 대한민국(KOR) 국가 정보
COUNTRIES_DEV_URL = "https://countries.dev/alpha/KOR"

# ③ ip-api : IP(8.8.8.8, 구글 공개 DNS) 기반 지역 정보
IP_API_URL = "http://ip-api.com/json/8.8.8.8"

# --------------------------------------------------------------------------
# 2) 산출물 경로
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # app/의 한 단계 위 = 프로젝트 루트
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

CSV_OUTPUT = OUTPUT_DIR / "seoul_weather_report.csv"
PARQUET_OUTPUT = OUTPUT_DIR / "seoul_weather_report.parquet"
PERFORMANCE_OUTPUT = OUTPUT_DIR / "performance_result.json"
VALIDATION_ERROR_OUTPUT = OUTPUT_DIR / "validation_errors.json"
RAW_SNAPSHOT_OUTPUT = OUTPUT_DIR / "raw_api_snapshot.json"  # 원본 응답도 재현용으로 남겨둠
