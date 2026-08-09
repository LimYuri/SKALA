"""[10] 시간대별 속도·마일당 요금을 Plotly 인터랙티브 차트로 저장한다.

입력: data/processed/trips_clean.parquet
출력: outputs/figures/hourly_profile_interactive.html

정적 PNG를 보완해 사용자가 시간별 정확한 평균값을 hover로 확인하고
확대·축소할 수 있도록 독립 실행 가능한 HTML 파일을 생성한다.
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")

# v2·v3와 같은 파생 지표와 속도 범위를 사용해 차트 수치를 일치시킨다.
df["speed_mph"] = df["trip_distance"] / (df["trip_duration_minutes"] / 60)
df["fare_per_mile"] = df["total_amount"] / df["trip_distance"]
df = df[(df["speed_mph"] > 0) & (df["speed_mph"] <= 80)]

# 24개 시간 단위 평균으로 집계해 인터랙티브 차트의 데이터 크기를 줄인다.
hourly = df.groupby("pickup_hour")[["speed_mph", "fare_per_mile"]].mean().reset_index()

# 속도와 마일당 요금의 축 단위가 다르므로 두 개의 나란한 서브플롯으로 구성한다.
fig = make_subplots(rows=1, cols=2, subplot_titles=("평균 속도 (mph)", "마일당 요금 ($)"))
fig.add_trace(
    go.Scatter(x=hourly["pickup_hour"], y=hourly["speed_mph"], mode="lines+markers",
               name="speed_mph", line=dict(color="#4C72B0")),
    row=1, col=1,
)
fig.add_trace(
    go.Scatter(x=hourly["pickup_hour"], y=hourly["fare_per_mile"], mode="lines+markers",
               name="fare_per_mile", line=dict(color="#DD8452")),
    row=1, col=2,
)
# 기존 출퇴근 정의(7-9시, 17-19시) 구간을 음영으로 표시해 v3 인사이트(낮이 더 막힘)와 대조
for start, end in [(7, 9), (17, 19)]:
    for col in (1, 2):
        fig.add_vrect(x0=start, x1=end, fillcolor="#DD8452", opacity=0.12, line_width=0, row=1, col=col)

fig.update_xaxes(title_text="승차 시각", dtick=3)
fig.update_layout(title="시간대별 속도·마일당 요금 (hover로 시간별 정확한 값 확인)", showlegend=False)

# full HTML로 저장해 별도 Python 환경 없이 브라우저에서 열 수 있게 한다.
out_path = ROOT / "outputs" / "figures" / "hourly_profile_interactive.html"
fig.write_html(out_path)
print(f"saved: {out_path}")
