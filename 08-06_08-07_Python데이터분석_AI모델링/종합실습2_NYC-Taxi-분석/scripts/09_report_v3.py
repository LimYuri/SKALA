"""[09] 시간대 밴드 재설계와 낮·심야 검정을 설명하는 v3 보고서를 생성한다.

입력: 08 단계의 시간대 밴드 통계와 t-test 결과
출력: report_v3.md

v1·v2의 그룹 정의가 평균을 상쇄한 이유와 v3에서 실질적으로 큰 속도
차이가 발견된 과정을 보존해 최종 종합 보고서의 분석 이력으로 사용한다.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "outputs" / "tables"

# 시간대 표본 수는 과학적 표기 대신 천 단위 구분자로 표시한다.
band_stats = pd.read_csv(TABLES / "band_stats_v3.csv", index_col=0).round(3)
band_stats["n"] = band_stats["n"].astype(int).map("{:,}".format)
ttest_v3 = pd.read_csv(TABLES / "ttest_results_v3.csv").round(4)

# 문제 정의 → 밴드 통계 → 최종 검정 → 해석 순서로 문서를 구성한다.
lines = [
    "# NYC 옐로우 택시 분석 — 2차 개선: 시간대 밴드 재설계 (v3)",
    "",
    "## 왜 v3인가",
    "",
    "v1·v2의 출퇴근(7~9, 17~19시) vs 비출퇴근 이분법은 효과크기가 전부 '무시가능' 수준이었다. "
    "원인은 그룹 경계 자체에 있었다: '비출퇴근' 안에 가장 빠른 심야(15~18mph)와 가장 막히는 "
    "낮 10~16시(약 8mph)가 함께 묶여 서로 상쇄됐고, 실제로 낮 시간대는 출퇴근 피크보다도 느리다. "
    "뉴욕 택시에게 혼잡은 '출퇴근 시간'이 아니라 '낮 전체'다. v3에서는 `pickup_hour`를 5개 "
    "시간대 밴드로 재그룹핑하고, 대비가 가장 뚜렷한 **낮(10~16시) vs 심야(0~6시)**를 헤드라인 검정으로 잡았다.",
    "",
    "![hourly profile](outputs/figures/hourly_profile_v3.png)",
    "",
    "## 1. 시간대 밴드별 기술통계",
    "",
    band_stats.to_markdown(),
    "",
    "![band speed boxplot](outputs/figures/band_speed_boxplot_v3.png)",
    "",
    "## 2. t-test: 낮(10~16시) vs 심야(0~6시)",
    "",
    ttest_v3.to_markdown(index=False),
    "",
    "## 3. 해석",
    "",
    "- `speed_mph`: 낮이 심야보다 **48% 느림, Cohen's d = -1.53 (큼)** — v1·v2에서 못 보던 "
    "실질적으로 큰 차이. 그룹 경계를 데이터에 맞게 다시 그으니 효과가 드러났다.",
    "- `trip_distance`: 낮이 33% 짧음 (d = -0.39, 작음). 심야는 장거리 이동 비중이 높다.",
    "- `fare_per_mile`: 낮이 33% 비쌈 — 같은 거리를 가도 정체 때문에 시간 요금이 붙는다. "
    "(d는 0.16으로 작게 나오는데, 단거리 trip에서 마일당 요금 분산이 매우 커서 그룹 내 편차가 크기 때문)",
    "- `total_amount`: 여전히 차이 없음 (d = -0.04). **총 요금은 시간대와 거의 무관하다** — "
    "낮에는 '짧은 거리를 비싼 단가로', 심야에는 '긴 거리를 싼 단가로' 이동해 총액이 비슷해진다. "
    "이것이 v1이 밋밋해 보였던 근본 이유다.",
    "",
    "## 결론",
    "",
    "요금 구조의 차이는 총액(`total_amount`)이 아니라 **구성**(거리 × 단가)에 있다. "
    "시간대는 '얼마를 내는가'가 아니라 '무엇에 대해 내는가'(거리 vs 정체 시간)를 바꾼다.",
    "",
]

# v3 자체 보고서를 보존하고, 11 단계의 Jinja2 최종 보고서에서 링크한다.
out_path = ROOT / "report_v3.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"saved: {out_path}")
