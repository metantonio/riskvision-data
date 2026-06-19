# RiskVision - Venezuelan Bank Data & Risk Visualizer
### Visualizador de Riesgos y Generador de Datos Bancarios (Venezuela)

---

## Language Selection / Selección de Idioma
*   [English Version (English)](#english-version)
*   [Versión en Español (Spanish)](#versión-en-español)

---

# ENGLISH VERSION

RiskVision is a synthetic data environment and interactive visualizer designed for data scientists and risk analysts. It simulates 3 years of daily operations for a commercial bank in Venezuela (10,000 clients, ~3 million transactions) to build and train machine learning models for Credit, Operational, and Liquidity Risk.

---

## 1. How to Initialize the Database

The database is built on a portable **SQLite** file (`bank_data.db`) and also exports a **PostgreSQL** compatible script (`database/backup_postgres.sql`).

To initialize or regenerate the database, run:
```bash
python database/db_generator.py
```
*Note: The generator uses Python's standard libraries (`sqlite3`, `random`, `math`, `datetime`, `os`, `sys`) and does not require third-party dependencies.*

---

## 2. Installation & Running the Visualizer

The visualizer is built using **FastAPI** (Python) and a premium responsive dark-mode HTML5/CSS3 frontend.

### Prerequisites (Python Environment)
Install the dependencies listed in `requirements.txt`:
```bash
python -m pip install -r requirements.txt
```

### Starting the Web App
1.  **Fast Launch (Windows)**: Double-click on `run.bat` and select `1` to run the visualizer. It will start the FastAPI server and open `http://127.0.0.1:8000` in your browser.
2.  **Manual Launch**:
    ```bash
    python -m uvicorn visualizer.app:app --host 127.0.0.1 --port 8000 --reload
    ```

---

## 3. Understanding the Venezuelan Economic Context

To build realistic risk models, the simulation incorporates the unique macroeconomic reality of Venezuela between **June 2023 and June 2026**:

*   **Multicurrency System (USD/VES)**: Although the national currency is the Bolívar (VES), the economy is highly dollarized. Customers maintain savings/checking accounts in Bolívares and custody accounts in USD (Convenio Cambiario N° 1).
*   **Dual Exchange Rates**: Coexistence of the official exchange rate set daily by the Central Bank of Venezuela (BCV) and the parallel market rate (Monitor/DólarToday). The spread between both rates represents a major market and FX risk for the bank.
*   **Hyper-restrictive Legal Reserve (Encaje Legal)**: The BCV requires banks to freeze a massive percentage of their VES deposits—historically set around **73%** during the 2023-2026 period. This leaves banks with very little liquidity in Bolívares to lend, making credit scarce and credit risk highly critical.
*   **Payment Cycles & Seasonality**: Transaction volume spikes significantly on the 15th and 30th of each month (bi-weekly salary payments, "quincenas") and explodes up to 3x in December due to year-end bonuses ("aguinaldos") and Christmas shopping.

---

## 4. Guide to Dashboard Indicators

### Tab 1: Consolidated Overview (Resumen General)
*   **Total Clients & Churn Rate**: Shows active customer count and churn rate (inactives/lost clients), essential for modeling customer retention.
*   **Deposits by Currency (USD vs VES)**: Represents the bank's dollarization index, showing the ratio of VES liabilities to USD assets.
*   **Approved Portfolio**: Total approved credits.
*   **Consolidated Commercial Balance**: A bar chart comparing deposits vs loans.
*   **Portfolio Risk Profile**: Internal credit rating distribution (Low, Medium, High Risk).

### Tab 2: Credit Risk (Riesgo de Crédito)
*   **Delinquency Rate vs Monthly Inflation**: A dual-axis line chart that shows the correlation between Venezuela's monthly inflation spikes (INPC) and loan defaults. As inflation rises, customer repayment capacity drops, causing delinquency (`dias_atraso` > 90) to increase.
*   **Probability of Default (PD) by Credit Score**: Shows default rates grouped by credit score. Ideal for training logistic regression or XGBoost classifiers for credit scoring.
*   **Delinquency by Economic Activity**: Compares default rates among employees, freelancers, business owners, and retirees.
*   **Portfolio Status by Credit Type**: Stacked bar chart showing outstanding balances classified by loan status (Vigente/Active, Paid, Defaulted, In Litigation).

### Tab 3: Operational Risk (Riesgo Operativo)
*   **Transactions by Channel & Status**: Stacked bar charts showing transaction volumes classified by status (Completed, Rejected due to insufficient funds, or Failed).
*   **System Outages (Caídas de Sistema)**: A time-series chart showing transaction failures on specific dates. These failures model operational network outages (e.g. timeout errors `ERR_TIMEOUT` or server cuts `ERR_CONEXION_HOST`).
*   **Losses by Fraud**: Visualizes fraud volume across channels. Pago Móvil (instant mobile payments) and Punto de Venta (POS) are highlighted as higher-risk channels.
*   **Critical Fraud Alerts**: A real-time table displaying high-value suspicious transactions. These incidents model night-time activity (1 AM - 5 AM), location anomalies, and device mismatches, providing features to train fraud-detection models.

### Tab 4: Liquidity and Market Risk (Riesgo de Liquidez)
*   **VES Deposits vs Legal Reserve (Encaje Legal)**: Illustrates how the 73% legal reserve requirement freezes VES deposits at the BCV, showing the bank's actual liquid capacity.
*   **Available Cash and Liquidity Gap**: Contrasts the bank's immediate cash reserves with its liquidity gap. A negative gap indicates that the bank must execute treasury operations to cover deficits.
*   **Treasury Flows**: Measures monthly volumes of overnight interbank borrowing (*Colocación Interbancaria*) received at active rates vs short-term investments (*Compra Divisas BCV*).

### Tab 5: Macroeconomic Analysis (Análisis Macroeconómico)
*   **Official BCV vs Parallel Exchange Rate**: Tracks the daily devaluation of the Bolívar and the widening gap (spread) between both rates.
*   **Inflation (INPC) vs GDP Growth**: Highlights the relationship between Venezuela's monthly inflation index and economic activity fluctuations.

---
---

# VERSIÓN EN ESPAÑOL

RiskVision es un entorno de datos sintéticos y visualizador interactivo diseñado para científicos y analistas de datos. Simula 3 años de operaciones diarias de un banco comercial en Venezuela (10,000 clientes, ~3 millones de transacciones) para construir y entrenar modelos de Machine Learning en Riesgo de Crédito, Operativo y Liquidez.

---

## 1. Cómo Inicializar la Base de Datos

La base de datos está construida sobre un archivo portable **SQLite** (`bank_data.db`) y exporta un script compatible con **PostgreSQL** (`database/backup_postgres.sql`).

Para inicializar o regenerar los datos, ejecuta:
```bash
python database/db_generator.py
```
*Nota: El generador utiliza librerías estándar de Python (`sqlite3`, `random`, `math`, `datetime`, `os`, `sys`) y no requiere dependencias externas.*

---

## 2. Instalación y Ejecución del Visualizador

El visualizador está desarrollado en **FastAPI** (Python) y posee un frontend premium SPA adaptable con modo oscuro en HTML5/CSS3.

### Prerrequisitos (Entorno Python)
Instala las dependencias listadas en el archivo `requirements.txt`:
```bash
python -m pip install -r requirements.txt
```

### Ejecutar la Aplicación Web
1.  **Inicio Rápido (Windows)**: Haz doble clic en el archivo `run.bat` y selecciona `1`. Esto iniciará el servidor FastAPI y abrirá `http://127.0.0.1:8000` en tu navegador.
2.  **Inicio Manual**:
    ```bash
    python -m uvicorn visualizer.app:app --host 127.0.0.1 --port 8000 --reload
    ```

---

## 3. Contexto Económico de Venezuela (Riesgos Reales)

Para lograr un modelado de Machine Learning realista, la simulación incorpora la realidad macroeconómica venezolana entre **Junio 2023 y Junio 2026**:

*   **Economía Multimoneda (USD/VES)**: El Bolívar (VES) es la moneda nacional, pero el país opera bajo una alta dolarización transaccional y de ahorros. Los clientes poseen cuentas corrientes/ahorros en Bolívares y cuentas de custodia de libre convertibilidad en Dólares (USD).
*   **Doble Tipo de Cambio**: Coexisten la tasa de cambio oficial determinada por el Banco Central de Venezuela (BCV) y el dólar paralelo (Monitor/DólarToday). La brecha cambiaria representa un riesgo de mercado y tipo de cambio crítico para el banco.
*   **Encaje Legal Restrictivo**: El BCV exige a la banca congelar un porcentaje altísimo de sus captaciones en VES, establecido históricamente en **73%** durante el período simulado. Esto restringe drásticamente los Bolívares que los bancos pueden prestar, haciendo que el crédito en VES sea escaso y indexado.
*   **Ciclos Transaccionales y Estacionalidad**: Se simulan picos de transacciones en quincenas (días 15 y 30) por pagos de nómina y una aceleración de hasta 3 veces en diciembre debido al pago de utilidades ("aguinaldos") y el consumo navideño.

---

## 4. Guía de Indicadores del Dashboard

### Pestaña 1: Resumen General
*   **Clientes Totales y Churn**: Muestra la cantidad total de clientes registrados y la tasa de deserción/churn (clientes inactivos), clave para el modelado de retención.
*   **Depósitos por Moneda (USD vs VES)**: Indica el índice de dolarización del banco, comparando los saldos en divisas con los Bolívares.
*   **Cartera Otorgada**: Monto total acumulado de préstamos vigentes.
*   **Balance Comercial Consolidado**: Gráfico de barras que compara depósitos totales frente a créditos colocados.
*   **Perfil de Riesgo de la Cartera**: Distribución de la clasificación de riesgo interna del portafolio (Riesgo Bajo, Medio, Alto).

### Pestaña 2: Riesgo de Crédito (Credit Risk)
*   **Tasa de Morosidad vs Inflación Mensual**: Gráfico de líneas que ilustra la correlación entre los picos de inflación mensual (INPC) y los impagos. Si la inflación sube, el poder adquisitivo se reduce y la morosidad (`dias_atraso` > 90) aumenta.
*   **Default por Score Crediticio**: Gráfico de barras que muestra la tasa de default por rangos de score de crédito. Útil para entrenar clasificadores de scoring (XGBoost, Regresión Logística).
*   **Morosidad por Actividad Económica**: Compara la tasa de morosidad entre empleados, independientes, empresarios y jubilados.
*   **Estado de Cartera por Tipo de Crédito**: Gráfico de barras apiladas que clasifica los saldos en USD por tipo de préstamo y estado (Vigente, Pagado, Vencido, En Litigio).

### Pestaña 3: Riesgo Operativo (Operational Risk)
*   **Transacciones por Canal y Estado**: Gráficos de barras apiladas que clasifican los volúmenes transaccionales en Completadas, Rechazadas (sin fondos) y Fallidas.
*   **Caídas de Sistema (Outages)**: Historial diario que muestra las fechas con fallas operativas masivas (caídas de core, fallas de red), simuladas mediante códigos como `ERR_TIMEOUT` o `ERR_CONEXION_HOST`.
*   **Fraude por Canal**: Distribución de pérdidas en USD por canal de cobro. Se resalta Pago Móvil (transferencias instantáneas) como el canal de mayor exposición al fraude.
*   **Alertas de Fraude**: Tabla de transacciones marcadas como fraudulentas. Simulan actividades inusuales en la madrugada (1 AM - 5 AM), coordenadas lejanas a la residencia del cliente y dispositivos desconocidos.

### Pestaña 4: Riesgo de Liquidez y Mercado
*   **Depósitos VES vs Encaje Legal**: Muestra gráficamente cómo el 73% de los depósitos en Bolívares permanecen bloqueados en el BCV, evidenciando la liquidez disponible real de la entidad.
*   **Disponible en Caja y Brecha de Liquidez**: Compara los Bolívares disponibles en bóveda con la brecha de encaje. Un saldo negativo activa necesidades de fondeo en tesorería.
*   **Flujo Mensual de Tesorería**: Volumen de préstamos interbancarios interdiarios (*Colocación Interbancaria*) solicitados a tasa activa vs. inversiones a plazo en divisas (*Compra Divisas BCV*).

### Pestaña 5: Análisis Macroeconómico
*   **Tipo de Cambio Oficial BCV vs Paralelo**: Histórico diario de las tasas cambiarias oficiales y paralelas, mostrando la devaluación acumulada del Bolívar.
*   **Inflación (INPC) vs Crecimiento PIB**: Relación mensual entre los índices de precios al consumidor y la variación de la actividad económica en Venezuela.
