"""[07] 지표 분해와 효과크기를 추가한 1차 개선(v2) 보고서를 생성한다.

입력: 06 단계의 v2 통계 결과와 04 단계의 회귀 결과
출력: report_v2.md

v1의 '통계적으로 유의함'을 그대로 강조하지 않고 변화율과 Cohen's d를
함께 제시해 실질적으로 작은 차이라는 점을 명확히 설명한다.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"

# 분석과 모델 산출물을 읽어 보고서에서 재계산 없이 그대로 재사용한다.
ttest_v2 = pd.read_csv(TABLES / "ttest_results_v2.csv").round(4)
desc_v2 = pd.read_csv(TABLES / "descriptive_by_group_v2.csv", index_col=0).round(3)
reg_coef = pd.read_csv(TABLES / "regression_coefficients.csv").round(4)
reg_metrics = pd.read_csv(TABLES / "regression_metrics.csv").round(4).iloc[0]

# v1의 한계 → v2 개선 → 결과 해석 순서로 Markdown 문서를 구성한다.
lines = [
    "# NYC 옐로우 택시 분석 — 1차 개선: 지표 분해와 효과크기 (v2)",
    "",
    "v1에서는 `total_amount`만 비교했는데, 출퇴근 시간대는 이동거리는 짧아 거리 요금이 줄고 "
    "정체로 속도는 느려 시간 요금이 느는 두 효과가 서로 상쇄되어 총 요금 차이가 실질적으로 거의 없어 보였다. "
    "v2에서는 `speed_mph`(평균 속도), `fare_per_mile`(마일당 요금)을 추가로 분해하고, "
    "표본이 9백만 건이라 p-value가 항상 0에 가깝게 나오는 문제를 보완하기 위해 Cohen's d(효과크기)를 함께 본다.",
    "",
    "## 1. 그룹별 기술통계",
    "",
    desc_v2.to_markdown(),
    "",
    "## 2. t-test + 효과크기 (Cohen's d)",
    "",
    ttest_v2.to_markdown(index=False),
    "",
    "![speed & fare per mile boxplot](outputs/figures/speed_fare_boxplot_v2.png)",
    "",
    "## 3. 해석",
    "",
    "- `total_amount`: 출퇴근이 약 2.3% 낮음. p<0.001로 통계적으로 유의하지만 Cohen's d=-0.04로 "
    "무시할 수준 — v1에서 \"차이가 없어 보인다\"고 느낀 게 데이터상으로도 맞았다.",
    "- `trip_distance`: 출퇴근이 약 11.9% 짧음 (통근형 단거리 이동).",
    "- `speed_mph`: 출퇴근이 약 6.2% 느림 (정체 반영).",
    "- `fare_per_mile`: 출퇴근이 약 7.3% 비쌈 (같은 거리라도 시간 요금 때문에 단가가 오름).",
    "- 4개 지표 모두 Cohen's d 기준으로는 '무시가능'~'작음' 수준이라, trip 단위로 보면 그룹 내 "
    "편차가 그룹 간 평균 차이보다 훨씬 크다. 다만 %차이 자체는 방향이 뚜렷하고 (짧고, 느리고, "
    "마일당 비싸고) 정체·통근 패턴과 일치해 **총 요금보다 거리/속도/단가 지표가 훨씬 해석 가능한 스토리**를 준다.",
    "",
    "## 4. 회귀모델 (v1과 동일, 재사용)",
    "",
    reg_coef.to_markdown(index=False),
    "",
    f"- RMSE: {reg_metrics['rmse']}",
    f"- MAE: {reg_metrics['mae']}",
    f"- R^2: {reg_metrics['r2']}",
    "",
]

# 버전별 분석 이력을 보존하기 위해 최종 report.md와 별도 파일로 저장한다.
out_path = ROOT / "report_v2.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"saved: {out_path}")
