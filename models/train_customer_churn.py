"""
RiskVision: Customer Churn Risk Model Training
Entrenamiento del Modelo de Predicción de Desafiliación de Clientes (Churn)

Objective / Objetivo:
Train a classification model to predict the probability of a client leaving the bank (estado_cliente = 'Inactivo')
based on demographic profile, income level, credit score, tenure, and account holdings.
Entrenar un modelo de clasificación para predecir la probabilidad de que un cliente abandone el banco (estado_cliente = 'Inactivo')
con base en su perfil demográfico, nivel de ingresos, score crediticio, antigüedad y cuentas asociadas.

Related Question / Pregunta Asociada:
Level 5, Question 5.4 & Level 1, Question 1.1 in questions.md
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
from sklearn.metrics import roc_auc_score, classification_report, f1_score

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bank_data.db"))
MODEL_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "churn_prediction_model.joblib"))

def load_churn_data(db_path=DB_PATH):
    print(f"[+] Loading customer profile and account relationship data from: {db_path}")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        cl.id AS cliente_id,
        cl.genero,
        cl.estado_civil,
        cl.estado_residencia,
        cl.score_credito,
        cl.ingresos_mensuales_usd,
        cl.actividad_economica,
        cl.nivel_riesgo_interno,
        cl.fecha_nacimiento,
        cl.fecha_registro,
        cl.estado_cliente,
        -- Account metrics per client
        COUNT(cu.id) AS total_cuentas,
        SUM(CASE WHEN cu.moneda = 'USD' THEN 1 ELSE 0 END) AS tiene_cuenta_usd,
        COALESCE(SUM(CASE WHEN cu.moneda = 'USD' THEN cu.saldo_actual ELSE 0 END), 0) AS saldo_total_usd,
        -- Loan relationship
        COALESCE(cr.tiene_credito, 0) AS tiene_credito
    FROM clientes cl
    LEFT JOIN cuentas cu ON cl.id = cu.cliente_id
    LEFT JOIN (
        SELECT cliente_id, 1 AS tiene_credito 
        FROM creditos 
        GROUP BY cliente_id
    ) cr ON cl.id = cr.cliente_id
    GROUP BY cl.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Feature Engineering
    ref_date = pd.to_datetime("2026-06-19")
    df["edad"] = (ref_date - pd.to_datetime(df["fecha_nacimiento"])).dt.days // 365
    df["antiguedad_dias"] = (ref_date - pd.to_datetime(df["fecha_registro"])).dt.days
    
    # Target: 1 if Inactive, 0 if Active
    df["target_churn"] = df["estado_cliente"].apply(lambda x: 1 if x == "Inactivo" else 0)
    
    print(f"[OK] Loaded {len(df):,} customer profile records.")
    print(f"    - Churned (Inactivo) : {df['target_churn'].sum()} ({df['target_churn'].mean()*100:.2f}%)")
    print(f"    - Retained (Activo)  : {(df['target_churn'] == 0).sum()} ({(1-df['target_churn'].mean())*100:.2f}%)")
    return df

def train_churn_model():
    df = load_churn_data()
    
    feature_numeric = [
        "edad", "antiguedad_dias", "score_credito", "ingresos_mensuales_usd",
        "total_cuentas", "tiene_cuenta_usd", "saldo_total_usd", "tiene_credito"
    ]
    feature_categorical = [
        "genero", "estado_civil", "estado_residencia", "actividad_economica", "nivel_riesgo_interno"
    ]
    
    X = df[feature_numeric + feature_categorical]
    y = df["target_churn"]
    
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
        max_depth=6,
        class_weight="balanced",
        random_state=42
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])
    
    print("\n[+] Training Customer Churn Prediction Model...")
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print(" CUSTOMER CHURN MODEL EVALUATION")
    print("="*50)
    print(f"ROC-AUC Score : {auc:.4f}")
    print(f"F1-Score      : {f1:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["Retained", "Churned"]))
    
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"[OK] Model artifact saved to: {MODEL_OUTPUT_PATH}")
    
    # Quick inference demonstration
    print("\n[+] Sample Prediction Test (At-Risk Customer):")
    sample_client = pd.DataFrame([{
        "edad": 34,
        "antiguedad_dias": 850,
        "score_credito": 480,
        "ingresos_mensuales_usd": 150.0,
        "total_cuentas": 1,
        "tiene_cuenta_usd": 0,
        "saldo_total_usd": 0.0,
        "tiene_credito": 0,
        "genero": "M",
        "estado_civil": "Soltero",
        "estado_residencia": "Zulia",
        "actividad_economica": "Desempleado",
        "nivel_riesgo_interno": "Alto"
    }])
    
    churn_prob = pipeline.predict_proba(sample_client)[0, 1]
    print(f"    Estimated Churn Probability : {churn_prob*100:.2f}%")
    print(f"    Retention Strategy          : {'TRIGGER RETENTION INCENTIVE' if churn_prob > 0.35 else 'LOW RISK'}")

if __name__ == "__main__":
    train_churn_model()
