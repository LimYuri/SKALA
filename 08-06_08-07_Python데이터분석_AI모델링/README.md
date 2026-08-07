# [Day 1] 종합 실습 - 실무형 수집·검증·품질 파이프라인

판교 7반 임유리

## 개요

Open-Meteo(서울 3일 시간대별 기온·강수확률), Countries.dev(대한민국 국가 정보),
ip-api(8.8.8.8 IP 위치 정보) 3개 API를 `httpx` + `asyncio.gather()`로 동시에
수집하고, Pydantic v2로 타입·범위를 검증한 뒤 CSV/Parquet로 저장하고 성능을
비교하는 파이프라인입니다.

## 실행 방법

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m app.main                # 파이프라인 실행
pytest -v                         # 테스트
ruff check .                      # 코드 스타일 검사
```

## 폴더 구조

```
app/            파이프라인 소스 코드 (config/models/api_client/pipeline/storage/main)
tests/          pytest 테스트
data/output/    실행 결과(CSV/Parquet/성능 JSON 등) 저장 위치
reports/        실행결과 보고서 PDF
```

## 산출물

- `data/output/seoul_weather_report.csv`, `.parquet` : 검증 통과 데이터
- `data/output/performance_result.json` : CSV/Parquet 쓰기·읽기 시간, 파일 크기
- `data/output/raw_api_snapshot.json` : 3개 API 원본 응답 스냅샷
