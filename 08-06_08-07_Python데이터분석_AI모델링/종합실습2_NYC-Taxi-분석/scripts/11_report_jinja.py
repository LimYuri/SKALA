"""[11] 누적된 분석 산출물을 Jinja2 템플릿으로 최종 보고서에 통합한다.

입력:
- data/processed/trips_clean.parquet
- outputs/tables 아래의 전처리·분석·모델 결과 파일
- templates/report.md.j2

출력:
- 프로젝트 루트의 report.md

보고서 본문과 표현 형식은 템플릿에 두고, 이 스크립트는 수치 가공과
템플릿에 전달할 컨텍스트 구성을 담당한다.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"
TEMPLATES = ROOT / "templates"


def comma(value):
    """정수형 수치를 보고서용 천 단위 구분 문자열로 변환한다."""
    return f"{int(value):,}"


def format_p_value(value):
    """매우 작은 p-value가 0.0000으로 오해되지 않도록 표시한다."""
    return "< 0.001" if float(value) < 0.001 else f"{float(value):.4f}"


def metric_row(frame, metric):
    """t-test 결과표에서 지정한 지표의 한 행을 꺼낸다."""
    return frame.loc[frame["metric"] == metric].iloc[0]


# 1. 최종 보고서에 사용할 전처리·분석 산출물을 불러온다.
df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")
# Parquet 로딩 환경에 따라 달라질 수 있는 불리언 표현을 명시적으로 통일한다.
df["is_rush_hour"] = df["is_rush_hour"].astype(bool)

comparison = json.loads(
    (TABLES / "pandas_polars_comparison.json").read_text(encoding="utf-8")
)
descriptive = pd.read_csv(TABLES / "descriptive_overall.csv", index_col=0).round(3)
descriptive["count"] = descriptive["count"].astype(int).map("{:,}".format)
correlation = pd.read_csv(TABLES / "correlation_matrix.csv", index_col=0).round(3)

ttest_v1 = pd.read_csv(TABLES / "ttest_results.csv")
ttest_v2 = pd.read_csv(TABLES / "ttest_results_v2.csv")
ttest_v3 = pd.read_csv(TABLES / "ttest_results_v3.csv")

# 각 분석 버전에서 보고서에 강조할 대표 지표만 추출한다.
v1_total = metric_row(ttest_v1, "total_amount")
v2_speed = metric_row(ttest_v2, "speed_mph")
v2_fare = metric_row(ttest_v2, "fare_per_mile")
v3_speed = metric_row(ttest_v3, "speed_mph")
v3_distance = metric_row(ttest_v3, "trip_distance")
v3_total = metric_row(ttest_v3, "total_amount")

# 2. v1→v2→v3로 질문과 분석 방법이 개선된 과정을 하나의 표로 구성한다.
analysis_stages = [
    {
        "stage": "최초 분석 (v1)",
        "question": "출퇴근과 비출퇴근의 총요금·이동거리는 다른가?",
        "improvement": "기본 그룹 비교와 Welch t-test를 수행",
        "key_result": (
            f"총요금 평균 차이는 ${abs(v1_total['diff']):.2f}. "
            "통계적으로 유의했지만 실질적 크기는 아직 평가하지 못함"
        ),
        "report_path": "report_v1.md",
    },
    {
        "stage": "1차 개선 (v2)",
        "question": "총요금이 비슷하게 보이는 이유를 속도와 단가로 분해할 수 있는가?",
        "improvement": "speed_mph·fare_per_mile과 Cohen's d를 추가",
        "key_result": (
            f"출퇴근 속도 {abs(v2_speed['diff_pct']):.1f}% 감소, "
            f"마일당 요금 {v2_fare['diff_pct']:.1f}% 증가. "
            "다만 모든 효과크기는 매우 작음"
        ),
        "report_path": "report_v2.md",
    },
    {
        "stage": "2차 개선 (v3)",
        "question": "출퇴근·비출퇴근 이분법이 시간대별 차이를 가리고 있는가?",
        "improvement": "하루를 5개 시간대 밴드로 재구성하고 낮·심야를 비교",
        "key_result": (
            f"낮 평균 속도가 심야보다 {abs(v3_speed['diff_pct']):.1f}% 낮고, "
            f"Cohen's d={v3_speed['cohens_d']:.2f}로 큰 효과"
        ),
        "report_path": "report_v3.md",
    },
]

# 3. 최종 분석(v3)의 표를 Markdown에서 읽기 쉬운 표시 형식으로 가공한다.
band_stats = pd.read_csv(TABLES / "band_stats_v3.csv", index_col=0).round(3)
band_stats["n"] = band_stats["n"].astype(int).map("{:,}".format)

ttest_display = ttest_v3.copy()
for column in ttest_display.select_dtypes(include="number").columns:
    if column != "p_value":
        ttest_display[column] = ttest_display[column].round(4)
ttest_display["p_value"] = ttest_display["p_value"].map(format_p_value)

model_metrics = pd.read_csv(TABLES / "regression_metrics.csv").iloc[0]
model_display = pd.DataFrame(
    [
        {
            "RMSE": f"{model_metrics['rmse']:.3f}",
            "MAE": f"{model_metrics['mae']:.3f}",
            "R²": f"{model_metrics['r2']:.4f}",
            "평가 표본 수": f"{int(model_metrics['n_test']):,}",
        }
    ]
)

# 4. Pandas·Polars 비교 결과를 평가자가 빠르게 확인할 수 있게 체크 목록으로 만든다.
comparison_checks = [
    {"label": "원천 데이터 shape", "passed": comparison["same_raw_shape"]},
    {"label": "정제 후 shape", "passed": comparison["same_cleaned_shape"]},
    {"label": "정제 후 컬럼", "passed": comparison["same_cleaned_columns"]},
    {"label": "정제 후 결측치", "passed": comparison["same_cleaned_null_counts"]},
    {"label": "정제 후 논리 자료형", "passed": comparison["same_cleaned_dtypes"]},
    {
        "label": "주요 수치 컬럼 평균·합계",
        "passed": comparison["same_cleaned_numeric_summary"],
    },
]

# 보고서에 연결할 정적·인터랙티브 차트의 제목과 상대 경로를 한곳에서 관리한다.
charts = [
    {"title": "상관관계 히트맵", "path": "outputs/figures/correlation_heatmap.png"},
    {"title": "출퇴근·비출퇴근 박스 플롯", "path": "outputs/figures/rush_vs_nonrush_boxplot.png"},
    {"title": "속도·마일당 요금 박스 플롯", "path": "outputs/figures/speed_fare_boxplot_v2.png"},
    {"title": "시간대별 프로파일", "path": "outputs/figures/hourly_profile_v3.png"},
    {"title": "시간대 밴드별 속도 박스 플롯", "path": "outputs/figures/band_speed_boxplot_v3.png"},
    {"title": "시간대별 인터랙티브 Plotly 차트", "path": "outputs/figures/hourly_profile_interactive.html"},
]

# 여러 통계표를 그대로 나열하지 않고 최종적으로 해석할 핵심 메시지를 정리한다.
final_findings = [
    (
        f"낮(10~16시)의 평균 속도는 심야(0~6시)보다 "
        f"{abs(v3_speed['diff_pct']):.1f}% 낮고 효과크기는 큽니다"
        f"(d={v3_speed['cohens_d']:.2f})."
    ),
    (
        f"낮의 평균 이동거리는 심야보다 {abs(v3_distance['diff_pct']):.1f}% 짧아 "
        "시간대별 운행 구성이 다릅니다."
    ),
    (
        f"총요금은 {abs(v3_total['diff_pct']):.1f}% 차이가 있지만 "
        f"효과크기는 {v3_total['cohens_d']:.2f}로 실질적 차이는 미미합니다."
    ),
]

# 5. Jinja2 환경을 설정하고 재사용 가능한 템플릿을 불러온다.
environment = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
environment.filters["comma"] = comma
template = environment.get_template("report.md.j2")

# 계산된 수치와 표를 컨텍스트로 전달하여 최종 Markdown을 렌더링한다.
rendered = template.render(
    generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    raw_rows=comparison["pandas_raw_shape"][0],
    raw_columns=comparison["pandas_raw_shape"][1],
    cleaned_rows=len(df),
    cleaned_columns=len(df.columns),
    group_counts=df["analysis_group"].value_counts().to_dict(),
    null_counts={column: int(count) for column, count in df.isna().sum().items() if count},
    remaining_duplicate_rows=int(df.duplicated().sum()),
    comparison_checks=comparison_checks,
    all_comparisons_passed=comparison["all_cleaned_checks_passed"],
    analysis_stages=analysis_stages,
    descriptive_table=descriptive.to_markdown(),
    correlation_table=correlation.to_markdown(),
    band_stats_table=band_stats.to_markdown(),
    ttest_table=ttest_display.to_markdown(index=False),
    model_table=model_display.to_markdown(index=False),
    model_mae=f"{model_metrics['mae']:.2f}",
    charts=charts,
    final_findings=final_findings,
)

# UTF-8로 저장해 Windows와 macOS에서 한글 보고서가 동일하게 보이도록 한다.
out_path = ROOT / "report.md"
out_path.write_text(rendered, encoding="utf-8")
print(f"saved: {out_path}")
