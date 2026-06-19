import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Visualizador de Riesgo Bancario - Venezuela")

# Configurar rutas para templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Conexión helper
def get_db():
    # bank_data.db está en la raíz del repositorio, subiendo un nivel desde visualizer/
    db_path = os.path.abspath(os.path.join(BASE_DIR, "..", "bank_data.db"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/kpis")
def get_kpis():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Total Clientes y Churn
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN estado_cliente='Inactivo' THEN 1 ELSE 0 END) as churned FROM clientes")
    clients_row = cursor.fetchone()
    total_clients = clients_row["total"]
    churned_clients = clients_row["churned"]
    churn_rate = round((churned_clients / total_clients) * 100, 2) if total_clients else 0.0
    
    # 2. Total Depósitos por Moneda
    cursor.execute("SELECT moneda, SUM(saldo_actual) as total_saldo FROM cuentas WHERE estado_cuenta='Activa' GROUP BY moneda")
    dep_rows = cursor.fetchall()
    deposits = {"VES": 0.0, "USD": 0.0}
    for r in dep_rows:
        deposits[r["moneda"]] = round(r["total_saldo"], 2)
        
    # 3. Créditos Totales e Impagos
    cursor.execute("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(CASE WHEN estado IN ('Vencido', 'En Litigio') THEN 1 ELSE 0 END) as defaulted_loans,
            SUM(monto_aprobado_usd) as total_monto_usd,
            SUM(CASE WHEN estado IN ('Vencido', 'En Litigio') THEN saldo_pendiente_usd ELSE 0 END) as total_def_monto_usd
        FROM creditos
    """)
    credit_row = cursor.fetchone()
    total_loans = credit_row["total_loans"]
    defaulted_loans = credit_row["defaulted_loans"]
    total_credit_monto = round(credit_row["total_monto_usd"] or 0.0, 2)
    default_monto = round(credit_row["total_def_monto_usd"] or 0.0, 2)
    default_rate = round((defaulted_loans / total_loans) * 100, 2) if total_loans else 0.0
    
    # 4. Transacciones y Fraude Operativo
    cursor.execute("""
        SELECT 
            COUNT(*) as total_txs,
            SUM(CASE WHEN es_fraude = 1 THEN 1 ELSE 0 END) as fraud_txs,
            SUM(CASE WHEN es_fraude = 1 THEN monto_usd ELSE 0 END) as fraud_monto_usd,
            SUM(CASE WHEN estado = 'Fallida' THEN 1 ELSE 0 END) as failed_txs
        FROM transacciones
    """)
    tx_row = cursor.fetchone()
    total_txs = tx_row["total_txs"]
    fraud_txs = tx_row["fraud_txs"] or 0
    fraud_monto = round(tx_row["fraud_monto_usd"] or 0.0, 2)
    failed_txs = tx_row["failed_txs"] or 0
    
    conn.close()
    
    return {
        "clientes": {
            "total": total_clients,
            "churn_rate_pct": churn_rate
        },
        "depositos": deposits,
        "creditos": {
            "total_prestamos": total_loans,
            "monto_total_usd": total_credit_monto,
            "monto_default_usd": default_monto,
            "default_rate_pct": default_rate
        },
        "operativo": {
            "total_transacciones": total_txs,
            "cantidad_fraudes": fraud_txs,
            "monto_fraude_usd": fraud_monto,
            "transacciones_fallidas": failed_txs,
            "tasa_falla_pct": round((failed_txs / total_txs) * 100, 4) if total_txs else 0.0
        }
    }

@app.get("/api/macro")
def get_macro():
    conn = get_db()
    cursor = conn.cursor()
    
    # Obtener agregados mensuales para que no sature la UI de puntos
    # SQLite no tiene funciones complejas de fecha en string por defecto, pero strftime funciona.
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', fecha) as mes,
            AVG(tasa_bcv_usd_ves) as bcv,
            AVG(tasa_paralela_usd_ves) as paralela,
            AVG(inflacion_mensual_pct) as inflacion,
            AVG(variacion_pib_mensual_pct) as pib,
            AVG(tasa_activa_ves_anual) as tasa_activa,
            AVG(tasa_pasiva_ves_anual) as tasa_pasiva
        FROM indicadores_macro
        GROUP BY mes
        ORDER BY mes
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "mes": r["mes"],
        "bcv": round(r["bcv"], 2),
        "paralela": round(r["paralela"], 2),
        "inflacion_pct": round(r["inflacion"], 2),
        "pib_var_pct": round(r["pib"], 2),
        "tasa_activa": round(r["tasa_activa"], 2),
        "tasa_pasiva": round(r["tasa_pasiva"], 2)
    } for r in rows]

@app.get("/api/credit")
def get_credit_risk():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Score crediticio de clientes al corriente vs en mora
    cursor.execute("""
        SELECT 
            CASE 
                WHEN score_credito >= 750 THEN '750+'
                WHEN score_credito >= 680 THEN '680-749'
                WHEN score_credito >= 600 THEN '600-679'
                WHEN score_credito >= 500 THEN '500-599'
                ELSE '300-499'
            END as rango_score,
            COUNT(*) as total,
            SUM(CASE WHEN estado IN ('Vencido', 'En Litigio') THEN 1 ELSE 0 END) as defaults
        FROM creditos cr
        JOIN clientes cl ON cr.cliente_id = cl.id
        GROUP BY rango_score
        ORDER BY rango_score DESC
    """)
    score_rows = cursor.fetchall()
    
    # 2. Cartera por tipo de crédito y estado
    cursor.execute("""
        SELECT 
            tipo_credito,
            estado,
            COUNT(*) as cantidad,
            SUM(saldo_pendiente_usd) as saldo_pendiente
        FROM creditos
        GROUP BY tipo_credito, estado
    """)
    type_rows = cursor.fetchall()
    
    # 3. Evolución mensual de tasa de morosidad vs inflación
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', fecha_pago) as mes,
            COUNT(*) as total_pagos,
            SUM(CASE WHEN estado_pago IN ('No Pagado', 'Atrasado') THEN 1 ELSE 0 END) as pagos_impagos,
            AVG(dias_atraso) as promedio_dias_atraso
        FROM pagos_creditos
        GROUP BY mes
        ORDER BY mes
    """)
    payments_rows = cursor.fetchall()
    
    # 4. Tasa de default según actividad económica
    cursor.execute("""
        SELECT 
            cl.actividad_economica,
            COUNT(*) as total_prestamos,
            SUM(CASE WHEN cr.estado IN ('Vencido', 'En Litigio') THEN 1 ELSE 0 END) as defaults
        FROM creditos cr
        JOIN clientes cl ON cr.cliente_id = cl.id
        GROUP BY cl.actividad_economica
    """)
    activity_rows = cursor.fetchall()
    
    conn.close()
    
    return {
        "scores": [{
            "rango": r["rango_score"],
            "total": r["total"],
            "defaults": r["defaults"],
            "tasa_default": round((r["defaults"] / r["total"]) * 100, 2) if r["total"] else 0.0
        } for r in score_rows],
        
        "cartera_tipo": [{
            "tipo": r["tipo_credito"],
            "estado": r["estado"],
            "cantidad": r["cantidad"],
            "saldo_usd": round(r["saldo_pendiente"] or 0.0, 2)
        } for r in type_rows],
        
        "evolucion_morosidad": [{
            "mes": r["mes"],
            "total_pagos": r["total_pagos"],
            "impagos": r["pagos_impagos"],
            "tasa_morosidad": round((r["pagos_impagos"] / r["total_pagos"]) * 100, 2) if r["total_pagos"] else 0.0,
            "promedio_dias_atraso": round(r["promedio_dias_atraso"] or 0.0, 1)
        } for r in payments_rows],
        
        "actividad_economica": [{
            "actividad": r["actividad_economica"],
            "total_prestamos": r["total_prestamos"],
            "defaults": r["defaults"],
            "tasa_default": round((r["defaults"] / r["total_prestamos"]) * 100, 2) if r["total_prestamos"] else 0.0
        } for r in activity_rows]
    }

@app.get("/api/operational")
def get_operational_risk():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Transacciones por canal y su estado
    cursor.execute("""
        SELECT 
            canal,
            estado,
            COUNT(*) as cantidad,
            SUM(monto_usd) as total_usd
        FROM transacciones
        GROUP BY canal, estado
    """)
    canal_rows = cursor.fetchall()
    
    # 2. Fraude por canal
    cursor.execute("""
        SELECT 
            canal,
            COUNT(*) as total_txs,
            SUM(es_fraude) as fraudes,
            SUM(CASE WHEN es_fraude = 1 THEN monto_usd ELSE 0 END) as monto_fraude
        FROM transacciones
        GROUP BY canal
    """)
    fraud_rows = cursor.fetchall()
    
    # 3. Historial de fallas operativas del sistema por día (Outages detectados)
    cursor.execute("""
        SELECT 
            date(fecha_hora) as dia,
            COUNT(*) as total_txs,
            SUM(CASE WHEN estado = 'Fallida' THEN 1 ELSE 0 END) as fallidas,
            SUM(CASE WHEN estado = 'Completada' THEN 1 ELSE 0 END) as completadas
        FROM transacciones
        GROUP BY dia
        HAVING fallidas > (total_txs * 0.15)
        ORDER BY dia
    """)
    outage_rows = cursor.fetchall()
    
    # 4. Transacciones fraudulentas notables (Top 10)
    cursor.execute("""
        SELECT 
            t.fecha_hora,
            c.cedula,
            c.nombre || ' ' || c.apellido as cliente,
            t.monto_usd,
            t.tipo_transaccion,
            t.canal,
            t.latitud,
            t.longitud
        FROM transacciones t
        JOIN cuentas ac ON t.cuenta_id = ac.id
        JOIN clientes c ON ac.cliente_id = c.id
        WHERE t.es_fraude = 1
        ORDER BY t.monto_usd DESC
        LIMIT 10
    """)
    top_frauds = cursor.fetchall()
    
    conn.close()
    
    return {
        "canales": [{
            "canal": r["canal"],
            "estado": r["estado"],
            "cantidad": r["cantidad"],
            "total_usd": round(r["total_usd"], 2)
        } for r in canal_rows],
        
        "fraudes_canal": [{
            "canal": r["canal"],
            "total_txs": r["total_txs"],
            "fraudes": r["fraudes"],
            "monto_fraude_usd": round(r["monto_fraude"] or 0.0, 2),
            "tasa_fraude_pct": round((r["fraudes"] / r["total_txs"]) * 100, 4) if r["total_txs"] else 0.0
        } for r in fraud_rows],
        
        "caidas_sistema": [{
            "dia": r["dia"],
            "total_txs": r["total_txs"],
            "fallidas": r["fallidas"],
            "tasa_falla_pct": round((r["fallidas"] / r["total_txs"]) * 100, 2)
        } for r in outage_rows],
        
        "listado_fraudes": [{
            "fecha_hora": r["fecha_hora"],
            "cedula": r["cedula"],
            "cliente": r["cliente"],
            "monto_usd": round(r["monto_usd"], 2),
            "tipo": r["tipo_transaccion"],
            "canal": r["canal"],
            "coords": f"{r['latitud']}, {r['longitud']}"
        } for r in top_frauds]
    }

@app.get("/api/liquidity")
def get_liquidity_risk():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Evolución semanal de depósitos, encaje legal y caja
    # Agrupamos semanalmente para no sobrecargar el gráfico (1095 días a ~150 semanas)
    cursor.execute("""
        SELECT 
            strftime('%Y-%W', fecha) as semana,
            MIN(fecha) as fecha_inicio,
            AVG(total_depositos_ves) as depositos_ves,
            AVG(total_depositos_usd) as depositos_usd,
            AVG(disponible_caja_ves) as disponible_ves,
            AVG(encaje_legal_bcv_ves) as encaje_ves,
            AVG(tasa_liquidez) as tasa_liq
        FROM resumen_liquidez_diario
        GROUP BY semana
        ORDER BY semana
    """)
    liq_rows = cursor.fetchall()
    
    # 2. Resumen de Operaciones de Tesorería
    cursor.execute("""
        SELECT 
            tipo_operacion,
            COUNT(*) as cantidad,
            SUM(monto_usd) as volumen_usd,
            AVG(tasa_anual) as tasa_promedio
        FROM operaciones_tesoreria
        GROUP BY tipo_operacion
    """)
    ops_rows = cursor.fetchall()
    
    # 3. Flujo cambiario (Préstamos interbancarios activos vs pasivos e inversiones)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', fecha) as mes,
            SUM(CASE WHEN tipo_operacion = 'Colocacion Interbancaria' THEN monto_usd ELSE 0 END) as fondeo_interbancario_usd,
            SUM(CASE WHEN tipo_operacion IN ('Compra Divisas BCV', 'Inversion Corto Plazo') THEN monto_usd ELSE 0 END) as inversiones_usd
        FROM operaciones_tesoreria
        GROUP BY mes
        ORDER BY mes
    """)
    flow_rows = cursor.fetchall()
    
    conn.close()
    
    return {
        "evolucion": [{
            "fecha": r["fecha_inicio"],
            "depositos_ves": round(r["depositos_ves"], 2),
            "depositos_usd": round(r["depositos_usd"], 2),
            "disponible_ves": round(r["disponible_ves"], 2),
            "encaje_ves": round(r["encaje_ves"], 2),
            "tasa_liquidez": round(r["tasa_liq"] * 100, 2)
        } for r in liq_rows],
        
        "tesoreria": [{
            "operacion": r["tipo_operacion"],
            "cantidad": r["cantidad"],
            "volumen_usd": round(r["volumen_usd"], 2),
            "tasa_promedio": round(r["tasa_promedio"], 2)
        } for r in ops_rows],
        
        "flujo_mensual": [{
            "mes": r["mes"],
            "fondeo_usd": round(r["fondeo_interbancario_usd"], 2),
            "inversiones_usd": round(r["inversiones_usd"], 2)
        } for r in flow_rows]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
