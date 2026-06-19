# Migrating RiskVision Data to Snowflake
### Migración de Datos de RiskVision a Snowflake

This guide details the easiest and fastest ways to upload the `RiskVision` bank database (SQLite) into Snowflake.

Esta guía detalla las formas más sencillas y rápidas de subir la base de datos bancaria de `RiskVision` (SQLite) a Snowflake.

---

## Method 1: The Programmatic Python Way (Recommended)
## Método 1: La Vía Programática con Python (Recomendado)

The simplest, most automated method is to use Python with the official Snowflake connector. The `write_pandas` function uploads the data to Snowflake's internal stage and copies it into target tables, automatically creating them.

El método más sencillo y automatizado es usar Python y el conector oficial de Snowflake. La función `write_pandas` sube los datos al stage interno de Snowflake y los copia a las tablas destino, creándolas automáticamente.

### Step 1: Install Requirements
### Paso 1: Instalar Requerimientos
Install the Snowflake Connector for Python with Pandas support:
Instala el conector de Snowflake con soporte para Pandas:
```bash
python -m pip install "snowflake-connector-python[pandas]"
```

### Step 2: Create and Run the Upload Script
### Paso 2: Crear y Ejecutar el Script de Subida
Create a file named `database/export_to_snowflake.py` and paste the following code:
Crea un archivo llamado `database/export_to_snowflake.py` y pega el siguiente código:

```python
import sqlite3
import pandas as pd
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas

# 1. Connect to local SQLite database / Conectar a SQLite local
sqlite_conn = sqlite3.connect("bank_data.db")

# 2. Connect to Snowflake (Configure with your credentials)
# Conectar a Snowflake (Configura con tus credenciales)
print("Connecting to Snowflake...")
sf_conn = connect(
    user='<YOUR_USER>',
    password='<YOUR_PASSWORD>',
    account='<YOUR_ACCOUNT_IDENTIFIER>',  # e.g., 'xy12345.us-east-2' or 'org-account'
    role="PUBLIC",
    warehouse='<YOUR_WAREHOUSE>',          # e.g., 'COMPUTE_WH'
    database='<YOUR_DATABASE>',            # e.g., 'RISKVISION_DB'
    schema='<YOUR_SCHEMA>'                 # e.g., 'PUBLIC'
)

# Tables to migrate / Tablas a migrar
tables = [
    'clientes', 
    'cuentas', 
    'creditos', 
    'pagos_creditos', 
    'indicadores_macro', 
    'resumen_liquidez_diario', 
    'operaciones_tesoreria', 
    'transacciones'  # ~3M rows / ~3M de filas
]

try:
    for table in tables:
        print(f"\n[+] Reading table '{table}' from SQLite...")
        # Read table into a Pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
        
        # Snowflake requires uppercase column names
        # Snowflake requiere nombres de columnas en mayúscula
        df.columns = [col.upper() for col in df.columns]
        
        # Adjust dates to string format for safety / Ajustar fechas a texto por seguridad
        for col in df.columns:
            if 'FECHA' in col or col == 'FECHA_HORA':
                df[col] = df[col].astype(str)
        
        print(f"[+] Uploading {len(df)} rows to Snowflake table '{table.upper()}'...")
        # write_pandas automatically creates the table if it does not exist
        # write_pandas crea la tabla automáticamente si no existe (auto_create_table=True)
        success, nchunks, nrows, _ = write_pandas(
            conn=sf_conn,
            df=df,
            table_name=table.upper(),
            auto_create_table=True
        )
        print(f"[✓] Successfully loaded {nrows} rows into Snowflake!")

except Exception as e:
    print(f"[✗] Error during migration: {e}")

finally:
    sqlite_conn.close()
    sf_conn.close()
    print("\n[+] Migration process completed / Proceso de migración finalizado.")
```

---

## Method 2: Export to CSV & Upload via Snowsight UI
## Método 2: Exportar a CSV y Subir por la Interfaz de Snowsight

If you prefer to use Snowflake's web console (Snowsight) without writing database credentials in scripts, you can export the database to CSV files and upload them.

Si prefieres usar la consola web de Snowflake (Snowsight) sin escribir credenciales en scripts, puedes exportar las tablas a archivos CSV y subirlas manualmente.

### Step 1: Export SQLite Tables to CSV
### Paso 1: Exportar Tablas SQLite a CSV
Run this short Python snippet to generate CSV files for each table:
Ejecuta este código en Python para generar los archivos CSV de cada tabla:
```python
import sqlite3
import pandas as pd
import os

conn = sqlite3.connect("bank_data.db")
os.makedirs("csv_export", exist_ok=True)
for table in ['clientes', 'cuentas', 'creditos', 'pagos_creditos', 'indicadores_macro', 'resumen_liquidez_diario', 'operaciones_tesoreria', 'transacciones']:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    df.to_csv(f"csv_export/{table}.csv", index=False)
conn.close()
```

### Step 2: Create Tables in Snowflake
### Paso 2: Crear las Tablas en Snowflake
Execute the DDL scripts in a Snowflake Worksheet. You can adapt the PostgreSQL schema provided in `database/backup_postgres.sql`. Snowflake standard types align closely (e.g., `VARCHAR`, `NUMBER`, `TIMESTAMP`, `DATE`).

Ejecuta el esquema DDL en una hoja de trabajo (Worksheet) de Snowflake. Puedes adaptar el esquema de PostgreSQL provisto en `database/backup_postgres.sql` (los tipos estándar como `VARCHAR`, `NUMBER`, `TIMESTAMP` y `DATE` son totalmente compatibles).

### Step 3: Load Data in Snowsight
### Paso 3: Cargar Datos en Snowsight
1. Log into your **Snowflake Console**.
2. Go to **Data** > **Databases** > Select your Database and Schema.
3. Click on the target table (e.g. `CLIENTES`).
4. Click **Load Data** in the top-right corner.
5. Browse and select your CSV file (e.g., `csv_export/clientes.csv`).
6. Configure the File Format (CSV, Skip header line = 1, Field separator = Comma).
7. Click **Load**.

*Note: For the large `transacciones.csv` (~300MB), the Snowsight UI might hit browser file size limits. For this table, using **Method 1** or uploading the file to a cloud stage (like AWS S3) and executing `COPY INTO` is highly recommended.*

*Nota: Para la tabla de `transacciones.csv` (~300MB), la consola de Snowsight podría alcanzar el límite de tamaño de subida del navegador. Para esta tabla se recomienda enfáticamente usar el **Método 1** o subir el archivo a un stage en la nube (ej. AWS S3) y ejecutar `COPY INTO`.*
