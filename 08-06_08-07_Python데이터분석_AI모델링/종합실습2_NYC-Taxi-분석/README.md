# NYC Yellow Taxi End-to-End 데이터 분석 프로젝트

NYC Yellow Taxi 운행 데이터를 Pandas와 Polars로 정제하고, 시간대별 운행 특성을 통계적으로 분석한 뒤 sklearn Pipeline으로 총요금을 예측하는 End-to-End 프로젝트입니다.

분석 결과와 개선 과정은 Jinja2를 이용해 [최종 종합 보고서](report.md)로 자동 생성합니다.

## 1. 프로젝트 질문

초기에는 평일 출퇴근 시간과 비출퇴근 시간의 총요금 차이를 비교했습니다. 그러나 표본 수가 매우 커 작은 차이도 통계적으로 유의하게 나타났고, 출퇴근·비출퇴근 이분법이 서로 다른 시간대의 특성을 평균으로 상쇄한다는 한계가 확인되었습니다.

이에 분석을 다음과 같이 개선했습니다.

| 단계 | 분석 내용 | 핵심 개선 |
|---|---|---|
| 최초 분석 (v1) | 출퇴근 vs 비출퇴근 | 기본 그룹 비교와 Welch t-test |
| 1차 개선 (v2) | 속도·마일당 요금 분석 | Cohen's d를 추가해 실질적 효과 확인 |
| 2차 개선 (v3) | 5개 시간대 밴드 분석 | 낮(10~16시)과 심야(0~6시) 비교 |

각 단계의 상세 내용은 [최초 분석](report_v1.md), [1차 개선](report_v2.md), [2차 개선](report_v3.md)에서 확인할 수 있습니다.

## 2. 핵심 결과

- 원천 로딩 데이터: **18,999,282행, 선택 컬럼 6개**
- 최종 정제 데이터: **9,068,557행, 12열**
- Pandas·Polars 정제 결과 비교: **전체 Pass**
- 낮 평균 속도는 심야보다 약 **48.4% 낮음**
- 속도 차이의 Cohen's d는 **-1.53**으로 큰 효과
- 낮 평균 이동거리는 심야보다 약 **33.0% 짧음**
- 총요금 차이는 약 **2.7%**지만 효과크기는 **-0.04**로 실질적 차이가 미미함
- 회귀모델 성능: **RMSE 4.132, MAE 2.430, R² 0.9333**

## 3. 데이터

