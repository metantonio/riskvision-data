# RiskVision: AI Agent Benchmark Questions & Analytical Prompts
### Preguntas de Evaluación y Consultas Analíticas para Agentes de IA

This document contains a structured repository of analytical and operational questions designed for AI agents, text-to-SQL assistants, and machine learning models integrated with the `RiskVision` database (`bank_data.db`).

Este documento contiene un repositorio estructurado de preguntas analíticas y operativas diseñadas para agentes de IA, asistentes de texto a SQL y modelos de machine learning integrados con la base de datos de `RiskVision` (`bank_data.db`).

The questions are organized progressively from **Level 1 (Direct Lookups & Basic Aggregations)** to **Level 5 (Complex Multi-step Reasoning & Stress Testing)** in both **English** and **Spanish**.

---

## Index / Índice
- [Level 1: Basic Lookups & KPIs / Nivel 1: Consultas Directas y KPIs Básicos](#level-1-basic-lookups--kpis--nivel-1-consultas-directas-y-kpis-básicos)
- [Level 2: Cross-Table Filters & Segment Comparisons / Nivel 2: Filtrado Cruzado y Comparaciones de Segmentos](#level-2-cross-table-filters--segment-comparisons--nivel-2-filtrado-cruzado-y-comparaciones-de-segmentos)
- [Level 3: Time-Series, Seasonality & Macro Correlations / Nivel 3: Series Temporales, Estacionalidad y Macroeconomía](#level-3-time-series-seasonality--macro-correlations--nivel-3-series-temporales-estacionalidad-y-macroeconomía)
- [Level 4: Predictive Models & Risk Inference / Nivel 4: Modelos Predictivos e Inferencia de Riesgo](#level-4-predictive-models--risk-inference--nivel-4-modelos-predictivos-e-inferencia-de-riesgo)
- [Level 5: Complex Multi-step Strategy & Stress Testing / Nivel 5: Estrategia Multidimensional y Pruebas de Estrés](#level-5-complex-multi-step-strategy--stress-testing--nivel-5-estrategia-multidimensional-y-pruebas-de-estrés)

---

## Level 1: Basic Lookups & KPIs / Nivel 1: Consultas Directas y KPIs Básicos
*Questions that test basic SQL retrieval, single-table aggregations, and direct metric lookups.*  
*Preguntas que evalúan consultas SQL directas, agregaciones de una sola tabla y búsqueda de métricas puntuales.*

### 1.1 Customer Demographics / Demografía de Clientes
* **EN:** How many registered clients are currently active versus inactive in the bank?
  * **ES:** ¿Cuántos clientes registrados están actualmente activos versus inactivos en el banco?
  * *Tables:* `clientes`
* **EN:** What is the average credit score and average monthly income in USD across all active clients?
  * **ES:** ¿Cuál es el score de crédito promedio y el ingreso mensual promedio en USD de todos los clientes activos?
  * *Tables:* `clientes`
* **EN:** What are the top 5 states in Venezuela with the largest customer base?
  * **ES:** ¿Cuáles son los 5 estados de Venezuela con mayor número de clientes registrados?
  * *Tables:* `clientes`

### 1.2 Accounts & Balances / Cuentas y Saldos
* **EN:** What is the total aggregate balance held in Bolívares (VES) and in US Dollars (USD) across all active accounts?
  * **ES:** ¿Cuál es el saldo total consolidado en Bolívares (VES) y en Dólares (USD) de todas las cuentas activas?
  * *Tables:* `cuentas`
* **EN:** How many custody accounts in USD are currently open in the bank?
  * **ES:** ¿Cuántas cuentas de custodia en USD están actualmente abiertas en el banco?
  * *Tables:* `cuentas`

### 1.3 Transactions & Macro / Transacciones y Macro
* **EN:** What was the official BCV exchange rate and the parallel market rate on December 31, 2024?
  * **ES:** ¿Cuál fue la tasa de cambio oficial del BCV y la tasa paralela el 31 de diciembre de 2024?
  * *Tables:* `indicadores_macro`
* **EN:** What percentage of transactions in the database are completed successfully versus rejected due to insufficient funds?
  * **ES:** ¿Qué porcentaje de transacciones en la base de datos están completadas versus rechazadas por saldo insuficiente?
  * *Tables:* `transacciones`
* **EN:** How many fraudulent transactions have been identified, and what is their total volume in USD?
  * **ES:** ¿Cuántas transacciones fraudulentas han sido identificadas y cuál es su monto total acumulado en USD?
  * *Tables:* `transacciones`

---

## Level 2: Cross-Table Filters & Segment Comparisons / Nivel 2: Filtrado Cruzado y Comparaciones de Segmentos
*Questions requiring multi-table joins, grouped segmentations, and conditional comparisons.*  
*Preguntas que requieren joins entre tablas, segmentaciones agrupadas y comparaciones condicionales.*

### 2.1 Credit Risk & Delinquency / Riesgo Crediticio y Morosidad
* **EN:** What is the loan default rate (percentage of loans in 'Vencido' or 'En Litigio') segmented by loan category (Consumo, Comercial, Microcredito)?
  * **ES:** ¿Cuál es la tasa de impago (porcentaje de créditos en 'Vencido' o 'En Litigio') segmentada por tipo de crédito (Consumo, Comercial, Microcrédito)?
  * *Tables:* `creditos`
* **EN:** Which economic activity (`actividad_economica`) exhibits the highest average days past due (`dias_atraso`) on loan installment payments?
  * **ES:** ¿Qué actividad económica (`actividad_economica`) presenta el mayor promedio de días de atraso (`dias_atraso`) en el pago de cuotas?
  * *Tables:* `clientes`, `creditos`, `pagos_creditos`
* **EN:** What is the total outstanding balance in USD for clients classified under the 'Alto' internal risk category?
  * **ES:** ¿Cuál es el saldo pendiente total en USD de los créditos de clientes clasificados con nivel de riesgo interno 'Alto'?
  * *Tables:* `clientes`, `creditos`

### 2.2 Operational Risk & Outages / Riesgo Operativo y Fallas
* **EN:** On which specific dates did the bank experience operational outages (`estado = 'Fallida'`), and what was the predominant error code on each date?
  * **ES:** ¿En cuáles fechas específicas experimentó el banco caídas del sistema (`estado = 'Fallida'`) y cuál fue el código de error predominante en cada fecha?
  * *Tables:* `transacciones`
* **EN:** Which transaction channel (Pago Móvil, Punto de Venta, ATM, etc.) accounts for the largest share of completed volume in Bolívares?
  * **ES:** ¿Cuál canal transaccional (Pago Móvil, Punto de Venta, ATM, etc.) concentra la mayor proporción del volumen completado en Bolívares?
  * *Tables:* `transacciones`, `cuentas`
* **EN:** What is the average transaction amount in USD for fraudulent transactions versus legitimate transactions on the Pago Móvil channel?
  * **ES:** ¿Cuál es el monto promedio en USD de las transacciones fraudulentas comparado con las legítimas en el canal Pago Móvil?
  * *Tables:* `transacciones`

### 2.3 Treasury & Liquidity / Tesorería y Liquidez
* **EN:** How many overnight interbank funding operations (`Colocacion Interbancaria`) did the bank execute, and who were the main counterparties?
  * **ES:** ¿Cuántas operaciones de fondeo interbancario (*overnight*) ejecutó el banco y cuáles fueron las principales contrapartes?
  * *Tables:* `operaciones_tesoreria`
* **EN:** On how many days did the bank experience a negative liquidity gap (`brecha_liquidez_usd < 0`) where vault cash fell below the legal reserve requirement?
  * **ES:** ¿En cuántos días presentó el banco una brecha de liquidez negativa (`brecha_liquidez_usd < 0`), donde el disponible en caja estuvo por debajo del encaje legal?
  * *Tables:* `resumen_liquidez_diario`

---

## Level 3: Time-Series, Seasonality & Macro Correlations / Nivel 3: Series Temporales, Estacionalidad y Macroeconomía
*Questions testing trend analysis, macroeconomic impact on consumer behavior, and cyclical effects.*  
*Preguntas que evalúan análisis de tendencias, impacto macroeconómico en el comportamiento del usuario y efectos cíclicos.*

### 3.1 Inflation & Currency Dynamics / Inflación y Dinámica Cambiaria
* **EN:** How did the exchange rate gap between the parallel dollar and the official BCV rate evolve month-by-month between June 2023 and December 2024?
  * **ES:** ¿Cómo evolucionó mes a mes la brecha entre el dólar paralelo y la tasa oficial del BCV entre junio de 2023 y diciembre de 2024?
  * *Tables:* `indicadores_macro`
* **EN:** Is there an observable increase in loan payment delays (`dias_atraso`) during the months with the highest monthly inflation rates?
  * **ES:** ¿Existe un incremento observable en los atrasos de pago de créditos (`dias_atraso`) durante los meses con mayores tasas de inflación mensual?
  * *Tables:* `pagos_creditos`, `indicadores_macro`
* **EN:** During which month did the Central Bank of Venezuela official rate experience its steepest monthly percentage devaluation?
  * **ES:** ¿En qué mes experimentó la tasa oficial del BCV su mayor devaluación porcentual mensual?
  * *Tables:* `indicadores_macro`

### 3.2 Payroll Cycles & Seasonal Spending / Ciclos de Nómina y Estacionalidad
* **EN:** What is the difference in daily transaction volume and total amount on salary payment days (15th and 30th) compared to ordinary business days?
  * **ES:** ¿Cuál es la diferencia en volumen transaccional diario y monto total en los días de pago de nómina (días 15 y 30) comparado con días hábiles ordinarios?
  * *Tables:* `transacciones`
* **EN:** How does transactional volume and average purchase size in December compare to the yearly monthly average, reflecting holiday season spending?
  * **ES:** ¿Cómo se compara el volumen transaccional y el monto promedio de compra en diciembre frente al promedio mensual del resto del año (efecto compras navideñas)?
  * *Tables:* `transacciones`
* **EN:** How do the deposit balances in Bolívares held by commercial clients (`J` document type) fluctuate between mid-month and month-end?
  * **ES:** ¿Cómo fluctúan los saldos de depósitos en Bolívares de clientes comerciales (tipo de documento `J`) entre quincenas y cierres de mes?
  * *Tables:* `clientes`, `cuentas`

---

## Level 4: Predictive Models & Risk Inference / Nivel 4: Modelos Predictivos e Inferencia de Riesgo
*Questions designed for AI agents interacting with trained machine learning models (Credit Scoring, Fraud Detection, Liquidity Forecasting).*  
*Preguntas orientadas a agentes de IA que consultan o interpretan modelos de ML (Credit Scoring, Detección de Fraude, Pronóstico de Liquidez).*

### 4.1 Credit Scoring & Probability of Default (PD)
* **EN:** If an active client with a credit score of 520, monthly income of $250 USD, and employed in the public sector requests a $1,500 USD Consumer loan for 12 months, what is their estimated Probability of Default (PD), and what key risk factors drive that prediction?
  * **ES:** Si un cliente activo con score de 520, ingreso de $250 USD y empleado público solicita un préstamo de Consumo por $1,500 USD a 12 meses, ¿cuál es su Probabilidad de Incumplimiento (PD) estimada y cuáles variables de riesgo sustentan esa predicción?
  * *Models/Tables:* Modelo PD / `clientes`, `creditos`, `indicadores_macro`
* **EN:** What is the Debt-to-Income (DTI) threshold above which historical default rates exceed 20% in the bank's portfolio?
  * **ES:** ¿Cuál es el umbral de relación Deuda-Ingreso (DTI) a partir del cual la tasa histórica de impago supera el 20% en la cartera del banco?
  * *Tables:* `clientes`, `creditos`
* **EN:** Which client segment presents the best risk-adjusted return: commercial loans for small companies or consumer loans for high-income private employees?
  * **ES:** ¿Qué segmento de clientes presenta el mejor retorno ajustado por riesgo: préstamos comerciales para pymes o créditos de consumo para empleados privados de altos ingresos?
  * *Tables:* `clientes`, `creditos`, `pagos_creditos`

### 4.2 Fraud Detection & Anomaly Rules
* **EN:** What are the top 3 feature anomalies that distinguish a transaction flagged as fraud (`es_fraude = 1`) from normal legitimate spending?
  * **ES:** ¿Cuáles son las 3 anomalías de variables más determinantes que distinguen una transacción marcada como fraude (`es_fraude = 1`) de un gasto legítimo habitual?
  * *Models/Tables:* Modelo Antifraude / `transacciones`, `clientes`
* **EN:** If an account located in Caracas executes a $400 USD Pago Móvil transaction at 3:15 AM from an unrecognized device ID, what is the anomaly risk score assigned by the model?
  * **ES:** Si una cuenta registrada en Caracas ejecuta un Pago Móvil de $400 USD a las 3:15 AM desde un dispositivo desconocido, ¿cuál es el nivel de riesgo o puntaje de anomalía asignado por el modelo?
  * *Models/Tables:* Modelo Antifraude / `transacciones`, `cuentas`, `clientes`

### 4.3 Liquidity Gap Forecasting
* **EN:** Based on historical legal reserve requirements (73% BCV encaje) and projected exchange rate devaluations, what is the forecasted liquidity gap (`brecha_liquidez_usd`) for the next 7 business days?
  * **ES:** Con base en el encaje legal histórico (73% BCV) y las proyecciones de devaluación cambiaria, ¿cuál es el pronóstico de la brecha de liquidez (`brecha_liquidez_usd`) para los próximos 7 días hábiles?
  * *Models/Tables:* Modelo de Liquidez / `resumen_liquidez_diario`, `indicadores_macro`

---

## Level 5: Complex Multi-step Strategy & Stress Testing / Nivel 5: Estrategia Multidimensional y Pruebas de Estrés
*Comprehensive scenarios requiring the agent to synthesize multiple domains: macro stress tests, customer churn diagnostics, profitability impact, and regulatory compliance.*  
*Escenarios complejos que requieren sintetizar múltiples áreas: pruebas de estrés macroeconómicas, diagnóstico de fuga de clientes, impacto en rentabilidad y cumplimiento regulatorio.*

### 5.1 Macroeconomic Stress Testing / Pruebas de Estrés Macroeconómicas
* **EN:** **Scenario:** The parallel dollar jumps by 35% in a single month while monthly inflation rises to 8.0%.  
  Based on our historical delinquency data, how many additional loans would enter default, what would be the expected dollar loss in credit portfolio provisions, and how much would deposit balances in VES decline due to capital flight toward USD?
  * **ES:** **Escenario:** El dólar paralelo sube un 35% en un solo mes mientras la inflación mensual alcanza el 8.0%.  
  Con base en el histórico de morosidad, ¿cuántos créditos adicionales caerían en mora, cuál sería la pérdida esperada en provisiones en dólares y cuánto disminuirían los depósitos en Bolívares por fuga hacia divisas?
  * *Tables:* `creditos`, `pagos_creditos`, `cuentas`, `indicadores_macro`, `resumen_liquidez_diario`

### 5.2 Capital Reserve & Liquidity Crunch Simulation / Simulación de Crisis de Liquidez
* **EN:** How did the widening of the exchange rate spread in October–December 2024 impact the bank's daily liquidity ratio and the frequency of emergency overnight interbank borrowing? Calculate the total annualized interest cost incurred in treasury funding during that quarter.
  * **ES:** ¿Cómo impactó la apertura de la brecha cambiaria en octubre-diciembre de 2024 en la tasa de liquidez diaria y en la frecuencia de préstamos interbancarios overnight? Calcula el costo total en intereses incurrido en operaciones de tesorería durante ese trimestre.
  * *Tables:* `indicadores_macro`, `resumen_liquidez_diario`, `operaciones_tesoreria`

### 5.3 Operational Outage Cost Analysis / Análisis del Costo Operativo de Fallas de Sistema
* **EN:** On November 20, 2023, a nationwide CANTV outage caused widespread transaction failures (`ERR_TIMEOUT` and `ERR_CONEXION_HOST`).  
  Quantify the total financial impact of this outage by calculating:
  1. The total rejected transaction volume in USD.
  2. Estimated merchant fee revenue lost (assuming a standard 1.5% POS commission and 0.3% Pago Móvil fee).
  3. The number of affected unique customers.
  * **ES:** El 20 de noviembre de 2023, una caída nacional de CANTV provocó fallas masivas en transacciones (`ERR_TIMEOUT` y `ERR_CONEXION_HOST`).  
  Cuantifica el impacto financiero total de esta caída calculando:
  1. El volumen transaccional total rechazado/fallido expresado en USD.
  2. Las comisiones bancarias estimadas no percibidas (asumiendo 1.5% en comisiones de Punto de Venta y 0.3% en Pago Móvil).
  3. El número de clientes únicos afectados.
  * *Tables:* `transacciones`, `cuentas`, `clientes`

### 5.4 Customer Churn & Portfolio Flight Diagnostic / Diagnóstico de Desafiliación de Clientes
* **EN:** Analyze the demographic and financial profile of clients who became inactive (`estado_cliente = 'Inactivo'`).  
  Do churned clients share specific characteristics in terms of credit score, economic activity, geographic state, or average account balance in the 90 days prior to their disaffiliation date?
  * **ES:** Analiza el perfil demográfico y financiero de los clientes que se desafiliaron del banco (`estado_cliente = 'Inactivo'`).  
  ¿Comparten los clientes que abandonaron el banco características específicas en cuanto a score crediticio, actividad económica, estado de residencia o saldo promedio en los 90 días previos a su fecha de retiro?
  * *Tables:* `clientes`, `cuentas`, `transacciones`

### 5.5 Overdraft & Credit Card Facility Utilization / Uso de Líneas de Crédito y Sobregiros
* **EN:** How many customers executed transactions that exceeded their available liquid balance by utilizing authorized overdraft or credit lines?  
  What was the average recovery period until their account returned to a positive balance, and what was the net interest yield generated from these credit facilities?
  * **ES:** ¿Cuántos clientes ejecutaron transacciones que superaron su saldo líquido disponible haciendo uso de líneas de crédito o sobregiro autorizado?  
  ¿Cuál fue el tiempo promedio de recuperación hasta que la cuenta retornó a saldo positivo y cuál fue el rendimiento neto en intereses generado por estas facilidades de crédito?
  * *Tables:* `cuentas`, `transacciones`, `clientes`, `creditos`

---

## Suggested Agent Execution Commands / Comandos Sugeridos para Ejecutar con Agentes
To prompt your AI agents with these questions, you can ask them directly in natural language (English or Spanish):
* *"Analyze the correlation between inflation spikes and loan default rates across all credit categories."*
* *"¿Cuál fue el costo financiero total para el banco de la falla de CANTV del 20 de noviembre de 2023?"*
* *"Build a risk profile report for clients who hold balances in both VES and USD."*
