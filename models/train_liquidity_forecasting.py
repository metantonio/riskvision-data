"""
RiskVision: Daily Liquidity Gap Forecasting Model Training
Entrenamiento del Modelo de Pronóstico de Brecha de Liquidez Diaria

Objective / Objetivo:
Train a time-series regression model to forecast the bank's daily liquidity gap (brecha_liquidez_usd)
for future horizons (e.g., 7 to 30 days). Takes into account the legal reserve requirement (73% BCV),
exchange rate devaluations, deposit dynamics, quincena cycles, and December seasonality.
Entrenar un modelo de regresión para series temporales que pronostique la brecha de liquidez diaria
del banco (brecha_liquidez_usd) a horizontes futuros. Considera el encaje legal (73% BCV),
devaluación cambiaria, ciclos de quincena y estacionalidad navideña.

Related Question / Pregunta Asociada:
Level 4, Question 4.3 in questions.md
"""

import sqlite3
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bank_data.db"))
MODEL_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "liquidity_forecast_model.joblib"))

def load_liquidity_data(db_path=DB_PATH):
    print(f"[+] Loading daily liquidity and macroeconomic time-series from: {db_path}")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        l.fecha,
        l.total_depositos_ves,
        l.total_depositos_usd,
        l.total_creditos_ves,
        l.total_creditos_usd,
        l.disponible_caja_ves,
        l.encaje_legal_bcv_ves,
        l.tasa_liquidez,
        l.brecha_liquidez_usd,
        m.tasa_bcv_usd_ves,
        m.tasa_paralela_usd_ves,
        m.inflacion_mensual_pct,
        m.variacion_pib_mensual_pct,
        m.tasa_activa_ves_anual,
        m.tasa_pasiva_ves_anual
    FROM resumen_liquidez_diario l
    JOIN indicadores_macro m ON l.fecha = m.fecha
    ORDER BY l.fecha ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df["fecha"] = pd.to_datetime(df["fecha"])
    
    # Feature Engineering
    # 1. Exchange rate spread
    df["brecha_cambiaria_pct"] = (df["tasa_paralela_usd_ves"] / df["tasa_bcv_usd_ves"] - 1.0) * 100.0
    
    # 2. Calendar and Seasonality Dummies
    df["dia_mes"] = df["fecha"].dt.day
    df["dia_semana"] = df["fecha"].dt.weekday
    df["mes"] = df["fecha"].dt.month
    df["es_quincena"] = df["dia_mes"].isin([15, 30]).astype(int)
    df["es_diciembre"] = (df["mes"] == 12).astype(int)
    
    # 3. Lags of key variables (t-1, t-7)
    df["lag_brecha_1"] = df["brecha_liquidez_usd"].shift(1)
    df["lag_brecha_7"] = df["brecha_liquidez_usd"].shift(7)
    df["lag_dep_ves_1"] = df["total_depositos_ves"].shift(1)
    df["lag_dep_ves_7"] = df["total_depositos_ves"].shift(7)
    df["lag_dep_usd_1"] = df["total_depositos_usd"].shift(1)
    df["lag_tasa_liq_1"] = df["tasa_liquidez"].shift(1)
    
    # 4. Rolling 7-day averages
    df["rolling_dep_ves_7"] = df["total_depositos_ves"].rolling(7).mean()
    df["rolling_brecha_7"] = df["brecha_liquidez_usd"].rolling(7).mean()
    
    # Drop rows with NaN from lags
    df = df.dropna().reset_index(drop=True)
    
    print(f"[OK] Loaded {len(df)} daily balance records (from {df['fecha'].min().strftime('%Y-%m-%d')} to {df['fecha'].max().strftime('%Y-%m-%d')})")
    return df

def train_liquidity_model():
    df = load_liquidity_data()
    
    features = [
        "dia_mes", "dia_semana", "mes", "es_quincena", "es_diciembre",
        "tasa_bcv_usd_ves", "brecha_cambiaria_pct", "inflacion_mensual_pct",
        "lag_brecha_1", "lag_brecha_7", "lag_dep_ves_1", "lag_dep_ves_7",
        "lag_dep_usd_1", "lag_tasa_liq_1", "rolling_dep_ves_7", "rolling_brecha_7"
    ]
    
    X = df[features]
    y = df["brecha_liquidez_usd"]
    
    # Time-Series Split (Sequential: last 90 days as test set)
    split_idx = len(df) - 90
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), features)]
    )
    
    regressor = HistGradientBoostingRegressor(
        max_iter=150,
        max_depth=5,
        learning_rate=0.08,
        random_state=42
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", regressor)
    ])
    
    print("\n[+] Training Daily Liquidity Gap Regressor...")
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print(" LIQUIDITY GAP FORECASTING MODEL EVALUATION")
    print("="*50)
    print(f"Test Horizon     : 90 Days out-of-sample")
    print(f"Mean Absolute Error (MAE) : ${mae:,.2f} USD")
    print(f"Root Mean Sq Error (RMSE) : ${rmse:,.2f} USD")
    print(f"R-squared (R2) Score      : {r2:.4f}")
    
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"[OK] Model artifact saved to: {MODEL_OUTPUT_PATH}")
    
    # Quick inference demonstration
    print("\n[+] Sample Next-Day Forecast Test:")
    latest_row = X_test.iloc[[-1]]
    pred_gap = pipeline.predict(latest_row)[0]
    actual_gap = y_test.iloc[-1]
    print(f"    Predicted Liquidity Gap : ${pred_gap:,.2f} USD")
    print(f"    Actual Liquidity Gap    : ${actual_gap:,.2f} USD")
    print(f"    Treasury Recommendation : {'FUNDING NEEDED (Deficit - Borrow Overnight)' if pred_gap < 0 else 'EXCESS LIQUIDITY (Invest / BCV Intervention)'}")

if __name__ == "__main__":
    train_liquidity_model()
