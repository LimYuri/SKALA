"""[08] 2차 개선(v3): 하루를 시간대 밴드로 재구성해 운행 특성을 분석한다.

입력: data/processed/trips_clean.parquet
출력: 시간대 밴드 통계·낮/심야 t-test CSV와 시간대별 PNG 차트

출퇴근·비출퇴근 이분법에서 심야(빠름)와 낮(혼잡)이 같은 그룹에 섞이는
평균 상쇄 문제를 확인하고, 시간대별 EDA에 맞춰 5개 구간으로 재설계한다.
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from plot_config import configure_matplotlib

# 운영체제에 맞는 한글 폰트를 선택한다.
configure_matplotlib()

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"

df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")
# v2와 같은 파생 지표·속도 필터를 사용해 버전 간 비교 기준을 유지한다.
df["speed_mph"] = df["trip_distance"] / (df["trip_duration_minutes"] / 60)
df["fare_per_mile"] = df["total_amount"] / df["trip_distance"]
df = df[(df["speed_mph"] > 0) & (df["speed_mph"] <= 80)]

# --- 1. 시간대 밴드 정의 ---
BANDS = {
    # v2까지의 "출퇴근/비출퇴근" 이분법 대신, 실측 speed_mph 프로파일(hourly_profile_v3.png)에서
    # 곡선이 꺾이는 지점 기준으로 5구간을 다시 나눔 (심야가 가장 빠르고 낮이 가장 느림)
    "심야(0~6시)": range(0, 7),
    "출근피크(7~9시)": range(7, 10),
    "낮(10~16시)": range(10, 17),
    "퇴근피크(17~19시)": range(17, 20),
    "밤(20~23시)": range(20, 24),
}
hour_to_band = {h: band for band, hours in BANDS.items() for h in hours}
df["time_band"] = df["pickup_hour"].map(hour_to_band)
band_order = list(BANDS)

METRICS = ["speed_mph", "fare_per_mile", "trip_distance", "total_amount"]

# --- 2. 시간대 밴드별 표본 수·평균·표준편차 ---
band_stats = df.groupby("time_band")[METRICS].agg(["mean", "std"]).reindex(band_order).round(3)
band_stats.columns = [f"{c}_{s}" for c, s in band_stats.columns]
band_stats.insert(0, "n", df["time_band"].value_counts().reindex(band_order))
band_stats.to_csv(TABLES / "band_stats_v3.csv")
print("=== 시간대 밴드별 기술통계 (v3) ===")
print(band_stats)


def cohens_d(a, b):
    """두 시간대 평균 차이를 pooled 표준편차 단위로 변환한다."""
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(((n1 - 1) * a.std() ** 2 + (n2 - 1) * b.std() ** 2) / (n1 + n2 - 2))
    return (a.mean() - b.mean()) / pooled_std


# --- 3. 탐색적 후속 검정: 낮(10~16시) vs 심야(0~6시) ---
# 시간대별 EDA에서 가장 대비가 컸던 두 구간이므로 확증적 인과 검정이 아닌 탐색 결과로 해석한다.
day = df[df["time_band"] == "낮(10~16시)"]
night = df[df["time_band"] == "심야(0~6시)"]

results = []
for metric in METRICS:
    # 두 구간의 표본 수가 다르므로 Welch t-test를 사용하고 효과크기를 함께 저장한다.
    t_stat, p_val = stats.ttest_ind(day[metric], night[metric], equal_var=False)
    d = cohens_d(day[metric], night[metric])
    effect = "무시가능" if abs(d) < 0.2 else "작음" if abs(d) < 0.5 else "중간" if abs(d) < 0.8 else "큼"
    results.append({
        "metric": metric,
        "day_mean": day[metric].mean(),
        "night_mean": night[metric].mean(),
        "diff_pct": (day[metric].mean() - night[metric].mean()) / night[metric].mean() * 100,
        "t_stat": t_stat,
        "p_value": p_val,
        "cohens_d": d,
        "effect_size": effect,
    })
ttest_df = pd.DataFrame(results)
ttest_df.to_csv(TABLES / "ttest_results_v3.csv", index=False)
print("\n=== t-test: 낮(10~16시) vs 심야(0~6시) + Cohen's d ===")
print(ttest_df.to_string(index=False))

# --- 4. 시간대별 평균 프로파일 ---
# 기존 출퇴근 음영과 24시간 곡선을 함께 보여 그룹 정의의 한계를 시각적으로 설명한다.
hourly = df.groupby("pickup_hour")[["speed_mph", "fare_per_mile"]].mean()
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, metric, title in zip(axes, ["speed_mph", "fare_per_mile"], ["평균 속도 (mph)", "마일당 요금 ($)"]):
    ax.plot(hourly.index, hourly[metric], marker="o", color="#4C72B0", linewidth=2)
    for start, end in [(7, 9), (17, 19)]:  # 기존 출퇴근 정의 표시
        ax.axvspan(start, end, alpha=0.15, color="#DD8452")
    ax.set_title(title)
    ax.set_xlabel("승차 시각")
    ax.set_xticks(range(0, 24, 3))
    ax.grid(alpha=0.3)
fig.suptitle("시간대별 프로파일 (음영 = 기존 출퇴근 정의: 낮이 출퇴근보다 더 막힌다)")
fig.tight_layout()
fig.savefig(FIGS / "hourly_profile_v3.png", dpi=150)
plt.close(fig)

# --- 5. 시간대 밴드별 속도 분포 ---
fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(data=df, x="time_band", y="speed_mph", order=band_order,
            color="#4C72B0", showfliers=False, ax=ax)
ax.set_title("시간대 밴드별 평균 속도")
ax.set_xlabel("")
ax.set_ylabel("speed (mph)")
fig.tight_layout()
fig.savefig(FIGS / "band_speed_boxplot_v3.png", dpi=150)
plt.close(fig)

print(f"\n저장 완료: {TABLES} / {FIGS}")
