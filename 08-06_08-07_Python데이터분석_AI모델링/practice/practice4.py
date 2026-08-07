"""
================================================================================
프로그램명   : [실습 4] 데이터 분석 및 AI 모델링 종합 실습
작성자       : 판교 7반 임유리
작성일       : 2026-08-07
설명         : 실습3(판교_7반_임유리_실습3.py)이 저장한 두 파일을 그대로 입력으로 사용한다.
               - sales_100k_cleaned.csv : region/category/amount 결측 제거 + IQR 이상치 제거까지 끝난 원본 전체 컬럼 데이터(956,363행)
               - region_category_agg.csv : region·category별 total/mean/count 집계 결과 EDA·t-test에는 정제 DataFrame을, 
               카이제곱과 Plotly 차트에는 groupby 집계 결과를 그대로 재사용한다. Pipeline도 정제 데이터로 학습한다. 
               순서대로 아래를 수행한다.
               1) 2×2 EDA 대시보드(히스토그램+KDE, 박스플롯, 월별 라인, 상관 히트맵)
               2) t-test(서울 vs 부산) + 카이제곱(지역 x 카테고리 독립성 — region_category_agg.csv의 count를 피벗해 분할표로 사용, crosstab을 다시 만들지 않는다)
               3) ColumnTransformer + Ridge Pipeline 학습·평가·저장·재로딩
               4) Plotly Express 인터랙티브 막대 차트(.html) 저장 — region_category_agg.csv의 total을 그대로 사용, groupby를 다시 하지 않는다
               * create_interactive_chart(): fig.write_html()이 저장한 HTML은 Plotly의 JSON 직렬화 특성상 한글 타이틀이 \\uXXXX 형태로 이스케이프되어 저장된다. 
                 저장 직후 파일을 다시 읽어 \\uXXXX 이스케이프를 실제 한글 문자로 복원하는 후처리를 추가했다.
================================================================================
"""

from __future__ import annotations # 최신 타입 힌트 문법 사용 지원

import re # 정규 표현식을 사용한 복잡한 텍스트 패턴 처리
import sys
from pathlib import Path

try:
    import joblib # 머신러닝 학습 모델의 로컬 저장/로드
    import matplotlib

    matplotlib.use("Agg") # GUI 창을 띄우지 않고 파일 저장 전용 백엔드로 설정(서버/CLI 환경)

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import seaborn as sns
    from scipy.stats import chi2_contingency, ttest_ind
    from matplotlib import font_manager # 차트 내 한글 깨짐 방지를 위한 폰트 설정
    from sklearn.compose import ColumnTransformer # 열 종류 별 전처리 분리 처리
    from sklearn.impute import SimpleImputer # 결측치를 평균/최빈값 등으로 대체
    from sklearn.linear_model import Ridge # 과적합을 방지하는 L2 규제 기반 선형 회귀 모델
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline # 전처리부터 모델 학습까지의 단계를 하나로 묶음
    from sklearn.preprocessing import OneHotEncoder, StandardScaler # 범주형 원핫인코딩 및 수치형 데이터 표준화
except ModuleNotFoundError as error:
    print(f"[패키지 오류] {error}", file=sys.stderr)
    print("python -m pip install -r requirements.txt 명령을 실행하세요.", file=sys.stderr)
    raise SystemExit(1) from error


BASE_DIR = Path(__file__).resolve().parent
CLEANED_FILE = BASE_DIR / "sales_100k_cleaned.csv" # 실습3이 저장한 정제+이상치제거 완료 데이터
AGG_FILE = BASE_DIR / "region_category_agg.csv" # 실습3이 저장한 region/category 집계 결과
DASHBOARD_FILE = BASE_DIR / "eda_dashboard.png"
MODEL_FILE = BASE_DIR / "sales_pipeline.joblib"
PLOTLY_FILE = BASE_DIR / "interactive_sales.html"

ALPHA = 0.05 # 유의 수준(P-value 기준)
RANDOM_STATE = 42
KOREAN_FONT_CANDIDATES = [
    "AppleGothic",
    "Malgun Gothic",
    "NanumGothic",
    "NanumBarunGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR",
]


