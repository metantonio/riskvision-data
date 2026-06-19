# RiskVision: Data Dictionary & Schema Specification
### Diccionario de Datos y Especificación de Esquema

This document contains the complete database dictionary, data types, column descriptions, and exact row counts for the `RiskVision` database (`bank_data.db`).

Este documento contiene el diccionario de datos completo, tipos de datos, descripción de columnas y cantidad exacta de filas para la base de datos de `RiskVision` (`bank_data.db`).

---

## Database Overview & Row Counts / Resumen y Cantidad de Filas

| Table Name / Tabla | Rows / Filas | Primary Key / Clave Primaria | Description / Descripción |
| :--- | :--- | :--- | :--- |
| [`clientes`](#1-clientes) | 10,000 | `id` (AUTOINCREMENT) | Demographics & credit profiles of customers / Datos demográficos y perfil crediticio. |
| [`cuentas`](#2-cuentas) | 13,101 | `id` (AUTOINCREMENT) | Accounts held in Bolívares (VES) & Dollars (USD) / Cuentas en Bolívares y Dólares. |
| [`transacciones`](#3-transacciones) | 3,016,766 | `id` (AUTOINCREMENT) | Historical transaction logs and fraud flags / Historial de transacciones y banderas de fraude. |
| [`creditos`](#4-creditos) | 44 | `id` (AUTOINCREMENT) | Active and past loan portfolio details / Detalles de la cartera de préstamos aprobados. |
| [`pagos_creditos`](#5-pagos_creditos) | 661 | `id` (AUTOINCREMENT) | Monthly payment tracking and delinquency days / Control de cuotas de pago e impagos. |
| [`indicadores_macro`](#6-indicadores_macro) | 1,097 | `fecha` | Daily economic indicators in Venezuela / Indicadores económicos diarios de Venezuela. |
| [`resumen_liquidez_diario`](#7-resumen_liquidez_diario) | 1,097 | `fecha` | Aggregated daily bank balance sheets / Balance diario consolidado del banco. |
| [`operaciones_tesoreria`](#8-operaciones_tesoreria) | 1,020 | `id` (AUTOINCREMENT) | Treasury cash funding and placements / Fondeos y colocaciones financieras del banco. |

---

## Table Specifications / Especificación de Tablas

### 1. `clientes`
*Description: Contains demographic and credit-related features of the bank's clients.*
*Descripción: Contiene características demográficas y crediticias de los clientes del banco.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique identifier for each client. | Identificador único del cliente. | `1` |
| `nombre` | TEXT | VARCHAR(100) | No | First name of the client. | Primer nombre del cliente. | `Juan` |
| `apellido` | TEXT | VARCHAR(100) | No | Last name of the client. | Apellidos del cliente. | `Rodríguez González` |
| `tipo_documento`| TEXT | CHAR(1) | No | Document type: 'V' (Venezuelan), 'E' (Foreigner), 'J' (Company). | Tipo de documento: 'V' (Venezolano), 'E' (Extranjero), 'J' (Jurídico). | `V` |
| `cedula` | TEXT | VARCHAR(20) | No | Unique identity card number. | Número único de cédula o RIF. | `V-18234567` |
| `fecha_nacimiento`| DATE | DATE | No | Birth date (or registry date for companies). | Fecha de nacimiento (o registro para personas jurídicas). | `1985-05-14` |
| `genero` | TEXT | CHAR(1) | No | Gender: 'M' (Male) or 'F' (Female). | Género: 'M' (Masculino) o 'F' (Femenino). | `M` |
| `estado_civil` | TEXT | VARCHAR(20) | No | Civil status: Soltero, Casado, Divorciado, Viudo. | Estado civil: Soltero, Casado, Divorciado, Viudo. | `Casado` |
| `email` | TEXT | VARCHAR(100) | No | Email address. | Dirección de correo electrónico. | `juan.rodriguez@gmail.com` |
| `telefono` | TEXT | VARCHAR(30) | No | Venezuelan mobile phone number. | Número telefónico móvil venezolano. | `0414-1234567` |
| `estado_residencia`| TEXT| VARCHAR(50) | No | Venezuelan state of residence. | Estado de residencia en Venezuela. | `Distrito Capital` |
| `fecha_registro`| DATE | DATE | No | Date when the client opened their first account. | Fecha en la que el cliente se registró en el banco. | `2023-06-19` |
| `estado_cliente`| TEXT | VARCHAR(10) | No | Active or Inactive (for churn modeling). | Estado del cliente: 'Activo' o 'Inactivo' (churn). | `Activo` |
| `fecha_desafiliacion`| DATE| DATE | Yes | Date client left the bank, if applicable. | Fecha en la que el cliente se retiró, si aplica. | `2024-11-20` |
| `score_credito` | INTEGER | INT | No | Credit bureau score (300 to 850). | Puntaje de buró de crédito (300 a 850). | `645` |
| `ingresos_mensuales_usd`| REAL | NUMERIC(15,2)| No | Base monthly income in US Dollars. | Ingresos mensuales estimados en Dólares. | `450.00` |
| `actividad_economica`| TEXT | VARCHAR(100) | No | Sector of economic activity. | Actividad económica o tipo de empleo. | `Empleado Privado` |
| `nivel_riesgo_interno`| TEXT | VARCHAR(10) | No | Bank's risk class: Bajo, Medio, Alto. | Nivel de riesgo interno asignado: Bajo, Medio, Alto. | `Medio` |

---

### 2. `cuentas`
*Description: Holds current and savings accounts details in VES or USD.*
*Descripción: Detalles de cuentas corrientes y de ahorro abiertas en VES o USD.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique identifier for each account. | Identificador único de la cuenta. | `1` |
| `cliente_id` | INTEGER | INT | No | Foreign key referencing `clientes(id)`. | Clave foránea que referencia a `clientes(id)`. | `1` |
| `numero_cuenta` | TEXT | CHAR(20) | No | Standard 20-digit Venezuelan account number. | Número de cuenta estándar venezolano (20 dígitos). | `01051234567890123456` |
| `tipo_cuenta` | TEXT | VARCHAR(15) | No | Account type: Corriente (Checking) or Ahorros (Savings). | Tipo de cuenta: Corriente o Ahorros. | `Corriente` |
| `moneda` | TEXT | CHAR(3) | No | Currency: VES (Bolívares) or USD (USD Custody). | Moneda de la cuenta: VES o USD. | `VES` |
| `fecha_apertura` | DATE | DATE | No | Opening date. | Fecha de apertura de la cuenta. | `2023-06-19` |
| `saldo_actual` | REAL | NUMERIC(18,2)| No | Current balance (at the end of simulation). | Saldo actual de la cuenta (al final de la serie). | `12450.50` |
| `estado_cuenta` | TEXT | VARCHAR(15) | No | Account status: Activa, Bloqueada, Cerrada. | Estado de la cuenta: Activa, Bloqueada, Cerrada. | `Activa` |

---

### 3. `transacciones`
*Description: Ledger of all transaction events (deposits, purchases, withdrawals, and fraud flags).*
*Descripción: Historial de transacciones (depósitos, compras, retiros y marcas de fraude).*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique transaction identifier. | Identificador único de la transacción. | `1540` |
| `cuenta_id` | INTEGER | INT | No | Foreign key referencing `cuentas(id)`. | Clave foránea que referencia a `cuentas(id)`. | `1` |
| `tipo_transaccion`| TEXT| VARCHAR(30) | No | Transaction type (e.g. Pago Movil, Compra Punto Venta). | Tipo de transacción (e.g. Pago Móvil, Compra Punto Venta). | `Pago Movil` |
| `monto` | REAL | NUMERIC(18,2)| No | Amount in the account's original currency. | Monto en la moneda original de la cuenta. | `450.00` |
| `monto_usd` | REAL | NUMERIC(18,2)| No | Standardized amount in US Dollars. | Monto normalizado en Dólares. | `11.65` |
| `tasa_cambio` | REAL | NUMERIC(12,4)| No | BCV official exchange rate of the transaction day. | Tasa de cambio oficial BCV del día de transacción. | `38.6200` |
| `fecha_hora` | TIMESTAMP | TIMESTAMP | No | Date and time of the event. | Fecha y hora exacta de la transacción. | `2024-12-10 12:30:15` |
| `canal` | TEXT | VARCHAR(30) | No | Transaction channel (e.g. Pago Movil, ATM, POS). | Canal de la transacción (e.g. Pago Móvil, ATM, POS). | `Pago Movil` |
| `estado` | TEXT | VARCHAR(15) | No | Status: Completada, Rechazada, Fallida. | Estado: Completada, Rechazada, Fallida. | `Completada` |
| `codigo_error` | TEXT | VARCHAR(30) | Yes | Error code for failed events (e.g. ERR_TIMEOUT). | Código de error para fallas operativas (e.g. ERR_TIMEOUT). | `NULL` |
| `es_fraude` | INTEGER | INT | No | Fraud flag: 1 (Fraudulent), 0 (Legitimate). | Bandera de fraude: 1 (Fraude), 0 (Legítimo). | `0` |
| `latitud` | REAL | NUMERIC(9,6) | Yes | Latitude coordinates of the transaction. | Latitud geográfica de la transacción. | `10.4806` |
| `longitud` | REAL | NUMERIC(9,6) | Yes | Longitude coordinates of the transaction. | Longitud geográfica de la transacción. | `-66.9036` |
| `dispositivo_id` | TEXT | VARCHAR(30) | Yes | ID of the device initiating the transaction. | Identificador único del dispositivo / IP. | `DEV_024581` |

---

### 4. `creditos`
*Description: Log of loans approved for qualified retail or corporate clients.*
*Descripción: Historial de créditos comerciales o consumo aprobados para clientes elegibles.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique loan identifier. | Identificador único del préstamo. | `1` |
| `cliente_id` | INTEGER | INT | No | Foreign key referencing `clientes(id)`. | Clave foránea que referencia a `clientes(id)`. | `542` |
| `monto_aprobado_usd`| REAL| NUMERIC(15,2)| No | Approved principal in USD. | Monto total aprobado en Dólares. | `1500.00` |
| `tasa_interes_anual`| REAL| NUMERIC(5,2)| No | Annual nominal lending interest rate. | Tasa de interés activa anual pactada. | `36.50` |
| `plazo_meses` | INTEGER | INT | No | Term of the loan in months. | Plazo del crédito expresado en meses. | `12` |
| `fecha_otorgamiento`| DATE| DATE | No | Credit origination date. | Fecha de otorgamiento del préstamo. | `2024-03-15` |
| `fecha_vencimiento`| DATE | DATE | No | Credit maturity date. | Fecha de vencimiento final del préstamo. | `2025-03-15` |
| `tipo_credito` | TEXT | VARCHAR(20) | No | Category: Consumo, Comercial, Microcredito. | Tipo: Consumo, Comercial, Microcrédito. | `Consumo` |
| `estado` | TEXT | VARCHAR(15) | No | Current state: Vigente, Pagado, Vencido, En Litigio. | Estado actual: Vigente, Pagado, Vencido, En Litigio. | `Vigente` |
| `saldo_pendiente_usd`| REAL| NUMERIC(15,2)| No | Outstanding balance in USD. | Saldo remanente pendiente en Dólares. | `500.00` |
| `cuotas_totales` | INTEGER | INT | No | Number of monthly installments. | Número total de cuotas mensuales pactadas. | `12` |
| `cuotas_pagadas` | INTEGER | INT | No | Number of paid installments. | Número de cuotas pagadas a la fecha. | `8` |

---

### 5. `pagos_creditos`
*Description: Amortization tracking, capturing payment history and overdue days.*
*Descripción: Control de amortización mensual de cuotas e historial de días de retraso.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique payment identifier. | Identificador único del pago de cuota. | `1` |
| `credito_id` | INTEGER | INT | No | Foreign key referencing `creditos(id)`. | Clave foránea que referencia a `creditos(id)`. | `1` |
| `monto_pago_usd` | REAL | NUMERIC(15,2)| No | Installment amount paid in USD (0 if unpaid). | Monto pagado por el cliente en USD (0 si no pagó). | `145.20` |
| `fecha_pago` | DATE | DATE | No | Date when the payment was processed. | Fecha de procesamiento del pago. | `2024-04-15` |
| `dias_atraso` | INTEGER | INT | No | Days past due (0 if paid on time). | Días de atraso en el pago (0 si fue a tiempo). | `0` |
| `estado_pago` | TEXT | VARCHAR(15) | No | Payment classification: A Tiempo, Atrasado, No Pagado. | Estado de la cuota: A Tiempo, Atrasado, No Pagado. | `A Tiempo` |

---

### 6. `indicadores_macro`
*Description: Timeseries containing daily macroeconomic metrics for Venezuela.*
*Descripción: Serie de tiempo diaria de indicadores macroeconómicos y de cambio de Venezuela.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fecha` | DATE | DATE | No (PK) | Daily date key. | Fecha de registro del indicador. | `2024-12-10` |
| `tasa_bcv_usd_ves`| REAL | NUMERIC(12,4)| No | Central Bank of Venezuela official exchange rate. | Tasa de cambio oficial publicada por el BCV. | `38.6200` |
| `tasa_paralela_usd_ves`| REAL | NUMERIC(12,4)| No | Parallel market exchange rate. | Tipo de cambio promedio del mercado paralelo. | `43.1500` |
| `inflacion_mensual_pct`| REAL | NUMERIC(5,2)| No | National monthly inflation rate (INPC). | Tasa de inflación mensual registrada (INPC). | `2.80` |
| `variacion_pib_mensual_pct`| REAL| NUMERIC(5,2)| No | Monthly GDP growth proxy. | Variación mensual de la actividad económica (PIB). | `1.20` |
| `tasa_activa_ves_anual`| REAL | NUMERIC(5,2)| No | Active lending rate in Bolívares. | Tasa de interés activa anual promedio fijada en VES. | `36.50` |
| `tasa_pasiva_ves_anual`| REAL | NUMERIC(5,2)| No | Passive deposit rate in Bolívares. | Tasa de interés pasiva anual promedio fijada en VES. | `14.00` |

---

### 7. `resumen_liquidez_diario`
*Description: Daily aggregated bank balances to assess liquidity ratios and legal reserves.*
*Descripción: Consolidado diario del balance bancario para evaluar ratios de liquidez y encaje legal.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fecha` | DATE | DATE | No (PK) | Date of aggregation. | Fecha del balance consolidado. | `2024-12-10` |
| `total_depositos_ves`| REAL| NUMERIC(20,2)| No | Sum of all active account balances in Bolívares. | Total acumulado de depósitos en cuentas VES. | `45120300.20` |
| `total_depositos_usd`| REAL| NUMERIC(20,2)| No | Sum of all active account balances in US Dollars. | Total acumulado de depósitos en cuentas USD. | `12450800.50` |
| `total_creditos_ves`| REAL| NUMERIC(20,2)| No | Sum of active loans converted to Bolívares. | Total de cartera de créditos en Bolívares. | `5420100.00` |
| `total_creditos_usd`| REAL| NUMERIC(20,2)| No | Sum of active loans in US Dollars. | Total de cartera de créditos en Dólares. | `140344.38` |
| `disponible_caja_ves`| REAL| NUMERIC(20,2)| No | Liquid funds held in bank vaults (in VES). | Fondos líquidos disponibles en caja (en Bolívares). | `6768045.03` |
| `encaje_legal_bcv_ves`| REAL| NUMERIC(20,2)| No | Required reserve frozen at the BCV (73% of VES deposits). | Encaje legal obligatorio inmovilizado en el BCV. | `32937819.15` |
| `tasa_liquidez` | REAL | NUMERIC(8,4) | No | Liquidity ratio: Liquid Assets / Total Deposits. | Tasa de liquidez: Activo disponible / Pasivos totales. | `0.1502` |
| `brecha_liquidez_usd`| REAL | NUMERIC(18,2)| No | Net liquidity surplus/deficit in USD. | Excedente o déficit neto de liquidez en Dólares. | `-2450.12` |

---

### 8. `operaciones_tesoreria`
*Description: Ledger of overnight interbank funding or Central Bank currency interventions.*
*Descripción: Historial de fondeos interbancarios interdiarios (Overnight) o compra-venta de divisas.*

| Column / Columna | Type (SQLite) | Type (Postgres) | Nullable | Description (EN) | Descripción (ES) | Example / Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | SERIAL | No | Unique transaction identifier. | Identificador único de la operación de tesorería. | `1` |
| `fecha` | DATE | DATE | No | Date of the treasury transaction. | Fecha de la operación. | `2024-12-10` |
| `tipo_operacion` | TEXT | VARCHAR(30) | No | Operation: Colocacion Interbancaria, Compra Divisas BCV. | Tipo: Colocación Interbancaria, Compra Divisas BCV. | `Colocacion Interbancaria` |
| `monto_usd` | REAL | NUMERIC(15,2)| No | Volume of the transaction in USD. | Volumen de la operación expresado en Dólares. | `250000.00` |
| `tasa_anual` | REAL | NUMERIC(5,2)| No | Annualized yield rate. | Tasa de interés anual pactada. | `32.85` |
| `plazo_dias` | INTEGER | INT | No | Term of the placement in days (e.g. 1 for overnight). | Plazo en días (e.g. 1 para operaciones overnight). | `1` |
| `contraparte` | TEXT | VARCHAR(100) | No | Trade counterparty (e.g. Banco de Venezuela, BCV). | Entidad contraparte de la transacción financiera. | `Banco de Venezuela` |
