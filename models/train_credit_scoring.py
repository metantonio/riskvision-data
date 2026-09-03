"""
RiskVision: Credit Scoring & Probability of Default (PD) Model Training
Entrenamiento del Modelo de Credit Scoring y Probabilidad de Incumplimiento (PD)

Objective / Objetivo:
Train a supervised binary classification model to predict the Probability of Default (PD)
for a loan applicant based on demographic, financial, and macroeconomic features.
Entrenar un modelo de clasificación binaria supervisada para predecir la Probabilidad de Incumplimiento (PD)
de un solicitante de crédito con base en variables demográficas, financieras y de contexto macroeconómico.

Related Question / Pregunta Asociada:
Level 4, Question 4.1 in questions.md
"""

import sqlite3
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report, brier_score_loss

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bank_data.db"))
MODEL_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "credit_scoring_model.joblib"))

def load_data(db_path=DB_PATH):
    print(f"[+] Loading credit risk dataset from: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # Query joining creditos, clientes, and historical macroeconomic context at origination
    query = """
    SELECT 
        cr.id AS credito_id,
        cl.score_credito,
        cl.ingresos_mensuales_usd,
        cl.actividad_economica,
        cl.nivel_riesgo_interno,
        cl.genero,
        cl.estado_civil,
        cr.monto_aprobado_usd,
        cr.tasa_interes_anual,
        cr.plazo_meses,
        cr.tipo_credito,
        cr.estado,
        m.inflacion_mensual_pct AS inflacion_origen,
        m.tasa_activa_ves_anual AS tasa_mercado_origen,
        -- Feature Engineering: Debt-to-Income (DTI) & Loan-to-Income ratios
        ROUND(cr.monto_aprobado_usd / (cl.ingresos_mensuales_usd * cr.plazo_meses), 4) AS ratio_dti,
        ROUND(cr.monto_aprobado_usd / cl.ingresos_mensuales_usd, 2) AS ratio_prestamo_ingreso
    FROM creditos cr
    JOIN clientes cl ON cr.cliente_id = cl.id
    LEFT JOIN indicadores_macro m ON cr.fecha_otorgamiento = m.fecha
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Define Target: 1 if Default (Vencido, En Litigio), 0 if Performing/Paid (Vigente, Pagado)
    df["target_default"] = df["estado"].apply(lambda x: 1 if x in ["Vencido", "En Litigio"] else 0)
    
    print(f"[OK] Loaded {len(df)} loan records.")
    print(f"    - Defaulted loans: {df['target_default'].sum()} ({df['target_default'].mean()*100:.2f}%)")
    print(f"    - Performing loans: {(df['target_default'] == 0).sum()} ({(1-df['target_default'].mean())*100:.2f}%)")
    return df

def train_credit_model():
    df = load_data()
    
    feature_numeric = [
        "score_credito", "ingresos_mensuales_usd", "monto_aprobado_usd",
        "tasa_interes_anual", "plazo_meses", "inflacion_origen",
        "tasa_mercado_origen", "ratio_dti", "ratio_prestamo_ingreso"
    ]
    feature_categorical = [
        "actividad_economica", "nivel_riesgo_interno", "tipo_credito",
        "genero", "estado_civil"
    ]
    
    X = df[feature_numeric + feature_categorical]
    y = df["target_default"]
    
    # Train / Test split (Stratified by default class)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    # Preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feature_numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), feature_categorical)
        ]
    )
    
    # Classifier with balanced weighting to handle default imbalance
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        class_weight="balanced",
        random_state=42
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])
    
    print("\n[+] Training Credit Scoring / PD Model...")
    pipeline.fit(X_train, y_train)
    
    # Predictions & Probabilities
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    # Metrics
    auc = roc_auc_score(y_test, y_prob)
    gini = 2 * auc - 1
    brier = brier_score_loss(y_test, y_prob)
    
    print("\n" + "="*50)
    print(" CREDIT SCORING (PD) MODEL EVALUATION")
    print("="*50)
    print(f"ROC-AUC Score : {auc:.4f}")
    print(f"Gini Index    : {gini:.4f} (Standard credit benchmark > 0.40)")
    print(f"Brier Score   : {brier:.4f} (Calibration score, lower is better)")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["Performing", "Default"]))
    
    # Save trained pipeline
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"[OK] Model artifact saved to: {MODEL_OUTPUT_PATH}")
    
    # Quick inference demonstration
    print("\n[+] Sample Prediction Test (Question 4.1 Profile):")
    sample_client = pd.DataFrame([{
        "score_credito": 520,
        "ingresos_mensuales_usd": 250.0,
        "monto_aprobado_usd": 1500.0,
        "tasa_interes_anual": 36.5,
        "plazo_meses": 12,
        "inflacion_origen": 2.5,
        "tasa_mercado_origen": 38.0,
        "ratio_dti": round(1500.0 / (250.0 * 12), 4),
        "ratio_prestamo_ingreso": round(1500.0 / 250.0, 2),
        "actividad_economica": "Empleado Público",
        "nivel_riesgo_interno": "Medio",
        "tipo_credito": "Consumo",
        "genero": "M",
        "estado_civil": "Casado"
    }])
    
    pred_pd = pipeline.predict_proba(sample_client)[0, 1]
    print(f"    Estimated Probability of Default (PD): {pred_pd*100:.2f}%")
    print(f"    Loan Recommendation: {'REJECT (High Default Risk)' if pred_pd > 0.15 else 'APPROVE'}")

if __name__ == "__main__":
    train_credit_model()