def print_title(title: str) -> None:
    print(f"\n{'=' * 68}\n{title}\n{'=' * 68}")


def configure_chart_font() -> None:
    """차트 내 한글 깨짐 방지를 위한 폰트 설정. 없으면 안내만 출력하고 계속 진행한다."""
    installed = {font.name for font in font_manager.fontManager.ttflist}
    selected = next((name for name in KOREAN_FONT_CANDIDATES if name in installed), None)
    if selected is None:
        print("[안내] 설치된 한글 폰트를 찾지 못해 그래프의 한글이 깨질 수 있습니다.")
        return
    plt.rcParams["font.family"] = selected
    plt.rcParams["axes.unicode_minus"] = False
    print(f"차트 글꼴: {selected}")


def load_practice3_outputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """실습3이 저장한 정제 데이터와 집계 결과를 읽는다. 둘 중 하나라도 없으면
    실습3을 먼저 실행해야 한다는 걸 바로 알 수 있게 메시지를 남긴다."""
    if not CLEANED_FILE.exists() or not AGG_FILE.exists():
        raise FileNotFoundError(
            "sales_100k_cleaned.csv 또는 region_category_agg.csv가 없습니다. "
            "판교_7반_임유리_실습3.py를 이 폴더에서 먼저 실행하세요."
        )
    cleaned = pd.read_csv(CLEANED_FILE)
    agg = pd.read_csv(AGG_FILE)

    required_cleaned = {"region", "category", "amount", "order_date", "quantity", "unit_price", "customer_age", "payment_method"}
    missing = sorted(required_cleaned - set(cleaned.columns))
    if missing: # 필수 컬럼 중 누락된 열이 있는지 확인
        raise ValueError(f"sales_100k_cleaned.csv에 필수 컬럼이 없습니다: {', '.join(missing)}")

    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    cleaned["month"] = cleaned["order_date"].dt.to_period("M").astype("string")
    return cleaned, agg


