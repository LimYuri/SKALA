"""[03] 최초 분석(v1)의 EDA·상관분석·출퇴근 그룹 검정을 수행한다.

입력: data/processed/trips_clean.parquet
출력: 기술통계·상관행렬·Welch t-test CSV와 Seaborn PNG 차트

이 단계는 최초 가설인 '출퇴근과 비출퇴근 운행에 차이가 있는가?'를
검증하는 기준선이며, 이후 v2·v3 분석의 출발점으로 사용된다.
"""
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from plot_config import configure_matplotlib

# 운영체제별 한글 폰트를 설정한 뒤 모든 정적 차트를 생성한다.
configure_matplotlib()

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"

METRICS = ["trip_distance", "total_amount", "trip_duration_minutes"]
PALETTE = {"출퇴근": "#4C72B0", "비출퇴근": "#DD8452"}  # seaborn colorblind pair

# --- 1. 기술통계 ---
# PDF 요구사항인 평균·표준편차·25/50/75% 분위수를 전체와 그룹별로 산출한다.
desc_overall = df[METRICS].describe(percentiles=[0.25, 0.5, 0.75]).T
desc_overall.to_csv(TABLES / "descriptive_overall.csv")

desc_group = df.groupby("analysis_group")[METRICS].describe(percentiles=[0.25, 0.5, 0.75])
desc_group.to_csv(TABLES / "descriptive_by_group.csv")
print("=== 기술통계 (그룹별) ===")
print(desc_group)

# --- 2. 상관분석 및 Seaborn 히트맵 ---
# 수치 컬럼 간 Pearson 상관계수로 거리·시간·요금의 선형 관계를 확인한다.
corr_cols = ["trip_distance", "trip_duration_minutes", "passenger_count", "total_amount"]
corr = df[corr_cols].corr()
corr.to_csv(TABLES / "correlation_matrix.csv")
print("\n=== 상관행렬 ===")
print(corr)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1, square=True,
            cbar_kws={"label": "Pearson r"}, ax=ax)
ax.set_title("변수 간 상관관계")
fig.tight_layout()
fig.savefig(FIGS / "correlation_heatmap.png", dpi=150)
plt.close(fig)

# --- 3. 최초 가설 검정: 출퇴근 vs 비출퇴근 ---
rush = df[df["is_rush_hour"]]
non_rush = df[~df["is_rush_hour"]]

results = []
for metric in ["total_amount", "trip_distance"]:
    # equal_var=False: Welch's t-test. 두 그룹 표본 수(306만 vs 601만)가 크게 달라 등분산 가정이 위험함
    t_stat, p_val = stats.ttest_ind(rush[metric], non_rush[metric], equal_var=False)
    results.append({
        "metric": metric,
        "rush_mean": rush[metric].mean(),
        "non_rush_mean": non_rush[metric].mean(),
        "diff": rush[metric].mean() - non_rush[metric].mean(),
        "t_stat": t_stat,
        "p_value": p_val,
        "significant_at_0.05": p_val < 0.05,
    })
ttest_df = pd.DataFrame(results)
ttest_df.to_csv(TABLES / "ttest_results.csv", index=False)
print("\n=== t-test (Welch) ===")
print(ttest_df.to_string(index=False))

# --- 4. 그룹별 분포 시각화 ---
# 표본이 매우 크므로 극단값 표시는 숨기고 중앙값과 사분위 범위 비교에 집중한다.
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for ax, metric, title in zip(axes, ["total_amount", "trip_distance"], ["총 요금 ($)", "이동거리 (mi)"]):
    sns.boxplot(data=df, x="analysis_group", y=metric, hue="analysis_group",
                order=["출퇴근", "비출퇴근"], palette=PALETTE, showfliers=False,
                legend=False, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("")
fig.suptitle("출퇴근 vs 비출퇴근 비교")
fig.tight_layout()
fig.savefig(FIGS / "rush_vs_nonrush_boxplot.png", dpi=150)
plt.close(fig)

print(f"\n저장 완료: {TABLES} / {FIGS}")
