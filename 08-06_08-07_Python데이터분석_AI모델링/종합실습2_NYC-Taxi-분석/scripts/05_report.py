"""[05] 최초 분석(v1)의 표·차트·모델 결과를 Markdown 보고서로 묶는다.

입력: 정제 Parquet와 03·04 단계에서 생성한 CSV 산출물
출력: report_v1.md

이 보고서는 최초 가설 검증 결과를 보존하며, v2·v3 개선이 필요한 이유를
비교할 수 있는 분석 기준선 역할을 한다.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"

# 최초 분석의 그룹 통계와 앞 단계에서 저장한 결과 파일을 다시 불러온다.
df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")
group_summary = df.groupby("analysis_group")[
    ["trip_distance", "total_amount", "trip_duration_minutes"]
].agg(["mean", "std"]).round(3)
group_summary.columns = [f"{col}_{stat}" for col, stat in group_summary.columns]

corr = pd.read_csv(TABLES / "correlation_matrix.csv", index_col=0).round(3)
ttest = pd.read_csv(TABLES / "ttest_results.csv").round(4)
coef = pd.read_csv(TABLES / "regression_coefficients.csv").round(4)
metrics = pd.read_csv(TABLES / "regression_metrics.csv").round(4).iloc[0]

# Markdown 문서 구조를 순서대로 구성해 실행 결과를 사람이 바로 읽을 수 있게 한다.
lines = [
    "# NYC 옐로우 택시 분석 — 최초 분석: 출퇴근 vs 비출퇴근 (v1)",
    "",
    f"- 대상 기간: 2026-01 ~ 2026-05 (평일, RatecodeID==1, 이상치 제거 후)",
    f"- 총 trip 수: {len(df):,} (출퇴근 {int((df['is_rush_hour']).sum()):,} / 비출퇴근 {int((~df['is_rush_hour']).sum()):,})",
    "",
    "## 1. 그룹별 기술통계 (평균 ± 표준편차)",
    "",
    group_summary.to_markdown(),
    "",
    "## 2. 상관행렬",
    "",
    corr.to_markdown(),
    "",
    "![correlation heatmap](outputs/figures/correlation_heatmap.png)",
    "",
    "## 3. t-test (출퇴근 vs 비출퇴근, Welch)",
    "",
    ttest.to_markdown(index=False),
    "",
    "![rush vs non-rush boxplot](outputs/figures/rush_vs_nonrush_boxplot.png)",
    "",
    "## 4. 선형회귀 (total_amount 예측)",
    "",
    coef.to_markdown(index=False),
    "",
    f"- RMSE: {metrics['rmse']}",
    f"- MAE: {metrics['mae']}",
    f"- R^2: {metrics['r2']}",
    f"- test set 크기: {int(metrics['n_test']):,}",
    "",
]

# UTF-8로 저장해 Windows·macOS에서 한글이 동일하게 보이도록 한다.
out_path = ROOT / "report_v1.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"saved: {out_path}")