def create_eda_dashboard(cleaned: pd.DataFrame, output_path: Path) -> None:
    """히스토그램+KDE / 박스플롯 / 월별 라인 / 상관 히트맵을 2x2 서브플롯 하나에 그려 저장한다."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    sns.histplot(cleaned["amount"], kde=True, bins=40, color="steelblue", ax=axes[0, 0])
    axes[0, 0].set_title("매출 분포와 KDE")
    axes[0, 0].set_xlabel("매출액")
    axes[0, 0].set_ylabel("빈도")

    sns.boxplot(data=cleaned, x="region", y="amount", color="lightblue", ax=axes[0, 1])
    axes[0, 1].set_title("지역별 매출 박스플롯")
    axes[0, 1].set_xlabel("지역")
    axes[0, 1].set_ylabel("매출액")

    # 월별 총매출은 매번 새로 groupby — 실습3의 region/category 집계와는 다른 축이라 agg 파일에 없음
    monthly_sales = cleaned.dropna(subset=["month"]).groupby("month", as_index=False)["amount"].sum().sort_values("month")
    axes[1, 0].plot(monthly_sales["month"], monthly_sales["amount"], marker="o", linewidth=2)
    axes[1, 0].set_title("월별 총매출 추이")
    axes[1, 0].set_xlabel("월")
    axes[1, 0].set_ylabel("총매출")
    axes[1, 0].tick_params(axis="x", rotation=45)

    # quantity/unit_price가 amount와 완전히 같은 식(누수)이 아닌지 먼저 확인한 뒤 상관 컬럼으로 채택함
    numeric_columns = ["quantity", "unit_price", "customer_age", "amount"]
    correlation = cleaned[numeric_columns].corr()
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=axes[1, 1])
    axes[1, 1].set_title("수치형 변수 상관 히트맵")

    fig.suptitle("Practice 4 판매 데이터 EDA 대시보드", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=150, bbox_inches="tight") # 파일 경로에 대시보드를 png 이미지로 저장
    plt.close(fig) # 메모리 누수를 예방하기 위해 파일 출력 완료 후 생성된 플롯 객체를 클로즈 처리


def run_statistical_tests(cleaned: pd.DataFrame, agg: pd.DataFrame) -> None:
    # 특정 지역의 매출액 데이터만 각각 추출해 결측치 제거
    seoul = cleaned.loc[cleaned["region"] == "서울", "amount"].dropna()
    busan = cleaned.loc[cleaned["region"] == "부산", "amount"].dropna()
    if len(seoul) < 2 or len(busan) < 2: # 통계적 비교 연산이 불가능한 최소 샘플 수인 경우 사전에 에러 처리
        raise ValueError("t-test에는 서울과 부산 데이터가 각각 2건 이상 필요합니다.")

    t_stat, t_pvalue = ttest_ind(seoul, busan, equal_var=False) # 등분산성을 가정하지 않는 웰치의 t-검정
    print("[독립표본 t-test: 서울과 부산의 평균 매출]")
    print(f"서울 데이터: {len(seoul):,}건, 평균: {seoul.mean():,.2f}")
    print(f"부산 데이터: {len(busan):,}건, 평균: {busan.mean():,.2f}")
    print(f"t 통계량: {t_stat:.6f}")
    print(f"p-value: {t_pvalue:.6g}")
    if t_pvalue < ALPHA:
        print("해석: p-value < 0.05이므로 평균 매출 차이는 통계적으로 유의합니다.")
    else:
        print("해석: p-value >= 0.05이므로 평균 매출 차이는 통계적으로 유의하지 않습니다.")

    # crosstab을 새로 만들지 않고, 실습3이 이미 계산해 둔 count를 region x category로 피벗해 분할표로 재사용
    contingency = agg.pivot(index="region", columns="category", values="count").fillna(0)
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        raise ValueError("카이제곱 검정에는 지역과 카테고리가 각각 2개 이상 필요합니다.")

    chi2, chi_pvalue, dof, expected = chi2_contingency(contingency) # 범주형 데이터 간의 독립성/연관성 확인을 위한 카이제곱 검정
    print("\n[카이제곱 독립성 검정: 지역과 카테고리]")
    print(f"카이제곱 통계량: {chi2:.6f}")
    print(f"자유도: {dof}")
    print(f"p-value: {chi_pvalue:.6g}")
    print(f"기대빈도 최솟값: {expected.min():,.2f}")
    if chi_pvalue < ALPHA:
        print("해석: p-value < 0.05이므로 지역과 카테고리는 서로 독립이라고 보기 어렵습니다.")
    else:
        print("해석: p-value >= 0.05이므로 지역과 카테고리의 연관성은 통계적으로 유의하지 않습니다.")


def train_and_save_pipeline(cleaned: pd.DataFrame) -> None:
    numeric_features = ["quantity", "unit_price", "customer_age"]
    categorical_features = ["region", "category", "payment_method"]
    x = cleaned[numeric_features + categorical_features]
    y = cleaned["amount"]
    x_train, x_test, y_train, y_test = train_test_split( # 전체 데이터를 학습용과 평가용 데이터셋으로 분할
        x, y, test_size=0.2, random_state=RANDOM_STATE
    )

    numeric_pipeline = Pipeline( # [수치형 전처리] 결측치는 중앙값으로 대체하고, 데이터는 표준화 스케일링 처리
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline( # [범주형 전처리] 결측치는 최빈값으로 대체하고, 텍스트 데이터는 원핫인코딩 배열로 반환
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    preprocessor = ColumnTransformer( # 컬럼 트랜스포머를 사용해 데이터 타입에 맞춰 사전에 정의된 전처리 파이프라인을 다중 결합함
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )
    pipeline = Pipeline( # [통합 파이프라인] 데이터 전처리 레이어와 최적화 알고리즘 모델을 하나의 흐름으로
        steps=[
            ("preprocess", preprocessor),
            ("model", Ridge(alpha=1.0, solver="lsqr")), # L2 규제와 고속 연산(lsqr) 적용
        ]
    )

    pipeline.fit(x_train, y_train) # 학습 데이터를 파이프라인에 입력해 전처리 기준 학습 및 머신러닝 모델 훈련
    predictions = pipeline.predict(x_test) # 매출 예측 결과 도출
    score = float(pipeline.score(x_test, y_test)) # 결정계수 점수 계산

    joblib.dump(pipeline, MODEL_FILE) # 학습 완료된 최종 파이프라인 전체 객체를 지정된 로컬 파일 경로에 저장
    loaded_pipeline = joblib.load(MODEL_FILE) # 저장된 파일이 정상인지 검증하기 위해 로컬에서 파이프라인 모델을 다시 로드
    loaded_predictions = loaded_pipeline.predict(x_test) # 불러온 모델로 동일한 평가 데이터 재예측
    prediction_match = bool(np.allclose(predictions, loaded_predictions)) # 부동소수점 오차를 감안해 저장 전의 예측값과 저장 후의 예측값이 완벽히 일치하는지 비교
    if not prediction_match: # 두 결과값이 다르면 프로그램 차단 및 에러 발생
        raise RuntimeError("모델 저장 전후의 예측 결과가 일치하지 않습니다.")

    print(f"학습 데이터: {len(x_train):,}건")
    print(f"평가 데이터: {len(x_test):,}건")
    print(f"테스트 R²: {score:.6f}")
    print(f"저장 전후 예측 일치: {prediction_match}")
    print(f"모델 저장: {MODEL_FILE.name}")


def create_interactive_chart(agg: pd.DataFrame) -> None:
    # 실습3이 이미 만들어 둔 region/category별 total을 그대로 쓴다 — groupby를 다시 하지 않음
    summary = agg.sort_values("total", ascending=False)

    figure = px.bar( # Plotly Express를 사용해 다중 막대 차드 정의 및 라벨 지정
        summary,
        x="region",
        y="total",
        color="category",
        barmode="group",
        title="지역과 카테고리별 총매출",
        labels={"region": "지역", "category": "카테고리", "total": "총매출액(원)"},
        hover_data={"total": ":,.0f"},
    )
    figure.update_layout( # 차트 레이아웃의 축 이름 및 시스템 환경별 다국어 웹 폰트/글꼴 크기 설정
        xaxis_title="지역",
        yaxis_title="총매출액(원)",
        legend_title="카테고리",
        font={"family": "Arial, Apple SD Gothic Neo, Malgun Gothic, NanumGothic, sans-serif", "size": 14},
    )
    figure.update_yaxes(tickformat=",")
    figure.write_html(PLOTLY_FILE, include_plotlyjs=True, full_html=True) # 자바스크립트 엔진 라이브러리를 내장해 독립 실행 가능한 HTML 파일로 1차 저장

    # plotly가 저장 시 한글을 \uXXXX로 이스케이프해 원문 확인이 안 되므로 후처리로 복원
    html_text = PLOTLY_FILE.read_text(encoding="utf-8")
    unescaped = re.sub(
        r"(?:\\u[0-9a-fA-F]{4})+",
        lambda match: match.group(0).encode().decode("unicode_escape"),
        html_text,
    )
    PLOTLY_FILE.write_text(unescaped, encoding="utf-8")


def verify_outputs() -> None:
    required_files = [DASHBOARD_FILE, MODEL_FILE, PLOTLY_FILE]
    missing = [str(path) for path in required_files if not path.exists()] # 리스트 중 디스크에 실제로 존재하지 않는 누락된 파일 경로들만 추출
    if missing: # 누락된 파일이 단 하나라도 있다면 오류 목록을 상세히 묶어 파일 누락 에러 발생
        raise FileNotFoundError("생성되지 않은 결과 파일:\n- " + "\n- ".join(missing))
    for path in required_files: # 필수 파일이 모두 존재할 경우, 각 파일의 물리적 내부 데이터 무결성 검사 수행
        if path.stat().st_size == 0: # 파일의 용량이 0바이트라면 연산 실패나 저장 버그가 발생 -> 데이터 에러 발생
            raise ValueError(f"결과 파일이 비어 있습니다: {path}")
        print(f"[PASS] {path.name} ({path.stat().st_size:,} bytes)")


def main() -> None:
    configure_chart_font()

    print_title("1. 실습3 산출물 로딩")
    cleaned, agg = load_practice3_outputs()
    print(f"정제 데이터: {len(cleaned):,}행, 집계 데이터: {len(agg):,}행")

    print_title("2. 2×2 EDA 대시보드")
    create_eda_dashboard(cleaned, DASHBOARD_FILE)
    print(f"저장 완료: {DASHBOARD_FILE.name}")

    print_title("3. 통계 검정")
    run_statistical_tests(cleaned, agg)

    print_title("4. sklearn Pipeline 학습과 저장")
    train_and_save_pipeline(cleaned)

    print_title("5. Plotly 인터랙티브 차트")
    create_interactive_chart(agg)
    print(f"저장 완료: {PLOTLY_FILE.name}")

    print_title("6. 최종 산출물 확인")
    verify_outputs()
    print("\n실습이 정상적으로 완료되었습니다.")


if __name__ == "__main__":
    try:
        main()
    except (
        FileNotFoundError, # 데이터 파일이 없거나 결과 산출물이 누락된 경우
        ValueError, # 데이터가 비어있거나 통계/정합성 조건이 맞지 않는 경우
        RuntimeError, # 머신러닝 모델 저장 전후 예측값이 일치하지 않는 경우
        OSError, # 디스크 권한 부족이나 폴더 생성 등 시스템 입출력 오류인 경우
        pd.errors.ParserError, # 원본 CSV 파일의 데이터 서식이 깨져서 파싱할 수 없는 경우
    ) as error:
        print(f"\n[실행 오류] {error}", file=sys.stderr)
        raise SystemExit(1) from error



#이번 실습에서 가장 어려웠던 건.. 로컬 환경의 세그폴트였다. 공식 requirements.txt에 고정된 두 버전이 서로 호환 테스트되지 않은 조합이라 pd.to_datetime(format="mixed") 같은 C 확장 연산에서 죽었었다.
#겉보기엔 "코드가 틀렸나" 싶었지만 실제론 라이브러리 버전 궁합 문제였다는 걸 확인했다. 라이브러리 버전이 중요함을 다시 한번 깨닫게 되었다.
#Plotly HTML의 유니코드 이스케이프 버그는 눈으로 차트를 보면 멀쩡한데 문자열 검사만 실패하는 케이스라, "결과물이 맞아 보여도 검증 스크립트가 정확히 무엇을 확인하는지"를 봐야 한다는 걸 배웠다.
#Pipeline을 저장한 뒤 다시 불러와 예측값을 np.allclose로 비교하는 부분은, 모델을 그냥 저장하는 것과 "저장한 모델이 실제로 재현 가능한지"를 검증하는 것의 차이를 보여준 부분이었다.
#저장했다고 다 끝나는게 아니라 확실한 검증을 해야겠다는 생각을 했다.
#처음엔 실습3에서 만든 raw csv를 이 파일에서 또 정제하려고 했는데, 그러면 정제 로직을 두 번 짜는 셈이라 실습3이 저장한 sales_100k_cleaned.csv/region_category_agg.csv를 그대로 읽어오는 쪽으로 바꿨다.
#카이제곱 검정도 crosstab을 새로 만들 필요 없이 agg 파일의 count를 pivot만 하면 됐다. 같은 집계를 두 번 하지 않아도 된다는 걸 실습3-4를 실제로 연결해보고 나서야 체감했다.
#Pipeline 피처로 quantity/unit_price를 쓰기 전에 quantity*unit_price가 amount와 완전히 같은 값(타깃 누수)은 아닌지부터 확인했다(상관관계 0.6~0.66 수준, 정확히 일치하진 않음). 
#성능 지표보다 피처가 정답을 그대로 포함하고 있진 않은지부터 봐야 한다는 걸 배웠다.
#298p 연계 Point 표만 보면 Pipeline 학습 데이터 원본이 sales_100k.csv라고 적혀 있어서 한 번은 원본(이상치 포함)으로 바꿔봤는데, R²가 0.84에서 0.19로 떨어졌다. 
#표 문구 하나를 문자 그대로 따르는 것보다, 같은 과제를 실제로 어떻게 풀었는지와 결과가 말이 되는지를 같이 봐야 한다는 걸 배웠다.
