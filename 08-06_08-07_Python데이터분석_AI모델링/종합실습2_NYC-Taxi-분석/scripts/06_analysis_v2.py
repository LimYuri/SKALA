"""[06] 1차 개선(v2): 총요금을 속도·거리·단가 지표로 분해한다.

입력: data/processed/trips_clean.parquet
출력: v2 그룹 통계·t-test CSV와 속도·마일당 요금 박스 플롯

v1의 거대한 표본에서는 작은 차이도 p-value가 매우 작게 나오므로,
Cohen's d를 함께 계산해 통계적 유의성과 실질적 효과를 구분한다.
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from plot_config import configure_matplotlib

# 운영체제별 한글 폰트를 적용해 동일한 차트를 생성한다.
configure_matplotlib()

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"
PALETTE = {"출퇴근": "#4C72B0", "비출퇴근": "#DD8452"}

df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")

# 총요금만으로 보이지 않는 운행 효율과 단가 차이를 설명하기 위한 파생 지표다.
df["speed_mph"] = df["trip_distance"] / (df["trip_duration_minutes"] / 60)
df["fare_per_mile"] = df["total_amount"] / df["trip_distance"]
# speed_mph는 파생 시 GPS 오차로 생기는 비현실적 값(>80mph)만 추가로 컷
df = df[(df["speed_mph"] > 0) & (df["speed_mph"] <= 80)]

METRICS = ["total_amount", "trip_distance", "speed_mph", "fare_per_mile"]

# --- 1. 출퇴근·비출퇴근 그룹별 파생 지표 기술통계 ---
desc_group = df.groupby("analysis_group")[METRICS].agg(["mean", "std"]).round(3)
desc_group.columns = [f"{c}_{s}" for c, s in desc_group.columns]
desc_group.to_csv(TABLES / "descriptive_by_group_v2.csv")
print("=== 그룹별 기술통계 (v2) ===")
print(desc_group)


def cohens_d(a, b):
    """두 집단 평균 차이를 pooled 표준편차로 표준화한 효과크기를 반환한다."""
    # 표본 크기(n)에 좌우되는 p-value와 달리, 두 그룹 평균 차이를 pooled std로 나눠 정규화한
    # 효과크기. n이 9백만이라 p-value가 항상 0에 수렴하는 문제를 이걸로 보완한다.
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(((n1 - 1) * a.std() ** 2 + (n2 - 1) * b.std() ** 2) / (n1 + n2 - 2))
    return (a.mean() - b.mean()) / pooled_std


# --- 2. Welch t-test와 Cohen's d ---
rush = df[df["is_rush_hour"]]
non_rush = df[~df["is_rush_hour"]]

results = []
for metric in METRICS:
    # 표본 수와 분산이 다른 두 그룹이므로 등분산을 가정하지 않는 Welch 검정을 사용한다.
    t_stat, p_val = stats.ttest_ind(rush[metric], non_rush[metric], equal_var=False)
    d = cohens_d(rush[metric], non_rush[metric])
    effect = "무시가능" if abs(d) < 0.2 else "작음" if abs(d) < 0.5 else "중간" if abs(d) < 0.8 else "큼"  # Cohen(1988) 관례 기준
    results.append({
        "metric": metric,
        "rush_mean": rush[metric].mean(),
        "non_rush_mean": non_rush[metric].mean(),
        "diff_pct": (rush[metric].mean() - non_rush[metric].mean()) / non_rush[metric].mean() * 100,
        "t_stat": t_stat,
        "p_value": p_val,
        "cohens_d": d,
        "effect_size": effect,
    })
ttest_df = pd.DataFrame(results)
ttest_df.to_csv(TABLES / "ttest_results_v2.csv", index=False)
print("\n=== t-test + Cohen's d (v2) ===")
print(ttest_df.to_string(index=False))

# --- 3. 속도·단가 분포 시각화 ---
# 이상점은 통계 계산에는 포함하되 그림에서는 숨겨 중앙 분포 비교를 쉽게 한다.
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for ax, metric, title in zip(axes, ["speed_mph", "fare_per_mile"], ["평균 속도 (mph)", "마일당 요금 ($)"]):
    sns.boxplot(data=df, x="analysis_group", y=metric, hue="analysis_group",
                order=["출퇴근", "비출퇴근"], palette=PALETTE, showfliers=False,
                legend=False, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("")
fig.suptitle("출퇴근 vs 비출퇴근: 속도·마일당 요금")
fig.tight_layout()
fig.savefig(FIGS / "speed_fare_boxplot_v2.png", dpi=150)
plt.close(fig)

print(f"\n저장 완료: {TABLES} / {FIGS}")
