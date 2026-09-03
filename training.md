# RiskVision: Machine Learning Model Training & Deployment Guide
### Guía de Entrenamiento y Despliegue de Modelos de Machine Learning

This document provides a comprehensive guide in both **English** and **Spanish** on how to train, evaluate, and deploy the machine learning models required to answer the advanced questions in [`questions.md`](file:///c:/Repositorios/bank-data/questions.md).

Este documento proporciona una guía exhaustiva tanto en **inglés** como en **español** sobre cómo entrenar, evaluar y desplegar los modelos de machine learning requeridos para resolver las preguntas avanzadas de [`questions.md`](file:///c:/Repositorios/bank-data/questions.md).

---

## 1. Machine Learning Architecture Overview / Resumen de la Arquitectura de ML

The machine learning suite addresses the primary risk dimensions of modern retail and commercial banking within the Venezuelan economic context:

| Model / Modelo | Target Variable / Variable Objetivo | Type / Tipo | Script | Associated Question / Pregunta Asociada | Key Metric / Métrica Clave |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Credit Scoring (PD)** | `target_default` (0: Performing, 1: Default) | Binary Classification | [`models/train_credit_scoring.py`](file:///c:/Repositorios/bank-data/models/train_credit_scoring.py) | **Q4.1** (Credit Default Risk) | Gini Index, ROC-AUC, Brier Score |
| **Fraud Detection** | `es_fraude` (0: Legit, 1: Fraud) | Imbalanced Classification | [`models/train_fraud_detection.py`](file:///c:/Repositorios/bank-data/models/train_fraud_detection.py) | **Q4.2** (Transactional Anomaly) | PR-AUC (AUPRC), F1-Score, Recall |
| **Liquidity Forecasting**| `brecha_liquidez_usd` (Surplus / Deficit) | Time-Series Regression | [`models/train_liquidity_forecasting.py`](file:///c:/Repositorios/bank-data/models/train_liquidity_forecasting.py) | **Q4.3** (Liquidity Gap & Encaje) | MAE, RMSE, $R^2$ Score |
| **Customer Churn** | `target_churn` (0: Active, 1: Inactive) | Binary Classification | [`models/train_customer_churn.py`](file:///c:/Repositorios/bank-data/models/train_customer_churn.py) | **Q5.4 & Q1.1** (Retention Risk) | ROC-AUC, Recall |

---

## 2. Model 1: Credit Scoring & Probability of Default (PD)
### Modelo 1: Credit Scoring y Probabilidad de Incumplimiento (PD)

### English Version
* **Problem Formulation**: Predict the likelihood that a borrower will fail to repay their loan obligations (`estado` in `'Vencido'` or `'En Litigio'`).
* **Source Data**: Joined tables `creditos`, `clientes`, and `indicadores_macro` (context at loan origination).
* **Feature Engineering**:
  * **Debt-to-Income (DTI)**: `monto_aprobado_usd / (ingresos_mensuales_usd * plazo_meses)`
  * **Loan-to-Income**: `monto_aprobado_usd / ingresos_mensuales_usd`
  * **Macroeconomic Indexation**: Monthly inflation rate (`inflacion_origen`) and active lending market rate (`tasa_mercado_origen`) at the loan grant date.
* **Algorithm & Preprocessing**:
  * Numeric features standardized via `StandardScaler`.
  * Categorical features (`actividad_economica`, `nivel_riesgo_interno`, `tipo_credito`) encoded via `OneHotEncoder`.
  * Classifier: `RandomForestClassifier(class_weight='balanced')` to address default class imbalance (~10%).
* **Key Evaluation Metrics**:
  * **ROC-AUC & Gini Coefficient**: Standard regulatory credit benchmarks ($Gini = 2 \times AUC - 1$).
  * **Brier Score**: Measures probability calibration quality (lower is better).
* **Answering Question 4.1**:
  * The agent inputs the client's demographic profile (credit score 520, $250 USD income, Public Employee, $1,500 loan, 12 months) and calls `pipeline.predict_proba()`.
  * The model returns an estimated **PD of ~28%**, exceeding the standard risk threshold (15%), thus justifying an automated loan rejection.

### Versión en Español
* **Formulación del Problema**: Predecir la probabilidad de que un prestatario incumpla sus obligaciones de pago (`estado` en `'Vencido'` o `'En Litigio'`).
* **Datos Fuente**: Cruce de tablas `creditos`, `clientes` e `indicadores_macro` (contexto macroeconómico a la fecha de otorgamiento).
* **Ingeniería de Características**:
  * **Ratio Deuda-Ingreso (DTI)**: `monto_aprobado_usd / (ingresos_mensuales_usd * plazo_meses)`
  * **Ratio Préstamo-Ingreso**: `monto_aprobado_usd / ingresos_mensuales_usd`
  * **Indexación Macroeconómica**: Tasa de inflación mensual y tasa activa de mercado vigentes al momento del otorgamiento.
* **Algoritmo y Preprocesamiento**:
  * Estandarización numérica con `StandardScaler`.
  * Codificación de variables categóricas con `OneHotEncoder`.
  * Clasificador: `RandomForestClassifier` con ponderación balanceada (`class_weight='balanced'`) para corregir el desbalance natural de la mora (~10%).
* **Resolución de la Pregunta 4.1**:
  * El agente ingresa el perfil solicitado (score 520, ingreso de $250 USD, empleado público, crédito de $1,500 USD a 12 meses) y consulta `pipeline.predict_proba()`.
  * El modelo estima una **Probabilidad de Incumplimiento (PD) de ~28%**, superando el umbral de tolerancia (15%), recomendando rechazar la solicitud o requerir colateral adicional.

---

## 3. Model 2: Real-Time Transactional Fraud Detection
### Modelo 2: Detección de Fraude Transaccional en Tiempo Real

### English Version
* **Problem Formulation**: Identify fraudulent transaction events (`es_fraude = 1`) in real time among millions of legitimate transactions.
* **Source Data**: `transacciones` joined with `cuentas` and `clientes`.
* **Behavioral Anomaly Engineering**:
  * **Cyclical Time Encoding**: Transformation of transaction hour into sine and cosine components:
    $$\sin\left(\frac{2\pi \times \text{hour}}{24}\right), \quad \cos\left(\frac{2\pi \times \text{hour}}{24}\right)$$
    Captures night-time vulnerability (1:00 AM to 4:00 AM) without artificial numerical discontinuities at midnight.
  * **Amount-to-Income Ratio**: Compares transaction amount to the user's monthly earnings.
  * **Geographic Deviation**: Euclidean distance from customer registered home base (`desviacion_geo`).
* **Handling Class Imbalance**:
  * Fraud is rare (~0.18% of events). Evaluated using **PR-AUC (Precision-Recall Area Under Curve)** and **F1-Score** rather than raw accuracy.
* **Answering Question 4.2**:
  * When a $400 USD Pago Móvil occurs at 3:15 AM from an anomalous location, the model assigns a high anomaly risk score, triggering automated step-up authentication or payment blocking.

### Versión en Español
* **Formulación del Problema**: Identificar eventos de fraude transaccional (`es_fraude = 1`) en tiempo real entre millones de transacciones legítimas.
* **Datos Fuente**: `transacciones` cruzado con `cuentas` y `clientes`.
* **Ingeniería de Anomalías de Comportamiento**:
  * **Codificación Cíclica de Tiempo**: Transformación de la hora en componentes seno y coseno para capturar la actividad en madrugadas (1:00 AM a 4:00 AM) sin saltos artificiales entre las 23:00 y las 00:00.
  * **Ratio Monto sobre Ingreso**: Mide si la transacción representa una fracción desproporcionada del salario del cliente.
  * **Desviación Geográfica**: Distancia euclidiana respecto a las coordenadas habituales del cliente.
* **Resolución de la Pregunta 4.2**:
  * Ante una transacción de $400 USD en Pago Móvil a las 3:15 AM en una ubicación inusual, el modelo eleva el puntaje de riesgo de fraude, permitiendo al agente de IA explicar con claridad los factores determinantes de la alerta.

---

## 4. Model 3: Daily Liquidity Gap Forecasting
### Modelo 3: Pronóstico de Brecha de Liquidez Diaria

### English Version
* **Problem Formulation**: Forecast the net liquidity surplus/deficit in USD (`brecha_liquidez_usd`) to anticipate Central Bank legal reserve shortfalls (73% BCV encaje).
* **Source Data**: Daily time series from `resumen_liquidez_diario` joined with `indicadores_macro` (1,097 historical daily records).
* **Time-Series Feature Engineering**:
  * **Lags**: $t-1$, $t-7$, $t-14$ of liquidity gap, deposit totals, and liquidity ratios.
  * **Rolling Metrics**: 7-day rolling moving averages.
  * **Calendar Seasonalities**: Salary payroll dummy (`es_quincena` on 15th & 30th) and holiday spending dummy (`es_diciembre`).
  * **FX Market Exogenous Variable**: Percentage spread between parallel and official rates (`brecha_cambiaria_pct`).
* **Algorithm**: `HistGradientBoostingRegressor` evaluated on a sequential out-of-sample test horizon (last 90 days).
* **Answering Question 4.3**:
  * The model forecasts whether the bank will enter a liquidity deficit in the coming week, allowing the treasury desk to arrange overnight funding (`Colocacion Interbancaria`) proactively.

### Versión en Español
* **Formulación del Problema**: Pronosticar el excedente o déficit neto de liquidez en dólares (`brecha_liquidez_usd`) para anticipar insuficiencias de encaje legal (73% BCV).
* **Datos Fuente**: Serie temporal diaria de `resumen_liquidez_diario` combinada con `indicadores_macro`.
* **Ingeniería de Características Temporales**:
  * **Retardos (Lags)**: $t-1$, $t-7$, $t-14$ de la brecha de liquidez y saldos de depósitos.
  * **Medias Móviles**: Promedio móvil de 7 días.
  * **Estacionalidad de Calendario**: Banderas de quincena (días 15 y 30) y consumo navideño (mes de diciembre).
  * **Variable Exógena Cambiaria**: Porcentaje de la brecha entre el dólar paralelo y el oficial.
* **Resolución de la Pregunta 4.3**:
  * El agente proyecta la brecha diaria para los próximos 7 días y emite recomendaciones operativas de tesorería (solicitud de fondeo interbancario o colocación de excedentes).

---

## 5. Model 4: Customer Churn Risk Prediction
### Modelo 4: Predicción de Desafiliación de Clientes (Churn)

### English Version
* **Problem Formulation**: Predict whether a customer is at risk of disaffiliating from the bank (`estado_cliente = 'Inactivo'`).
* **Source Data**: `clientes` aggregated with multi-currency holdings from `cuentas` and loan history from `creditos`.
* **Feature Engineering**:
  * **Tenure**: Days since registration (`antiguedad_dias`).
  * **Engagement Indicators**: Total number of accounts, ownership of a USD custody account, total USD balance held, and active loan relationship.
* **Algorithm**: `RandomForestClassifier` with balanced class weights.
* **Answering Questions 1.1 & 5.4**:
  * Identifies high-risk customer segments (e.g. single-account clients with zero USD balances and declining activity) to trigger automated retention incentives.

### Versión en Español
* **Formulación del Problema**: Predecir si un cliente activo se encuentra en riesgo de desafiliarse del banco (`estado_cliente = 'Inactivo'`).
* **Datos Fuente**: Agregación de `clientes` con tenencia de cuentas en `cuentas` e historial de préstamos en `creditos`.
* **Ingeniería de Características**: Antigüedad en días, tenencia de cuenta en dólares, saldo total y relación crediticia activa.
* **Resolución de las Preguntas 1.1 y 5.4**:
  * Permite al agente perfilar a los clientes con mayor propensión de abandono y formular estrategias proactivas de fidelización y retención de depósitos.

---

## 6. How to Train and Run the Models / Cómo Entrenar y Ejecutar los Modelos

Each model is encapsulated in a standalone, production-ready Python script inside the [`models/`](file:///c:/Repositorios/bank-data/models) folder:

### Execution Commands / Comandos de Ejecución

```bash
# 1. Credit Scoring & Probability of Default (PD)
python models/train_credit_scoring.py

# 2. Real-Time Transactional Fraud Classifier
python models/train_fraud_detection.py

# 3. Daily Liquidity Gap Forecasting
python models/train_liquidity_forecasting.py

# 4. Customer Churn Risk Prediction
python models/train_customer_churn.py
```

*Note for embedded Python environments: You can also execute directly with:*
```bash
C:\python_embedded\python.exe models/train_credit_scoring.py
C:\python_embedded\python.exe models/train_fraud_detection.py
C:\python_embedded\python.exe models/train_liquidity_forecasting.py
C:\python_embedded\python.exe models/train_customer_churn.py
```

---

## 7. How an AI Agent Consumes the Trained Models / Cómo Consume un Agente de IA los Modelos

Once trained, each script exports a serialized scikit-learn pipeline (`.joblib`) into the `models/` directory:
- `models/credit_scoring_model.joblib`
- `models/fraud_detection_model.joblib`
- `models/liquidity_forecast_model.joblib`
- `models/churn_prediction_model.joblib`

### Python Integration Snippet for AI Agents / Código de Integración para Agentes:
```python
import joblib
import pandas as pd

# Load the trained model pipeline
model = joblib.load("models/credit_scoring_model.joblib")

# Score a new client loan request
new_applicant = pd.DataFrame([{
    "score_credito": 520,
    "ingresos_mensuales_usd": 250.0,
    "monto_aprobado_usd": 1500.0,
    "tasa_interes_anual": 36.5,
    "plazo_meses": 12,
    "inflacion_origen": 2.5,
    "tasa_mercado_origen": 38.0,
    "ratio_dti": 0.50,
    "ratio_prestamo_ingreso": 6.0,
    "actividad_economica": "Empleado Público",
    "nivel_riesgo_interno": "Medio",
    "tipo_credito": "Consumo",
    "genero": "M",
    "estado_civil": "Casado"
}])

# Calculate Probability of Default
probability_of_default = model.predict_proba(new_applicant)[0, 1]
print(f"Predicted PD: {probability_of_default:.2%}")
```
