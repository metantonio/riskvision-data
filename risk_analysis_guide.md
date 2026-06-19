# RiskVision: Risk Analysis & Machine Learning Modeling Guide
### Guía de Análisis de Riesgos y Modelado de Machine Learning

---

## Table of Contents / Tabla de Contenido
1.  [English Version: Risk Interpretation & ML Models](#english-version)
2.  [Versión en Español: Interpretación de Riesgos y Modelos de ML](#versión-en-español)

---

# ENGLISH VERSION

This guide provides a structured framework for data analysts and data scientists to interpret the generated banking data and design machine learning models for **Credit Risk (PD)**, **Operational Risk (Fraud & Outages)**, and **Liquidity/Market Risk** within the Venezuelan economic context.

---

## 1. Credit Risk Interpretation & Modeling (PD)

### How an Analyst Interprets the Data
*   **The Inflation-Default Link**: In Venezuela, high monthly inflation (INPC) erodes the real income of consumers. When inflation spikes, the default rate on retail loans (Consumo/Microcrédito) rises because the cost of living increases faster than wages. An analyst should compute the correlation between `indicadores_macro.inflacion_mensual_pct` and `pagos_creditos.dias_atraso`.
*   **Credit Score Skewness**: While the demographic `score_credito` is normally distributed around 620, the default rate is highly non-linear. Default events (`estado` in 'Vencido', 'En Litigio') are heavily clustered below 550.
*   **Economic Activity Vulnerability**: Employees in the public sector have stable nominal incomes but very low real value due to inflation, while informal merchants (`Independiente/Profesional` or `Empresario`) have volatile income in VES but higher overall USD-equivalent income. An analyst will observe that default volatility is higher in informal sectors during low-GDP months.

### Proposed Machine Learning Models

#### Model A: Credit Scoring (Probability of Default - PD)
*   **Type**: Supervised Binary Classification.
*   **Algorithm**: **XGBoost Classifier** or **LightGBM** (to capture non-linear relationships and interactions), or **Regularized Logistic Regression** (for financial interpretability).
*   **Target Variable**: `target_default` (1 if `creditos.estado` is 'Vencido' or 'En Litigio'; 0 if 'Pagado' or 'Vigente').
*   **Key Features**:
    *   `score_credito` (numeric)
    *   `ingresos_mensuales_usd` (numeric)
    *   `actividad_economica` (categorical -> one-hot encoded)
    *   `nivel_riesgo_interno` (ordinal)
    *   **Debt-to-Income Ratio**: `monto_aprobado_usd / (ingresos_mensuales_usd * plazo_meses)` (engineered numeric feature)
    *   **Macroeconomic Context**: Inflation rate and GDP growth at the loan's start date.
*   **Evaluation Metrics**: ROC-AUC, Gini Coefficient (standard in credit scoring, $Gini = 2 \times AUC - 1$), Precision-Recall Curve (since defaults are typically imbalanced, around 5-10%).

---

## 2. Operational Risk Interpretation & Modeling

### How an Analyst Interprets the Data
*   **System Outages (Outage Cost)**: On specific dates, transaction failure rates (`estado = 'Fallida'`) spike up to 40% due to `ERR_TIMEOUT` or `ERR_CONEXION_HOST`. An analyst can quantify the cost of an outage by summing the average fees/commissions lost from rejected transaction volumes during these hours.
*   **Fraud Behavioral Anomaly**: Fraudulent transactions (`es_fraude = 1`) display clear behavioral anomalies compared to legitimate transactions: they occur primarily between 1:00 AM and 5:00 AM (when normal users are asleep), the amounts are significantly higher than the user's historical average, and they are concentrated in the `Pago Movil` channel.

### Proposed Machine Learning Models

#### Model B: Real-time Transactional Fraud Classifier
*   **Type**: Supervised Classification (with heavy class imbalance, ~0.15% positive class).
*   **Algorithm**: **Random Forest Classifier** (robust to noise), **XGBoost** (with `scale_pos_weight` parameter tuned for imbalance), or **Isolation Forest / One-Class SVM** (unsupervised anomaly detection if labels are unknown).
*   **Key Features**:
    *   **Temporal Features**: Sine/Cosine transformation of the transaction hour (to capture the cyclical 24-hour patterns).
    *   **Amount Ratio**: `monto_usd / cliente.ingresos_mensuales_usd` (compares transaction size to user's monthly income).
    *   **Geographic Velocity**: Deviation of `latitud` and `longitud` from the client's registered state coordinates.
    *   `canal` (categorical).
*   **Evaluation Metrics**: F1-Score, PR-AUC (AUPRC), Recall (critical to minimize False Negatives / missed fraud).

---

## 3. Liquidity and Market Risk Interpretation & Modeling

### How an Analyst Interprets the Data
*   **The Encaje Legal Trap**: A 73% legal reserve requirement means that for every 100 Bolívares deposited, 73 Bs. must be frozen at the Central Bank of Venezuela (BCV). This severely restricts bank liquidity. An analyst will observe that whenever deposits in VES decrease, the bank immediately falls into a liquidity deficit, forcing it to borrow overnight interbank funds (*Colocación Interbancaria*) at high rates to avoid BCV penalties.
*   **Cambiario (FX) Risk**: When the gap between the parallel rate and the official BCV rate widens, customers accelerate their withdrawals of VES to buy USD in the parallel market. This causes a liquidity run. An analyst must monitor the *exchange rate spread* (`tasa_paralela_usd_ves / tasa_bcv_usd_ves - 1`).

### Proposed Machine Learning Models

#### Model C: Daily Liquidity Gap Forecast
*   **Type**: Time-Series Regression / Forecasting.
*   **Algorithm**: **Prophet** (excellent for quincena and December holiday seasonalities), **SARIMAX** (incorporating exchange rate spread as an exogenous variable), or **LSTM** (for deep sequential modeling).
*   **Target Variable**: `brecha_liquidez_usd` (daily liquid surplus/deficit).
*   **Key Features**:
    *   Lagged values of `total_depositos_ves` and `total_depositos_usd` (t-1, t-7, t-30).
    *   Exchange rate spread (Parallel / BCV - 1).
    *   Bi-weekly salary day flag (15th and 30th).
    *   Month flag (December dummy).
*   **Evaluation Metrics**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE).

---

## 4. Example ML Training Pipeline (Python)

Below is a complete script to train and evaluate a **Credit Scoring Model** using the simulated SQLite database:

```python
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# 1. Load data from SQLite
conn = sqlite3.connect("bank_data.db")
query = """
    SELECT 
        c.score_credito,
        c.ingresos_mensuales_usd,
        c.actividad_economica,
        c.nivel_riesgo_interno,
        cr.monto_aprobado_usd,
        cr.tasa_interes_anual,
        cr.plazo_meses,
        cr.tipo_credito,
        CASE WHEN cr.estado IN ('Vencido', 'En Litigio') THEN 1 ELSE 0 END as target_default
    FROM creditos cr
    JOIN clientes c ON cr.cliente_id = c.id
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 2. Feature Engineering: Debt-to-Income Ratio
df['ratio_cuota_ingreso'] = (df['monto_aprobado_usd'] / df['plazo_meses']) / (df['ingresos_mensuales_usd'] + 1)

# 3. Define features and target
X = df.drop(columns=['target_default'])
y = df['target_default']

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 5. Preprocessing Pipeline
numeric_features = ['score_credito', 'ingresos_mensuales_usd', 'monto_aprobado_usd', 'tasa_interes_anual', 'plazo_meses', 'ratio_cuota_ingreso']
categorical_features = ['actividad_economica', 'nivel_riesgo_interno', 'tipo_credito']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# 6. Model Pipeline
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
])

# 7. Train Model
model_pipeline.fit(X_train, y_train)

# 8. Evaluate Model
y_pred = model_pipeline.predict(X_test)
y_pred_proba = model_pipeline.predict_proba(X_test)[:, 1]

print("=== Model Performance ===")
print(classification_report(y_test, y_pred))
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
```

---
---

# VERSIÓN EN ESPAÑOL

Esta guía proporciona un marco estructurado para que los analistas y científicos de datos interpreten los datos bancarios generados y diseñen modelos de aprendizaje automático para **Riesgo de Crédito (PD)**, **Riesgo Operativo (Fraude y Caídas)** y **Riesgo de Liquidez y Mercado** adaptados a la realidad económica venezolana.

---

## 1. Interpretación y Modelado de Riesgo de Crédito (PD)

### Cómo un Analista Interpreta los Datos
*   **Vínculo Inflación-Default**: En Venezuela, una inflación mensual elevada (INPC) erosiona el poder adquisitivo real de los consumidores. Cuando la inflación se dispara, la tasa de morosidad de los créditos de consumo/microcréditos aumenta porque el costo de la vida sube más rápido que los salarios. El analista debe calcular la correlación entre `indicadores_macro.inflacion_mensual_pct` y `pagos_creditos.dias_atraso`.
*   **Comportamiento No Lineal del Score**: Aunque el `score_credito` se distribuye normalmente alrededor de 620, los defaults ocurren de forma altamente concentrada y no lineal por debajo de los 550 puntos de score.
*   **Vulnerabilidad por Sector Laboral**: Los empleados públicos tienen ingresos fijos que pierden valor real muy rápido, mientras que los comerciantes informales (`Empresario` o `Independiente`) perciben ingresos variables pero más dolarizados. La morosidad en estos sectores informales fluctúa fuertemente en meses de contracción económica (PIB negativo).

### Modelos de Machine Learning Sugeridos

#### Modelo A: Scoring Crediticio (Probabilidad de Default - PD)
*   **Tipo**: Clasificación Binaria Supervisada.
*   **Algoritmo**: **XGBoost Classifier** o **LightGBM** (para capturar interacciones complejas no lineales), o **Regresión Logística Regularizada** (si se requiere alta explicabilidad regulatoria).
*   **Variable Objetivo**: `target_default` (1 si `creditos.estado` es 'Vencido' o 'En Litigio'; 0 si es 'Pagado' o 'Vigente').
*   **Características Clave (Features)**:
    *   `score_credito` (numérico)
    *   `ingresos_mensuales_usd` (numérico)
    *   `actividad_economica` (categórico -> codificado)
    *   `nivel_riesgo_interno` (ordinal)
    *   **Ratio de Endeudamiento**: `(monto_aprobado_usd / plazo_meses) / ingresos_mensuales_usd` (relación cuota-ingreso).
    *   **Variables Macro**: Inflación y variación del PIB vigentes en la fecha de otorgamiento.
*   **Métricas de Evaluación**: ROC-AUC, Coeficiente de Gini ($Gini = 2 \times AUC - 1$) y Curva Precision-Recall (por el desbalance de defaults).

---

## 2. Interpretación y Modelado de Riesgo Operativo

### Cómo un Analista Interpreta los Datos
*   **Costo de Caídas de Sistema (Outages)**: En fechas específicas del dataset, las transacciones fallidas (`estado = 'Fallida'`) se elevan hasta un 40% debido a fallas operativas de core bancario o red (`ERR_TIMEOUT` y `ERR_CONEXION_HOST`). Un analista puede calcular el impacto financiero sumando las comisiones promedio que el banco dejó de percibir por las transacciones rechazadas.
*   **Anomalía Conductual del Fraude**: Las transacciones fraudulentas (`es_fraude = 1`) muestran un patrón conductual claro: ocurren mayoritariamente de madrugada (1:00 AM a 5:00 AM), con montos significativamente más altos que la media del cliente y concentradas en el canal digital instantáneo `Pago Movil`.

### Modelos de Machine Learning Sugeridos

#### Modelo B: Clasificador de Fraude Transaccional en Tiempo Real
*   **Tipo**: Clasificación Supervisada con alto desbalance de clases (~0.15% de casos positivos).
*   **Algoritmo**: **Random Forest** (resistente al ruido), **XGBoost** (ajustando el peso de clases con `scale_pos_weight`), o algoritmos de detección de anomalías no supervisados como **Isolation Forest** si no se tienen etiquetas históricas.
*   **Características Clave (Features)**:
    *   **Variables Temporales**: Transformación seno/coseno de la hora de la transacción para modelar el ciclo diario.
    *   **Ratio de Monto**: `monto_usd / cliente.ingresos_mensuales_usd` (tamaño de la transacción en relación con sus ingresos).
    *   **Desviación Geográfica**: Distancia entre las coordenadas de la transacción (`latitud`, `longitud`) y el estado de residencia del cliente.
    *   `canal` de la transacción.
*   **Métricas de Evaluación**: F1-Score, PR-AUC (AUPRC), y Recall (maximizar la captura de fraudes evitando falsos negativos).

---

## 3. Interpretación y Modelado de Riesgo de Liquidez y Mercado

### Cómo un Analista Interpreta los Datos
*   **La Restricción del Encaje Legal**: El encaje legal del **73%** sobre captaciones en Bolívares (VES) bloquea la mayor parte de los fondos del banco en el BCV. Si los depósitos de clientes disminuyen, el banco cae inmediatamente en un déficit de liquidez, viéndose obligado a pedir fondos interbancarios interdiarios (*Colocación Interbancaria*) a tasas muy elevadas.
*   **Riesgo Tipo de Cambio (FX)**: Cuando la brecha cambiaria (diferencia entre tasa paralela y BCV) se ensancha, los clientes retiran rápidamente sus Bolívares para cambiarlos a Dólares en el mercado paralelo, provocando salidas netas de capital y brechas de liquidez negativas.

### Modelos de Machine Learning Sugeridos

#### Modelo C: Pronóstico de Brecha de Liquidez Diaria
*   **Tipo**: Regresión de Series de Tiempo.
*   **Algoritmo**: **Prophet** (ideal para captar la estacionalidad del ciclo quincenal y navideño), **SARIMAX** (incluyendo la brecha cambiaria como variable exógena), o redes **LSTM** para modelar secuencias.
*   **Variable Objetivo**: `brecha_liquidez_usd` (superávit o déficit neto del día).
*   **Características Clave (Features)**:
    *   Valores rezagados (lags) de depósitos y caja (t-1, t-7, t-30).
    *   Brecha cambiaria diaria (`tasa_paralela_usd_ves / tasa_bcv_usd_ves - 1`).
    *   Banderas estacionales: Día de quincena (15/30) y mes de diciembre.
*   **Métricas de Evaluación**: MAE, RMSE.

---

## 4. Pipeline de Entrenamiento en Python (Scikit-Learn)

El siguiente script carga los datos de SQLite y entrena un clasificador básico para predecir la probabilidad de default de un cliente:

```python
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# 1. Cargar datos de la BD SQLite
conn = sqlite3.connect("bank_data.db")
query = """
    SELECT 
        c.score_credito,
        c.ingresos_mensuales_usd,
        c.actividad_economica,
        c.nivel_riesgo_interno,
        cr.monto_aprobado_usd,
        cr.tasa_interes_anual,
        cr.plazo_meses,
        cr.tipo_credito,
        CASE WHEN cr.estado IN ('Vencido', 'En Litigio') THEN 1 ELSE 0 END as target_default
    FROM creditos cr
    JOIN clientes c ON cr.cliente_id = c.id
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 2. Ingeniería de variables: Relación Cuota/Ingreso
df['ratio_cuota_ingreso'] = (df['monto_aprobado_usd'] / df['plazo_meses']) / (df['ingresos_mensuales_usd'] + 1)

# 3. Separar features y etiqueta
X = df.drop(columns=['target_default'])
y = df['target_default']

# 4. Partición de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 5. Preprocesamiento de columnas
numeric_features = ['score_credito', 'ingresos_mensuales_usd', 'monto_aprobado_usd', 'tasa_interes_anual', 'plazo_meses', 'ratio_cuota_ingreso']
categorical_features = ['actividad_economica', 'nivel_riesgo_interno', 'tipo_credito']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# 6. Pipeline del modelo
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
])

# 7. Entrenar el modelo
model_pipeline.fit(X_train, y_train)

# 8. Evaluar el modelo
y_pred = model_pipeline.predict(X_test)
y_pred_proba = model_pipeline.predict_proba(X_test)[:, 1]

print("=== Rendimiento del Modelo ===")
print(classification_report(y_test, y_pred))
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
```
