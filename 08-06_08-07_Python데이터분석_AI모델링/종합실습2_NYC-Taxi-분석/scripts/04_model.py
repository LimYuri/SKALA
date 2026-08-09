"""[04] 총요금을 예측하는 재현 가능한 선형회귀 Pipeline을 학습한다.

입력: data/processed/trips_clean.parquet
출력:
  - outputs/tables/regression_coefficients.csv
  - outputs/tables/regression_metrics.csv
  - models/total_amount_regression_pipeline.joblib

전처리(StandardScaler)와 모델(LinearRegression)을 하나로 묶어 저장함으로써
재로딩·배포 시에도 학습 때와 동일한 스케일링이 적용되도록 한다.
"""
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_parquet(ROOT / "data" / "processed" / "trips_clean.parquet")

FEATURES = ["trip_distance", "trip_duration_minutes", "pickup_hour", "is_rush_hour"]
TARGET = "total_amount"

# 불리언 피처는 sklearn 수치 전처리에 명확히 전달되도록 0/1로 변환한다.
X = df[FEATURES].copy()
X["is_rush_hour"] = X["is_rush_hour"].astype(int)
y = df[TARGET]

# 동일한 평가 결과를 재현할 수 있도록 분할 비율과 난수 시드를 고정한다.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 전처리(스케일링)+모델을 하나의 파이프라인으로: 배포/재사용 시 스케일링 누락 위험을 없앤다
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("reg", LinearRegression()),
])
pipeline.fit(X_train, y_train)
pred = pipeline.predict(X_test)

# RMSE는 큰 오차에 민감하고, MAE는 평균적인 달러 오차, R²는 설명력을 나타낸다.
rmse = np.sqrt(mean_squared_error(y_test, pred))
mae = mean_absolute_error(y_test, pred)
r2 = r2_score(y_test, pred)

# 계수는 스케일링된 피처 기준 (표준편차 1단위 변화당 total_amount 변화량) -> 피처 간 영향력 비교에 용이
reg = pipeline.named_steps["reg"]
coef_table = pd.DataFrame({"feature": FEATURES, "coefficient_scaled": reg.coef_})
coef_table.loc[len(coef_table)] = ["intercept", reg.intercept_]

print("=== 선형회귀 결과 (total_amount 예측, Pipeline: StandardScaler + LinearRegression) ===")
print(coef_table.to_string(index=False))
print(f"\nRMSE: {rmse:.3f}")
print(f"MAE:  {mae:.3f}")
print(f"R^2:  {r2:.4f}")

# 수치 결과는 보고서 자동 생성에서 다시 사용할 수 있도록 CSV로 저장한다.
out = ROOT / "outputs" / "tables"
coef_table.to_csv(out / "regression_coefficients.csv", index=False)
pd.DataFrame([{"rmse": rmse, "mae": mae, "r2": r2, "n_test": len(y_test)}]).to_csv(
    out / "regression_metrics.csv", index=False
)

# 전처리까지 포함한 Pipeline 전체를 하나의 joblib 파일로 영속화한다.
model_dir = ROOT / "models"
model_dir.mkdir(exist_ok=True)
model_path = model_dir / "total_amount_regression_pipeline.joblib"
joblib.dump(pipeline, model_path)
print(f"\nmodel saved: {model_path}")