- 데이터셋: NYC TLC Yellow Taxi Trip Records
- 분석 기간: 2026년 1월~5월
- 출처: [NYC Taxi & Limousine Commission Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- 분석 대상: 평일, 기본 요금제(`RatecodeID == 1`) 운행

원천 데이터와 정제 데이터는 용량이 크기 때문에 Git 저장 대상에서 제외합니다. 파이프라인을 실행하면 원천 Parquet를 내려받고 다음 파일을 자동 생성합니다.

- `data/processed/trips_clean.csv`
- `data/processed/trips_clean.parquet`

현재 생성 파일의 대략적인 크기는 CSV 875MB, Parquet 136MB입니다.

## 4. 실행 환경

- 테스트 Python: 3.10
- 주요 라이브러리: Pandas, Polars, SciPy, Seaborn, Plotly, scikit-learn, Jinja2

### 설치

```bash
python -m pip install -r requirements.txt
```

macOS 또는 Linux에서 `python` 명령이 Python 3을 가리키지 않으면 `python3`를 사용합니다.

### 전체 파이프라인 실행

```bash
python main.py
```

실행 순서는 데이터 다운로드 → 전처리 → EDA·통계 분석 → 모델 학습 → 시각화 → Jinja2 보고서 생성입니다. 원천 파일이 이미 있으면 다운로드 단계는 건너뜁니다.

데이터가 이미 내려받아진 환경에서 전체 실행에는 약 2~3분이 걸릴 수 있으며, 최초 실행 시간은 네트워크와 시스템 성능에 따라 달라집니다.

## 5. 프로젝트 구조

```text
day2-e2e-data-analysis/
├── main.py                         # 전체 파이프라인 실행
├── requirements.txt               # 프로젝트 의존성
├── README.md                       # 실행 및 평가 안내
├── report.md                       # Jinja2 최종 종합 보고서
├── report_v1.md                    # 최초 분석
├── report_v2.md                    # 1차 개선
├── report_v3.md                    # 2차 개선
├── templates/
│   └── report.md.j2                # 최종 보고서 Jinja2 템플릿
├── scripts/
│   ├── 01_download_data.py         # 데이터 다운로드
│   ├── 02_preprocess.py            # Pandas·Polars 정제 및 비교
│   ├── 03_analysis.py              # 기술통계·상관분석·최초 t-test
│   ├── 04_model.py                 # sklearn Pipeline 학습 및 저장
│   ├── 05_report.py                # v1 보고서 생성
│   ├── 06_analysis_v2.py           # 지표 분해·효과크기 분석
│   ├── 07_report_v2.py             # v2 보고서 생성
│   ├── 08_analysis_v3.py           # 시간대 밴드 분석
│   ├── 09_report_v3.py             # v3 보고서 생성
│   ├── 10_plotly_chart.py          # 인터랙티브 차트 생성
│   └── 11_report_jinja.py          # 최종 종합 보고서 자동 생성
├── outputs/
│   ├── figures/                    # PNG 및 Plotly HTML
│   └── tables/                     # 통계·평가·비교 결과
├── models/
│   └── total_amount_regression_pipeline.joblib
└── data/
    ├── raw/                        # 다운로드 원천 데이터
    └── processed/                  # 정제 CSV·Parquet
```

## 6. 평가 기준별 확인 위치

| PDF 평가 항목 | 구현 코드 | 주요 산출물 |
|---|---|---|
| Pandas·Polars 사용 및 비교 | `scripts/02_preprocess.py` | `outputs/tables/pandas_polars_comparison.json` |
| 결측치·중복 처리 및 EDA | `scripts/02_preprocess.py` | 정제 CSV·Parquet, 비교 JSON |
| Seaborn 정적 시각화 | `scripts/03_analysis.py`, `06_analysis_v2.py`, `08_analysis_v3.py` | `outputs/figures/*.png` |
| Plotly 인터랙티브 시각화 | `scripts/10_plotly_chart.py` | `hourly_profile_interactive.html` |
| 기술통계·상관계수 | `scripts/03_analysis.py` | `descriptive_overall.csv`, `correlation_matrix.csv` |
| Welch t-test·효과크기 | `scripts/03_analysis.py`, `06_analysis_v2.py`, `08_analysis_v3.py` | `ttest_results*.csv` |
| sklearn Pipeline·평가 | `scripts/04_model.py` | `regression_metrics.csv` |
| joblib 모델 저장 | `scripts/04_model.py` | `models/total_amount_regression_pipeline.joblib` |
| report.md 자동 생성 | `scripts/11_report_jinja.py` | `templates/report.md.j2`, `report.md` |

## 7. Pandas·Polars 교차 검증

두 라이브러리에 동일한 필터링, 결측치 처리, 파생 컬럼 생성, 중복 제거 로직을 적용하고 다음 항목을 비교합니다.

- 원천 및 정제 후 shape
- 컬럼명
- 결측치 수
- 논리 자료형
- 주요 수치 컬럼의 평균과 합계

최신 실행 결과는 `outputs/tables/pandas_polars_comparison.json`에 저장되며, `all_cleaned_checks_passed` 값은 `true`입니다.

## 8. 머신러닝 Pipeline

- 입력 변수: `trip_distance`, `trip_duration_minutes`, `pickup_hour`, `is_rush_hour`
- 예측 대상: `total_amount`
- Pipeline: `StandardScaler` + `LinearRegression`
- 데이터 분할: 학습 80% / 평가 20%, `random_state=42`
- 저장 모델: `models/total_amount_regression_pipeline.joblib`

이 모델은 시간대 효과의 인과관계를 추정하기 위한 모델이 아니라 전체 전처리와 예측 단계를 하나로 묶은 재현 가능한 회귀 baseline입니다.

## 9. 해석 시 주의점

- v3의 낮·심야 비교는 시간대별 EDA 이후 수행한 탐색적 후속 분석입니다.
- 표본이 매우 크므로 p-value와 함께 Cohen's d를 해석합니다.
- `fare_per_mile`은 기본요금, 팁, 통행료, 할증 및 짧은 운행의 영향을 함께 받습니다.
- 관찰 데이터이므로 시간대와 요금·속도의 인과관계를 직접 확정할 수 없습니다.

최종 결과와 자세한 해석은 [report.md](report.md)를 확인해 주세요.
