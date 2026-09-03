"""
RiskVision: Real-Time Transactional Fraud Detection Model Training
Entrenamiento del Modelo de Detección de Fraude Transaccional en Tiempo Real

Objective / Objetivo:
Train a machine learning classifier to detect fraudulent transaction events in real time.
Captures behavioral anomalies: unusual night hours, excessive amount relative to income,
abnormal channels, and geographic location deviations.
Entrenar un clasificador de machine learning para detectar eventos de fraude transaccional en tiempo real.
Captura anomalías de comportamiento: horarios nocturnos inusuales, montos desproporcionados al ingreso,
canales de alto riesgo y saltos geográficos anómalos.

Related Question / Pregunta Asociada:
Level 4, Question 4.2 in questions.md
"""

import sqlite3
import os
import math
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, classification_report, roc_auc_score, f1_score

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bank_data.db"))
MODEL_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "fraud_detection_model.joblib"))

def load_fraud_data(db_path=DB_PATH, sample_legit=150000):
    print(f"[+] Loading transaction records from: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # Load ALL fraudulent transactions + a stratified random sample of legitimate transactions
    # to train efficiently and maintain representative class imbalance (~0.2% fraud)
    query_fraud = """
    SELECT 
        t.id, t.monto, t.monto_usd, t.tipo_transaccion, t.canal, t.fecha_hora,
        t.latitud, t.longitud, t.es_fraude,
        cl.ingresos_mensuales_usd, cl.score_credito, cl.actividad_economica
    FROM transacciones t
    JOIN cuentas cu ON t.cuenta_id = cu.id
    JOIN clientes cl ON cu.cliente_id = cl.id
    WHERE t.es_fraude = 1
    """
    df_fraud = pd.read_sql_query(query_fraud, conn)
    
    query_legit = f"""
    SELECT 
        t.id, t.monto, t.monto_usd, t.tipo_transaccion, t.canal, t.fecha_hora,
        t.latitud, t.longitud, t.es_fraude,
        cl.ingresos_mensuales_usd, cl.score_credito, cl.actividad_economica
    FROM transacciones t
    JOIN cuentas cu ON t.cuenta_id = cu.id
    JOIN clientes cl ON cu.cliente_id = cl.id
    WHERE t.es_fraude = 0 AND t.estado = 'Completada'
    ORDER BY RANDOM()
    LIMIT {sample_legit}
    """
    df_legit = pd.read_sql_query(query_legit, conn)
    conn.close()
    
    df = pd.concat([df_fraud, df_legit], ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    # Feature Engineering
    # 1. Cyclical time features (hour of day: sin & cos)
    df["hora"] = pd.to_datetime(df["fecha_hora"]).dt.hour
    df["sin_hora"] = np.sin(2 * np.pi * df["hora"] / 24.0)
    df["cos_hora"] = np.cos(2 * np.pi * df["hora"] / 24.0)
    
    # 2. Amount to Income Ratio
    df["ratio_monto_ingreso"] = np.round(df["monto_usd"] / np.maximum(df["ingresos_mensuales_usd"], 10.0), 4)
    
    # 3. Geographic deviation from reference center (Caracas base: 10.4806, -66.9036)
    base_lat, base_lon = 10.4806, -66.9036
    df["desviacion_geo"] = np.sqrt((df["latitud"] - base_lat)**2 + (df["longitud"] - base_lon)**2)
    
    print(f"[OK] Loaded dataset for training: {len(df):,} transactions")
    print(f"    - Fraudulent events : {len(df_fraud):,} ({len(df_fraud)/len(df)*100:.3f}%)")
    print(f"    - Legitimate events : {len(df_legit):,}")
    return df

def train_fraud_model():
    df = load_fraud_data()
    
    feature_numeric = [
        "monto_usd", "ratio_monto_ingreso", "sin_hora", "cos_hora",
        "desviacion_geo", "score_credito"
    ]
    feature_categorical = ["canal", "tipo_transaccion", "actividad_economica"]
    
    X = df[feature_numeric + feature_categorical]
    y = df["es_fraude"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feature_numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), feature_categorical)
        ]
    )
    
    classifier = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])
    
    print("\n[+] Training Real-Time Fraud Classifier...")
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    pr_auc = average_precision_score(y_test, y_prob)
    roc_auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print(" TRANSACTIONAL FRAUD MODEL EVALUATION")
    print("="*50)
    print(f"PR-AUC Score  : {pr_auc:.4f} (Crucial for heavily imbalanced fraud detection)")
    print(f"ROC-AUC Score : {roc_auc:.4f}")
    print(f"F1-Score      : {f1:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))
    
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"[OK] Model artifact saved to: {MODEL_OUTPUT_PATH}")
    
    # Quick inference demonstration (Question 4.2 profile)
    print("\n[+] Sample Prediction Test (Question 4.2 Profile):")
    sample_tx = pd.DataFrame([{
        "monto_usd": 400.0,
        "ratio_monto_ingreso": round(400.0 / 300.0, 4), # $400 on $300 salary
        "sin_hora": math.sin(2 * math.pi * 3 / 24.0), # 3:15 AM
        "cos_hora": math.cos(2 * math.pi * 3 / 24.0),
        "desviacion_geo": 4.5, # Abnormal jump to far region
        "score_credito": 610,
        "canal": "Pago Movil",
        "tipo_transaccion": "Pago Movil",
        "actividad_economica": "Empleado Privado"
    }])
    
    fraud_prob = pipeline.predict_proba(sample_tx)[0, 1]
    print(f"    Transaction Amount     : $400.00 USD at 03:15 AM (Pago Movil)")
    print(f"    Assigned Fraud Risk    : {fraud_prob*100:.2f}%")
    print(f"    Automated Action       : {'FLAG AS FRAUD / BLOCK' if fraud_prob > 0.50 else 'ALLOW'}")

if __name__ == "__main__":
    train_fraud_model()
