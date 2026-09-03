import sqlite3
import random
import datetime
import math
import os
import sys
import calendar

# Definición de constantes para la simulación
START_DATE = datetime.date(2023, 6, 19)
END_DATE = datetime.date(2026, 6, 19)
TOTAL_CLIENTS = 10000
INITIAL_ACTIVE_CLIENTS = 7000
DB_FILE = "bank_data.db"
SQL_BACKUP_FILE = "database/backup_postgres.sql"

# Listas de datos para generación de nombres realistas en Venezuela
FIRST_NAMES_MALE = ["Juan", "José", "Carlos", "Luis", "Manuel", "Francisco", "Jesús", "Miguel", "Ángel", "Pedro", 
                    "Daniel", "Alexander", "David", "Rafael", "Javier", "Edgar", "Franklin", "Richard", "Jorge", "Gustavo"]
FIRST_NAMES_FEMALE = ["María", "Carmen", "Ana", "Josefa", "Isabel", "Yulitza", "Patricia", "Elizabeth", "Rosa", "Luisa",
                      "Daniela", "Gabriela", "Mariela", "Adriana", "Carolina", "Beatriz", "Yusbelly", "Coromoto", "Genesis", "Andreina"]
LAST_NAMES = ["Rodríguez", "González", "Hernández", "Martínez", "Pérez", "García", "Díaz", "Sánchez", "Ramírez", "Flores",
              "Gómez", "Torres", "Álvarez", "Ruiz", "Castillo", "Mejías", "Silva", "Rivas", "Salazar", "Rondón", "Machado"]
VENEZUELAN_STATES = ["Distrito Capital", "Miranda", "Zulia", "Carabobo", "Aragua", "Lara", "Bolívar", "Anzoátegui", 
                     "Táchira", "Falcón", "Monagas", "Sucre", "Portuguesa", "Mérida", "Yaracuy", "Barinas", 
                     "Guárico", "Trujillo", "Cojedes", "Apure", "Nueva Esparta", "Vargas", "Delta Amacuro", "Amazonas"]
ECONOMIC_ACTIVITIES = ["Empleado Privado", "Empleado Público", "Independiente/Profesional", "Empresario/Comerciante", "Jubilado", "Desempleado"]
RISK_LEVELS = ["Bajo", "Medio", "Alto"]
CHANNELS_VES = ["Pago Movil", "Punto de Venta", "Banca Movil", "Banca en Linea", "ATM", "Taquilla"]
CHANNELS_USD = ["Banca en Linea", "Taquilla"]
ERROR_CODES = ["ERR_TIMEOUT", "ERR_CONEXION_HOST", "ERR_FALLA_TAQUILLA"]

def init_db(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        tipo_documento TEXT CHECK(tipo_documento IN ('V', 'E', 'J')) NOT NULL,
        cedula TEXT UNIQUE NOT NULL,
        fecha_nacimiento DATE NOT NULL,
        genero TEXT CHECK(genero IN ('M', 'F')) NOT NULL,
        estado_civil TEXT CHECK(estado_civil IN ('Soltero', 'Casado', 'Divorciado', 'Viudo')) NOT NULL,
        email TEXT NOT NULL,
        telefono TEXT NOT NULL,
        estado_residencia TEXT NOT NULL,
        fecha_registro DATE NOT NULL,
        estado_cliente TEXT CHECK(estado_cliente IN ('Activo', 'Inactivo')) NOT NULL,
        fecha_desafiliacion DATE,
        score_credito INTEGER NOT NULL,
        ingresos_mensuales_usd REAL NOT NULL,
        actividad_economica TEXT NOT NULL,
        nivel_riesgo_interno TEXT CHECK(nivel_riesgo_interno IN ('Bajo', 'Medio', 'Alto')) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        numero_cuenta TEXT UNIQUE NOT NULL,
        tipo_cuenta TEXT CHECK(tipo_cuenta IN ('Corriente', 'Ahorros')) NOT NULL,
        moneda TEXT CHECK(moneda IN ('VES', 'USD')) NOT NULL,
        fecha_apertura DATE NOT NULL,
        saldo_actual REAL NOT NULL,
        estado_cuenta TEXT CHECK(estado_cuenta IN ('Activa', 'Bloqueada', 'Cerrada')) NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuenta_id INTEGER NOT NULL,
        tipo_transaccion TEXT CHECK(tipo_transaccion IN ('Pago Movil', 'Transferencia', 'Retiro ATM', 'Compra Punto Venta', 'Deposito Taquilla', 'Retiro Taquilla')) NOT NULL,
        monto REAL NOT NULL,
        monto_usd REAL NOT NULL,
        tasa_cambio REAL NOT NULL,
        fecha_hora TIMESTAMP NOT NULL,
        canal TEXT NOT NULL,
        estado TEXT CHECK(estado IN ('Completada', 'Rechazada', 'Fallida')) NOT NULL,
        codigo_error TEXT,
        es_fraude INTEGER DEFAULT 0,
        latitud REAL,
        longitud REAL,
        dispositivo_id TEXT,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS creditos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        monto_aprobado_usd REAL NOT NULL,
        tasa_interes_anual REAL NOT NULL,
        plazo_meses INTEGER NOT NULL,
        fecha_otorgamiento DATE NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        tipo_credito TEXT CHECK(tipo_credito IN ('Consumo', 'Comercial', 'Microcredito', 'Hipotecario')) NOT NULL,
        estado TEXT CHECK(estado IN ('Vigente', 'Pagado', 'Vencido', 'En Litigio')) NOT NULL,
        saldo_pendiente_usd REAL NOT NULL,
        cuotas_totales INTEGER NOT NULL,
        cuotas_pagadas INTEGER NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos_creditos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credito_id INTEGER NOT NULL,
        monto_pago_usd REAL NOT NULL,
        fecha_pago DATE NOT NULL,
        dias_atraso INTEGER NOT NULL,
        estado_pago TEXT CHECK(estado_pago IN ('A Tiempo', 'Atrasado', 'No Pagado')) NOT NULL,
        FOREIGN KEY (credito_id) REFERENCES creditos(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS indicadores_macro (
        fecha DATE PRIMARY KEY,
        tasa_bcv_usd_ves REAL NOT NULL,
        tasa_paralela_usd_ves REAL NOT NULL,
        inflacion_mensual_pct REAL NOT NULL,
        variacion_pib_mensual_pct REAL NOT NULL,
        tasa_activa_ves_anual REAL NOT NULL,
        tasa_pasiva_ves_anual REAL NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumen_liquidez_diario (
        fecha DATE PRIMARY KEY,
        total_depositos_ves REAL NOT NULL,
        total_depositos_usd REAL NOT NULL,
        total_creditos_ves REAL NOT NULL,
        total_creditos_usd REAL NOT NULL,
        disponible_caja_ves REAL NOT NULL,
        encaje_legal_bcv_ves REAL NOT NULL,
        tasa_liquidez REAL NOT NULL,
        brecha_liquidez_usd REAL NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operaciones_tesoreria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE NOT NULL,
        tipo_operacion TEXT CHECK(tipo_operacion IN ('Colocacion Interbancaria', 'Compra Divisas BCV', 'Venta Divisas', 'Inversion Corto Plazo')) NOT NULL,
        monto_usd REAL NOT NULL,
        tasa_anual REAL NOT NULL,
        plazo_dias INTEGER NOT NULL,
        contraparte TEXT NOT NULL
    );
    """)

    # Índices para mejorar rendimiento de queries y entrenamiento de modelos
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacciones_cuenta ON transacciones(cuenta_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON transacciones(fecha_hora);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_cedula ON clientes(cedula);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_creditos_cliente ON creditos(cliente_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pagos_credito ON pagos_creditos(credito_id);")
    
    conn.commit()

# Generación de variables macroeconómicas reales (Junio 2023 - Junio 2026)
def generate_macro_data():
    """
    Genera serie de tiempo macroeconómica diaria fiel a la historia venezolana:
    - Anclas mensuales oficiales de tasa BCV y mercado paralelo (Monitor Dólar / EnParaleloVzla).
    - Reflejo fiel del anclaje cambiario en ~36.40 Bs/$ durante el primer semestre de 2024,
      la posterior apertura de la brecha cambiaria en Q4 2024 (llegando a 20-25%+), y proyección 2025-2026.
    - Tasas de inflación mensual reales (INPC BCV / OVF) y crecimiento de PIB.
    - Interpolación suave día a día con inercia de fin de semana para la tasa oficial BCV.
    """
    macro_anchors = {
        # (year, month): (bcv, paralelo, inflacion_mensual_pct, pib_mensual_pct, tasa_activa_pct, tasa_pasiva_pct)
        (2023, 6): (27.28, 29.45, 6.2, -0.2, 38.5, 14.0),
        (2023, 7): (29.50, 31.75, 7.2, 0.1, 38.2, 14.2),
        (2023, 8): (32.59, 34.10, 7.4, -0.5, 38.0, 14.5),
        (2023, 9): (34.42, 35.70, 6.0, 0.4, 37.8, 14.0),
        (2023, 10): (35.15, 37.15, 5.9, 0.6, 37.5, 13.8),
        (2023, 11): (35.48, 37.30, 3.5, 1.1, 37.0, 13.5),
        (2023, 12): (35.93, 39.50, 3.9, 2.0, 36.8, 13.5),
        (2024, 1): (36.26, 38.40, 1.7, 0.2, 36.5, 13.0),
        (2024, 2): (36.15, 38.10, 1.2, 0.5, 36.2, 12.8),
        (2024, 3): (36.31, 38.60, 1.2, 0.8, 36.0, 12.5),
        (2024, 4): (36.45, 39.20, 1.5, 1.0, 36.0, 12.5),
        (2024, 5): (36.53, 39.95, 1.5, 1.2, 35.8, 12.5),
        (2024, 6): (36.38, 40.50, 1.0, 1.3, 35.5, 12.2),
        (2024, 7): (36.61, 41.80, 0.7, 1.4, 35.2, 12.0),
        (2024, 8): (36.65, 43.70, 1.4, 0.9, 35.5, 12.0),
        (2024, 9): (36.90, 44.50, 0.8, 1.2, 36.0, 12.5),
        (2024, 10): (42.56, 51.20, 1.4, 1.5, 37.2, 13.0),
        (2024, 11): (47.30, 55.80, 2.1, 1.8, 38.5, 13.5),
        (2024, 12): (51.80, 64.50, 3.5, 2.5, 39.8, 14.0),
        (2025, 1): (54.20, 66.50, 2.2, 0.5, 39.5, 13.8),
        (2025, 2): (56.80, 69.20, 2.0, 0.6, 39.0, 13.5),
        (2025, 3): (59.50, 72.00, 1.9, 0.8, 38.8, 13.5),
        (2025, 4): (62.30, 75.40, 1.8, 1.0, 38.5, 13.2),
        (2025, 5): (65.50, 79.00, 2.1, 1.1, 38.5, 13.2),
        (2025, 6): (69.20, 83.50, 2.3, 1.3, 38.2, 13.0),
        (2025, 7): (73.00, 87.80, 2.0, 1.2, 38.0, 13.0),
        (2025, 8): (77.50, 93.00, 2.2, 1.1, 38.2, 13.2),
        (2025, 9): (82.00, 98.50, 2.4, 1.4, 38.5, 13.5),
        (2025, 10): (87.80, 106.00, 2.8, 1.6, 39.2, 13.8),
        (2025, 11): (94.50, 115.00, 3.6, 2.0, 40.5, 14.2),
        (2025, 12): (103.00, 126.00, 4.5, 2.8, 42.0, 15.0),
        (2026, 1): (107.50, 130.00, 2.2, 0.6, 41.5, 14.5),
        (2026, 2): (112.00, 135.50, 2.0, 0.8, 41.0, 14.2),
        (2026, 3): (117.20, 141.00, 2.1, 1.0, 40.8, 14.0),
        (2026, 4): (123.00, 148.00, 2.3, 1.2, 40.5, 14.0),
        (2026, 5): (129.50, 156.00, 2.5, 1.4, 40.5, 14.0),
        (2026, 6): (136.00, 164.00, 2.4, 1.5, 40.0, 13.8),
        (2026, 7): (142.00, 172.00, 2.4, 1.5, 40.0, 13.8)
    }

    macro_records = {}
    current_date = START_DATE
    delta = datetime.timedelta(days=1)
    
    last_weekday_bcv = None
    last_weekday_par = None
    
    while current_date <= END_DATE:
        year, month = current_date.year, current_date.month
        day = current_date.day
        days_in_m = calendar.monthrange(year, month)[1]
        
        next_key = (year + 1, 1) if month == 12 else (year, month + 1)
        cur_anchor = macro_anchors.get((year, month))
        nxt_anchor = macro_anchors.get(next_key, cur_anchor)
        
        # Fracción transcurrida del mes [0.0, 1.0]
        t = (day - 1) / max(1, days_in_m - 1)
        
        base_bcv = cur_anchor[0] + t * (nxt_anchor[0] - cur_anchor[0])
        base_par = cur_anchor[1] + t * (nxt_anchor[1] - cur_anchor[1])
        base_inf = cur_anchor[2]
        base_pib = cur_anchor[3]
        base_act = cur_anchor[4] + t * (nxt_anchor[4] - cur_anchor[4])
        base_pas = cur_anchor[5] + t * (nxt_anchor[5] - cur_anchor[5])
        
        weekday = current_date.weekday()
        if weekday < 5:  # Lunes a Viernes: mercado activo
            noise_bcv = random.uniform(-0.0015, 0.0015) * base_bcv
            bcv_val = round(base_bcv + noise_bcv, 4)
            last_weekday_bcv = bcv_val
            
            noise_par = random.uniform(-0.006, 0.006) * base_par
            par_val = round(base_par + noise_par, 4)
            # Garantizar prima mínima del mercado paralelo
            par_val = max(round(bcv_val * 1.025, 4), par_val)
            last_weekday_par = par_val
        else:  # Fines de semana: tasa oficial BCV se mantiene fija al cierre de viernes
            bcv_val = last_weekday_bcv if last_weekday_bcv else round(base_bcv, 4)
            par_val = last_weekday_par if last_weekday_par else round(base_par, 4)
            
        act_val = round(base_act + random.uniform(-0.1, 0.1), 2)
        pas_val = round(base_pas + random.uniform(-0.05, 0.05), 2)
        
        macro_records[current_date.strftime("%Y-%m-%d")] = {
            "bcv": bcv_val,
            "paralela": par_val,
            "inflacion": base_inf,
            "pib": base_pib,
            "activa": act_val,
            "pasiva": pas_val
        }
        current_date += delta
        
    return macro_records

def generate_demographics(num_clients):
    clients_data = []
    
    # Generar cedulas únicas
    cedula_set = set()
    while len(cedula_set) < num_clients:
        rand = random.random()
        if rand < 0.90:
            prefix = "V"
            num = random.randint(7000000, 32000000)
        elif rand < 0.95:
            prefix = "E"
            num = random.randint(80000000, 85000000)
        else:
            prefix = "J"
            num = random.randint(100000000, 499999999)
        cedula_set.add(f"{prefix}-{num}")
    
    cedulas = list(cedula_set)
    
    for i in range(num_clients):
        gender = "M" if random.random() < 0.5 else "F"
        if gender == "M":
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES) + " " + random.choice(LAST_NAMES)
        
        cedula = cedulas[i]
        is_juridico = cedula.startswith("J")
        
        birth_year = random.randint(1945, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        dob = datetime.date(birth_year, birth_month, birth_day)
        
        if is_juridico:
            first_name = "Corporación " + first_name
            last_name = random.choice(["C.A.", "S.A.", "S.R.L."])
            dob = datetime.date(random.randint(1995, 2021), birth_month, birth_day)
            
        civil_status = random.choice(["Soltero", "Casado", "Divorciado", "Viudo"]) if not is_juridico else "Soltero"
        email = f"{first_name.lower().replace(' ', '')}.{last_name.split()[0].lower()}@gmail.com"
        phone = f"04{random.choice(['14', '24', '16', '26', '12'])}-{random.randint(1000000, 9999999)}"
        state = random.choice(VENEZUELAN_STATES)
        
        # Fecha de registro escalonada
        if i < INITIAL_ACTIVE_CLIENTS:
            reg_date = START_DATE
        else:
            days_offset = random.randint(1, (END_DATE - START_DATE).days)
            reg_date = START_DATE + datetime.timedelta(days=days_offset)
            
        status = "Activo"
        churn_date = None
        # Churn realista (~4% total)
        if random.random() < 0.04 and reg_date < END_DATE - datetime.timedelta(days=180):
            status = "Inactivo"
            days_churn = random.randint(180, (END_DATE - reg_date).days)
            churn_date = reg_date + datetime.timedelta(days=days_churn)
            
        score = int(random.normalvariate(620, 95))
        score = max(300, min(850, score))
        
        # Ingresos mensuales base en USD acordes a la estructura socioeconómica de Venezuela
        if is_juridico:
            income = round(random.lognormvariate(8.2, 0.8), 2)
            income = max(2000.0, min(40000.0, income))
            activity = "Empresario/Comerciante"
        else:
            activity = random.choice(ECONOMIC_ACTIVITIES)
            if activity == "Jubilado":
                # Pensión IVSS + Bono contra la Guerra Económica ($120 - $220)
                income = round(random.uniform(120.0, 220.0), 2)
            elif activity == "Empleado Público":
                # Salario base + Cestaticket ($40) + Bono de Guerra ($90-$120)
                income = round(random.uniform(140.0, 350.0), 2)
            elif activity == "Empleado Privado":
                income = round(random.lognormvariate(5.8, 0.4), 2)
                income = max(180.0, min(850.0, income))
            elif activity == "Independiente/Profesional":
                income = round(random.lognormvariate(6.5, 0.5), 2)
                income = max(350.0, min(2200.0, income))
            elif activity == "Empresario/Comerciante":
                income = round(random.lognormvariate(7.6, 0.6), 2)
                income = max(1500.0, min(10000.0, income))
            else: # Desempleado (ingresos informales o remesas esporádicas)
                income = round(random.uniform(30.0, 90.0), 2)
                score = max(300, score - 140)
                
        # Nivel de riesgo interno determinado por ingresos y score
        if score > 680 and income > 800:
            risk = "Bajo"
        elif score < 520 or income < 180:
            risk = "Alto"
        else:
            risk = "Medio"
            
        clients_data.append({
            "id": i + 1,
            "nombre": first_name,
            "apellido": last_name,
            "tipo_documento": cedula[0],
            "cedula": cedula,
            "fecha_nacimiento": dob.strftime("%Y-%m-%d"),
            "genero": gender,
            "estado_civil": civil_status,
            "email": email,
            "telefono": phone,
            "estado_residencia": state,
            "fecha_registro": reg_date.strftime("%Y-%m-%d"),
            "estado_cliente": status,
            "fecha_desafiliacion": churn_date.strftime("%Y-%m-%d") if churn_date else None,
            "score_credito": score,
            "ingresos_mensuales_usd": income,
            "actividad_economica": activity,
            "nivel_riesgo_interno": risk
        })
    return clients_data

def generate_accounts(clients):
    accounts = []
    account_id = 1
    bcv_rate_start = 28.67
    
    for c in clients:
        # Todos los clientes tienen cuenta en VES
        ves_type = random.choice(["Corriente", "Ahorros"])
        ves_acct = f"0105{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(1000000000, 9999999999)}"
        
        # Saldo inicial coherente con ingresos mensuales (20% a 65% de un mes de ingreso)
        init_balance_usd = c["ingresos_mensuales_usd"] * random.uniform(0.20, 0.65)
        init_balance_ves = init_balance_usd * bcv_rate_start
        
        acct_status = "Activa" if c["estado_cliente"] == "Activo" else "Cerrada"
        
        accounts.append({
            "id": account_id,
            "cliente_id": c["id"],
            "numero_cuenta": ves_acct,
            "tipo_cuenta": ves_type,
            "moneda": "VES",
            "fecha_apertura": c["fecha_registro"],
            "saldo_actual": round(init_balance_ves, 2),
            "estado_cuenta": acct_status
        })
        account_id += 1
        
        # Cuentas en USD (Custodia en divisas)
        prob_usd = 0.35
        if c["ingresos_mensuales_usd"] > 1000 or c["tipo_documento"] == "J":
            prob_usd = 0.85
        elif c["ingresos_mensuales_usd"] < 200:
            prob_usd = 0.08
            
        if random.random() < prob_usd:
            usd_type = "Corriente"
            usd_acct = f"0105{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(1000000000, 9999999999)}"
            init_bal_usd = c["ingresos_mensuales_usd"] * random.uniform(0.15, 0.50)
            
            accounts.append({
                "id": account_id,
                "cliente_id": c["id"],
                "numero_cuenta": usd_acct,
                "tipo_cuenta": usd_type,
                "moneda": "USD",
                "fecha_apertura": c["fecha_registro"],
                "saldo_actual": round(init_bal_usd, 2),
                "estado_cuenta": acct_status
            })
            account_id += 1
            
    return accounts

def generate_all_data(db_conn):
    print("Iniciando generación de datos calibrados...")
    
    # 1. Generar Macro
    print("1/6 Generando indicadores macroeconómicos reales de Venezuela...")
    macro_data = generate_macro_data()
    
    # 2. Generar Clientes y Cuentas
    print("2/6 Generando perfiles socioeconómicos de clientes y cuentas...")
    clients = generate_demographics(TOTAL_CLIENTS)
    accounts = generate_accounts(clients)
    
    cursor = db_conn.cursor()
    
    cursor.executemany("""
    INSERT INTO clientes (id, nombre, apellido, tipo_documento, cedula, fecha_nacimiento, genero, estado_civil, email, telefono, estado_residencia, fecha_registro, estado_cliente, fecha_desafiliacion, score_credito, ingresos_mensuales_usd, actividad_economica, nivel_riesgo_interno)
    VALUES (:id, :nombre, :apellido, :tipo_documento, :cedula, :fecha_nacimiento, :genero, :estado_civil, :email, :telefono, :estado_residencia, :fecha_registro, :estado_cliente, :fecha_desafiliacion, :score_credito, :ingresos_mensuales_usd, :actividad_economica, :nivel_riesgo_interno)
    """, clients)
    
    cursor.executemany("""
    INSERT INTO cuentas (id, cliente_id, numero_cuenta, tipo_cuenta, moneda, fecha_apertura, saldo_actual, estado_cuenta)
    VALUES (:id, :cliente_id, :numero_cuenta, :tipo_cuenta, :moneda, :fecha_apertura, :saldo_actual, :estado_cuenta)
    """, accounts)
    
    db_conn.commit()
    
    # Estructura en memoria para balance y estados
    acct_map = {}
    acct_ids_ves = []
    acct_ids_usd = []
    
    for acct in accounts:
        acct_map[acct["id"]] = {
            "cliente_id": acct["cliente_id"],
            "moneda": acct["moneda"],
            "saldo": acct["saldo_actual"],
            "estado": acct["estado_cuenta"],
            "fecha_apertura": datetime.datetime.strptime(acct["fecha_apertura"], "%Y-%m-%d").date()
        }
        if acct["moneda"] == "VES":
            acct_ids_ves.append(acct["id"])
        else:
            acct_ids_usd.append(acct["id"])
            
    clients_map = {c["id"]: c for c in clients}
    
    # Asignación de facilidades de crédito / sobregiro autorizado:
    # Empresas y clientes VIP (score >= 700 y bajo riesgo) cuentan con línea de sobregiro
    credit_facilities_usd = {}
    for c in clients:
        cid = c["id"]
        is_jur = c["cedula"].startswith("J")
        if is_jur:
            credit_facilities_usd[cid] = round(c["ingresos_mensuales_usd"] * 1.5, 2)
        elif c["score_credito"] >= 700 and c["nivel_riesgo_interno"] == "Bajo":
            credit_facilities_usd[cid] = round(c["ingresos_mensuales_usd"] * 0.75, 2)
        else:
            credit_facilities_usd[cid] = 0.0
            
    # 3. Simulación diaria (Transacciones, Créditos, Liquidez)
    print("3/6 Ejecutando simulación diaria financieramente coherente (2023 - 2026)...")
    
    current_date = START_DATE
    delta = datetime.timedelta(days=1)
    
    tx_batch = []
    loans_list = []
    loan_payments_list = []
    daily_liquidity_list = []
    treasury_ops_list = []
    
    loan_id_counter = 1
    payment_id_counter = 1
    treasury_id_counter = 1
    
    active_loans = {}
    
    # Fechas de fallas operacionales específicas
    outage_dates = {
        "2023-11-20": 0.42, # Caída enlace nacional CANTV
        "2024-04-15": 0.35, # Datacenter secundario
        "2024-12-10": 0.48, # Sobrecarga por pagos navideños
        "2025-06-03": 0.30, # Falla de red transaccional
        "2025-12-24": 0.40, # Falla procesamiento tarjetas
        "2026-03-12": 0.28  # Mantenimiento Core Bancario
    }
    
    disponible_caja_ves = 25000000.0
    
    while current_date <= END_DATE:
        date_str = current_date.strftime("%Y-%m-%d")
        macro = macro_data[date_str]
        bcv = macro["bcv"]
        paralelo = macro["paralela"]
        
        day_of_month = current_date.day
        month = current_date.month
        weekday = current_date.weekday()
        
        active_accts_ves = [aid for aid in acct_ids_ves if acct_map[aid]["fecha_apertura"] <= current_date and acct_map[aid]["estado"] == "Activa"]
        active_accts_usd = [aid for aid in acct_ids_usd if acct_map[aid]["fecha_apertura"] <= current_date and acct_map[aid]["estado"] == "Activa"]
        
        # --- FLUJOS DE ENTRADA REGULARES (Depósitos de Nómina, Honorarios, Ventas) ---
        # 1. Quincenas (días 15 y 30): Empleados y Jubilados
        is_quincena = (day_of_month == 15) or (day_of_month == 30) or (month == 2 and day_of_month == 28)
        if is_quincena:
            for aid in active_accts_ves:
                info = acct_map[aid]
                c = clients_map[info["cliente_id"]]
                if c["actividad_economica"] in ["Empleado Privado", "Empleado Público", "Jubilado"]:
                    salary_usd = c["ingresos_mensuales_usd"] / 2.0
                    if c["actividad_economica"] == "Jubilado":
                        if day_of_month == 30: continue
                        salary_usd = c["ingresos_mensuales_usd"]
                    salary_ves = salary_usd * bcv
                    info["saldo"] += salary_ves
                    tx_batch.append((
                        None, aid, "Deposito Taquilla", round(salary_ves, 2), round(salary_usd, 2), bcv,
                        f"{date_str} 08:30:00", "Taquilla", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))
                    
        # 2. Independientes / Profesionales: cobros de honorarios semanales (días 7, 14, 21, 28)
        if day_of_month in [7, 14, 21, 28]:
            for aid in active_accts_ves:
                info = acct_map[aid]
                c = clients_map[info["cliente_id"]]
                if c["actividad_economica"] == "Independiente/Profesional":
                    fee_usd = (c["ingresos_mensuales_usd"] * 0.25) * random.uniform(0.85, 1.15)
                    fee_ves = fee_usd * bcv
                    info["saldo"] += fee_ves
                    tx_batch.append((
                        None, aid, "Transferencia", round(fee_ves, 2), round(fee_usd, 2), bcv,
                        f"{date_str} 11:15:00", "Banca en Linea", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))
                    
        # 3. Empresarios / Comercios / Jurídicos: depósitos comerciales frecuentes (cada 3 días)
        if day_of_month % 3 == 0:
            for aid in active_accts_ves:
                info = acct_map[aid]
                c = clients_map[info["cliente_id"]]
                if c["actividad_economica"] == "Empresario/Comerciante" or c["cedula"].startswith("J"):
                    biz_usd = (c["ingresos_mensuales_usd"] * 0.10) * random.uniform(0.8, 1.3)
                    biz_ves = biz_usd * bcv
                    info["saldo"] += biz_ves
                    tx_batch.append((
                        None, aid, "Deposito Taquilla", round(biz_ves, 2), round(biz_usd, 2), bcv,
                        f"{date_str} 16:45:00", "Taquilla", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))
                    
        # 4. Desempleados: remesas y ayudas familiares (días 10 y 24)
        if day_of_month in [10, 24]:
            for aid in active_accts_ves:
                info = acct_map[aid]
                c = clients_map[info["cliente_id"]]
                if c["actividad_economica"] == "Desempleado":
                    rem_usd = (c["ingresos_mensuales_usd"] * 0.50) * random.uniform(0.9, 1.1)
                    rem_ves = rem_usd * bcv
                    info["saldo"] += rem_ves
                    tx_batch.append((
                        None, aid, "Transferencia", round(rem_ves, 2), round(rem_usd, 2), bcv,
                        f"{date_str} 14:20:00", "Banca Movil", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))

        # --- TRANSACCIONES DIARIAS EN BOLÍVARES (VES) ---
        outage_pct = outage_dates.get(date_str, 0.001)
        
        # Separar cuentas con liquidez vs cuentas con saldo bajo o agotado
        pos_accts_ves = [aid for aid in active_accts_ves if acct_map[aid]["saldo"] > 0]
        zero_accts_ves = [aid for aid in active_accts_ves if acct_map[aid]["saldo"] <= 0]
        
        tx_prob = 0.22
        if is_quincena: tx_prob *= 1.4
        if month == 12: tx_prob *= 1.6
        if weekday in [5, 6]: tx_prob *= 1.15
        
        # Cuentas con saldo tienen alta actividad natural
        num_pos = int(len(pos_accts_ves) * min(0.60, tx_prob))
        # Cuentas sin saldo transaccionan raramente (intentos accidentales o uso de sobregiro)
        num_zero = int(len(zero_accts_ves) * 0.008)
        
        transacting_ves = random.sample(pos_accts_ves, k=min(num_pos, len(pos_accts_ves))) + random.sample(zero_accts_ves, k=min(num_zero, len(zero_accts_ves)))
        random.shuffle(transacting_ves)
        
        for aid in transacting_ves:
            info = acct_map[aid]
            c = clients_map[info["cliente_id"]]
            cid = c["id"]
            
            rand = random.random()
            if rand < 0.55:
                chan = "Pago Movil"
                txtype = "Pago Movil"
                amt_usd = random.uniform(1.5, 25.0)
            elif rand < 0.85:
                chan = "Punto de Venta"
                txtype = "Compra Punto Venta"
                amt_usd = random.uniform(4.0, 60.0)
            elif rand < 0.95:
                chan = "Banca Movil" if random.random() < 0.7 else "Banca en Linea"
                txtype = "Transferencia"
                max_tr = max(20.0, min(500.0, c["ingresos_mensuales_usd"] * 0.40))
                amt_usd = random.uniform(15.0, max_tr)
            elif rand < 0.98:
                chan = "ATM"
                txtype = "Retiro ATM"
                amt_usd = random.uniform(5.0, 35.0)
            else:
                chan = "Taquilla"
                txtype = "Retiro Taquilla" if random.random() < 0.6 else "Deposito Taquilla"
                amt_usd = random.uniform(30.0, 250.0)
                
            amt_ves = amt_usd * bcv
            
            if txtype == "Deposito Taquilla":
                info["saldo"] += amt_ves
                status = "Completada"
                err = None
            else:
                # Egresos: evaluar saldo propio + línea de crédito / sobregiro disponible
                credit_limit_usd = credit_facilities_usd.get(cid, 0.0)
                # Si tiene un préstamo activo de consumo/comercial, cuenta con facilidad crediticia
                has_active_loan = any(l["cliente_id"] == cid and l["estado"] == "Vigente" for l in active_loans.values())
                if has_active_loan:
                    credit_limit_usd = max(credit_limit_usd, c["ingresos_mensuales_usd"] * 0.6)
                    
                credit_limit_ves = credit_limit_usd * bcv
                available_funds_ves = info["saldo"] + credit_limit_ves
                
                if available_funds_ves >= amt_ves:
                    # Fondo suficiente o cubierto por crédito
                    if random.random() < outage_pct:
                        status = "Fallida"
                        err = random.choice(ERROR_CODES)
                    else:
                        status = "Completada"
                        err = None
                        info["saldo"] -= amt_ves
                else:
                    # Sin respaldo financiero ni crédito: Rechazo por fondos insuficientes
                    status = "Rechazada"
                    err = "ERR_FONDO_INSUFICIENTE"
                    
            # Fraude operativo
            is_fraud = 0
            if status == "Completada" and txtype in ["Pago Movil", "Compra Punto Venta", "Transferencia"]:
                hour = random.randint(0, 23)
                if hour in [1, 2, 3, 4] and amt_usd > (c["ingresos_mensuales_usd"] * 0.45) and random.random() < 0.07:
                    is_fraud = 1
            else:
                hour = random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22])
                
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            time_str = f"{date_str} {hour:02d}:{minute:02d}:{second:02d}"
            
            lat = 10.4806 + random.uniform(-0.15, 0.15)
            lon = -66.9036 + random.uniform(-0.15, 0.15)
            if is_fraud:
                lat += random.choice([-2.5, 3.5, 1.2])
                lon += random.choice([-4.0, 2.8, -1.5])
                
            dev_id = f"DEV_{hash(c['cedula']) % 1000000:06d}" if not is_fraud else f"DEV_{random.randint(100000, 999999):06d}"
            
            tx_batch.append((
                None, aid, txtype, round(amt_ves, 2), round(amt_usd, 2), bcv,
                time_str, chan, status, err, is_fraud, round(lat, 4), round(lon, 4), dev_id
            ))
            
        # --- TRANSACCIONES DIARIAS EN DÓLARES (USD) ---
        num_tx_usd = int(len(active_accts_usd) * 0.06)
        transacting_usd = random.sample(active_accts_usd, k=num_tx_usd) if num_tx_usd < len(active_accts_usd) else active_accts_usd
        
        for aid in transacting_usd:
            info = acct_map[aid]
            c = clients_map[info["cliente_id"]]
            
            rand = random.random()
            if rand < 0.70:
                chan = "Banca en Linea"
                txtype = "Transferencia"
                amt_usd = random.uniform(20.0, min(600.0, c["ingresos_mensuales_usd"] * 0.50))
            elif rand < 0.85:
                chan = "Taquilla"
                txtype = "Deposito Taquilla"
                amt_usd = random.uniform(50.0, 400.0)
            else:
                chan = "Taquilla"
                txtype = "Retiro Taquilla"
                amt_usd = random.uniform(30.0, 300.0)
                
            if txtype == "Deposito Taquilla":
                info["saldo"] += amt_usd
                status = "Completada"
                err = None
            else:
                if info["saldo"] >= amt_usd:
                    if random.random() < outage_pct:
                        status = "Fallida"
                        err = random.choice(ERROR_CODES)
                    else:
                        info["saldo"] -= amt_usd
                        status = "Completada"
                        err = None
                else:
                    status = "Rechazada"
                    err = "ERR_FONDO_INSUFICIENTE"
                    
            hour = random.randint(8, 18)
            time_str = f"{date_str} {hour:02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
            lat = 10.4806 + random.uniform(-0.1, 0.1)
            lon = -66.9036 + random.uniform(-0.1, 0.1)
            dev_id = "WEB_PORTAL" if chan == "Banca en Linea" else "TELLER_CARACAS"
            
            tx_batch.append((
                None, aid, txtype, round(amt_usd, 2), round(amt_usd, 2), bcv,
                time_str, chan, status, err, 0, round(lat, 4), round(lon, 4), dev_id
            ))
            
        # --- CARTERA DE CRÉDITO: Otorgamiento Calibrado (~1,000 préstamos en 3 años) ---
        # En días hábiles bancarios se aprueban entre 1 y 2 préstamos para clientes elegibles
        if weekday < 5 and random.random() < 0.90:
            num_new_loans = 1 if random.random() < 0.70 else 2
            eligible_clients = [c for c in clients if c["estado_cliente"] == "Activo" and c["score_credito"] > 580 and c["fecha_registro"] <= date_str]
            
            for _ in range(num_new_loans):
                if eligible_clients:
                    c = random.choice(eligible_clients)
                    already_has_loan = any(l["cliente_id"] == c["id"] and l["estado"] in ["Vigente", "Vencido"] for l in active_loans.values())
                    if not already_has_loan:
                        plazo = random.choice([12, 18, 24, 36])
                        loan_amt_usd = round(c["ingresos_mensuales_usd"] * random.uniform(2.5, 6.0), 2)
                        loan_amt_usd = max(500.0, min(25000.0, loan_amt_usd))
                        
                        tasa = round(macro["activa"] + random.uniform(-2.5, 2.5), 2)
                        fecha_ven = current_date + datetime.timedelta(days=plazo*30)
                        tipo_c = random.choice(["Consumo", "Comercial", "Microcredito"])
                        if loan_amt_usd > 8000 or c["cedula"].startswith("J"):
                            tipo_c = "Comercial"
                            
                        rate_m = (tasa / 100) / 12
                        cuota_mensual = (loan_amt_usd * rate_m) / (1 - (1 + rate_m)**(-plazo))
                        
                        new_loan = {
                            "id": loan_id_counter,
                            "cliente_id": c["id"],
                            "monto_aprobado_usd": loan_amt_usd,
                            "tasa_interes_anual": tasa,
                            "plazo_meses": plazo,
                            "fecha_otorgamiento": date_str,
                            "fecha_vencimiento": fecha_ven.strftime("%Y-%m-%d"),
                            "tipo_credito": tipo_c,
                            "estado": "Vigente",
                            "saldo_pendiente_usd": loan_amt_usd,
                            "cuotas_totales": plazo,
                            "cuotas_pagadas": 0,
                            "dia_pago": day_of_month,
                            "cuota_mensual": cuota_mensual
                        }
                        loans_list.append(new_loan)
                        active_loans[loan_id_counter] = new_loan
                        loan_id_counter += 1
                        
                        # Desembolso del crédito
                        c_accts = [aid for aid, ac in acct_map.items() if ac["cliente_id"] == c["id"]]
                        usd_acct = [aid for aid in c_accts if acct_map[aid]["moneda"] == "USD"]
                        if usd_acct:
                            ac_id = usd_acct[0]
                            acct_map[ac_id]["saldo"] += loan_amt_usd
                            tx_batch.append((
                                None, ac_id, "Deposito Taquilla", loan_amt_usd, loan_amt_usd, bcv,
                                f"{date_str} 10:00:00", "Taquilla", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                            ))
                        else:
                            ac_id = [aid for aid in c_accts if acct_map[aid]["moneda"] == "VES"][0]
                            amt_ves = loan_amt_usd * bcv
                            acct_map[ac_id]["saldo"] += amt_ves
                            tx_batch.append((
                                None, ac_id, "Deposito Taquilla", round(amt_ves, 2), loan_amt_usd, bcv,
                                f"{date_str} 10:00:00", "Taquilla", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                            ))
                            
        # --- CARTERA DE CRÉDITO: Cobro Mensual e Historial de Pagos ---
        loans_to_pay = [l for l in active_loans.values() if l["estado"] in ["Vigente", "Vencido"] and l["dia_pago"] == day_of_month]
        for l in loans_to_pay:
            c = clients_map[l["cliente_id"]]
            c_accts = [aid for aid, ac in acct_map.items() if ac["cliente_id"] == c["id"]]
            
            usd_acct = [aid for aid in c_accts if acct_map[aid]["moneda"] == "USD" and acct_map[aid]["estado"] == "Activa"]
            ves_acct = [aid for aid in c_accts if acct_map[aid]["moneda"] == "VES" and acct_map[aid]["estado"] == "Activa"]
            payment_amount = l["cuota_mensual"]
            
            # Estrés macroeconómico: inflación alta y salto del paralelo elevan probabilidad de impago
            macro_strain = max(1.0, (macro["inflacion"] / 2.5) * (macro["paralela"] / macro["bcv"]))
            default_prob = 0.035 * macro_strain
            if c["score_credito"] < 500:
                default_prob += 0.18
            elif c["score_credito"] < 600:
                default_prob += 0.06
                
            has_funds_usd = usd_acct and acct_map[usd_acct[0]]["saldo"] >= payment_amount
            has_funds_ves = ves_acct and acct_map[ves_acct[0]]["saldo"] >= (payment_amount * bcv)
            
            if random.random() > default_prob and (has_funds_usd or has_funds_ves):
                if has_funds_usd:
                    ac_id = usd_acct[0]
                    acct_map[ac_id]["saldo"] -= payment_amount
                    tx_batch.append((
                        None, ac_id, "Transferencia", payment_amount, payment_amount, bcv,
                        f"{date_str} 09:00:00", "Banca Movil", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))
                else:
                    ac_id = ves_acct[0]
                    amt_ves = payment_amount * bcv
                    acct_map[ac_id]["saldo"] -= amt_ves
                    tx_batch.append((
                        None, ac_id, "Transferencia", round(amt_ves, 2), payment_amount, bcv,
                        f"{date_str} 09:00:00", "Banca Movil", "Completada", None, 0, 10.48, -66.90, "SYSTEM"
                    ))
                    
                l["cuotas_pagadas"] += 1
                l["saldo_pendiente_usd"] = max(0.0, l["monto_aprobado_usd"] - (l["cuotas_pagadas"] * (l["monto_aprobado_usd"] / l["cuotas_totales"])))
                
                loan_payments_list.append({
                    "id": payment_id_counter,
                    "credito_id": l["id"],
                    "monto_pago_usd": round(payment_amount, 2),
                    "fecha_pago": date_str,
                    "dias_atraso": 0,
                    "estado_pago": "A Tiempo"
                })
                payment_id_counter += 1
                
                if l["cuotas_pagadas"] >= l["cuotas_totales"]:
                    l["estado"] = "Pagado"
            else:
                latre = random.randint(10, 40) if random.random() < 0.65 else random.randint(45, 110)
                l["saldo_pendiente_usd"] += payment_amount * 0.03
                
                if latre > 90:
                    l["estado"] = "Vencido" if random.random() < 0.70 else "En Litigio"
                    
                loan_payments_list.append({
                    "id": payment_id_counter,
                    "credito_id": l["id"],
                    "monto_pago_usd": 0.0,
                    "fecha_pago": date_str,
                    "dias_atraso": latre,
                    "estado_pago": "No Pagado" if latre > 30 else "Atrasado"
                })
                payment_id_counter += 1
                
        # --- RIESGO DE LIQUIDEZ Y TESORERÍA ---
        total_dep_ves = sum(acct_map[aid]["saldo"] for aid in active_accts_ves)
        total_dep_usd = sum(acct_map[aid]["saldo"] for aid in active_accts_usd)
        total_cred_usd = sum(l["saldo_pendiente_usd"] for l in active_loans.values() if l["estado"] in ["Vigente", "Vencido"])
        total_cred_ves = total_cred_usd * bcv
        
        # Encaje Legal BCV: 73% sobre depósitos en VES
        encaje_bcv_ves = total_dep_ves * 0.73
        
        # Flujo neto en caja
        net_flow_usd = sum(tx[4] if tx[2] == "Deposito Taquilla" else -tx[4] for tx in tx_batch if tx[6].startswith(date_str))
        disponible_caja_ves += (net_flow_usd * bcv)
        disponible_caja_ves = max(total_dep_ves * 0.05, disponible_caja_ves)
        
        tasa_liq = disponible_caja_ves / (total_dep_ves + 1.0)
        brecha_liq_usd = (disponible_caja_ves - encaje_bcv_ves) / bcv
        
        if brecha_liq_usd < 0:
            borrow_amt_usd = abs(brecha_liq_usd) * 1.10
            disponible_caja_ves += (borrow_amt_usd * bcv)
            treasury_ops_list.append({
                "id": treasury_id_counter,
                "fecha": date_str,
                "tipo_operacion": "Colocacion Interbancaria",
                "monto_usd": round(borrow_amt_usd, 2),
                "tasa_anual": round(macro["activa"] * 0.90, 2),
                "plazo_dias": 1,
                "contraparte": random.choice(["Banco de Venezuela", "Banesco", "Banco Provincial"])
            })
            treasury_id_counter += 1
        elif brecha_liq_usd > (total_dep_usd * 0.18):
            invest_amt_usd = brecha_liq_usd * 0.45
            disponible_caja_ves -= (invest_amt_usd * bcv)
            treasury_ops_list.append({
                "id": treasury_id_counter,
                "fecha": date_str,
                "tipo_operacion": "Compra Divisas BCV" if random.random() < 0.6 else "Inversion Corto Plazo",
                "monto_usd": round(invest_amt_usd, 2),
                "tasa_anual": round(macro["pasiva"] * 1.25, 2),
                "plazo_dias": random.choice([7, 14, 28]),
                "contraparte": "Banco Central de Venezuela" if random.random() < 0.6 else "Bolsa de Valores de Caracas"
            })
            treasury_id_counter += 1
            
        daily_liquidity_list.append({
            "fecha": date_str,
            "total_depositos_ves": round(total_dep_ves, 2),
            "total_depositos_usd": round(total_dep_usd, 2),
            "total_creditos_ves": round(total_cred_ves, 2),
            "total_creditos_usd": round(total_cred_usd, 2),
            "disponible_caja_ves": round(disponible_caja_ves, 2),
            "encaje_legal_bcv_ves": round(encaje_bcv_ves, 2),
            "tasa_liquidez": round(tasa_liq, 4),
            "brecha_liquidez_usd": round(brecha_liq_usd, 2)
        })
        
        # Volcar transacciones a SQLite por lotes de 50,000 para optimizar memoria RAM
        if len(tx_batch) >= 50000:
            cursor.executemany("""
            INSERT INTO transacciones (id, cuenta_id, tipo_transaccion, monto, monto_usd, tasa_cambio, fecha_hora, canal, estado, codigo_error, es_fraude, latitud, longitud, dispositivo_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tx_batch)
            db_conn.commit()
            tx_batch = []
            
        current_date += delta
        
    if tx_batch:
        cursor.executemany("""
        INSERT INTO transacciones (id, cuenta_id, tipo_transaccion, monto, monto_usd, tasa_cambio, fecha_hora, canal, estado, codigo_error, es_fraude, latitud, longitud, dispositivo_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tx_batch)
        db_conn.commit()
        
    # 4. Insertar Créditos y Pagos
    print("4/6 Guardando cartera de créditos e historial de pagos...")
    cursor.executemany("""
    INSERT INTO creditos (id, cliente_id, monto_aprobado_usd, tasa_interes_anual, plazo_meses, fecha_otorgamiento, fecha_vencimiento, tipo_credito, estado, saldo_pendiente_usd, cuotas_totales, cuotas_pagadas)
    VALUES (:id, :cliente_id, :monto_aprobado_usd, :tasa_interes_anual, :plazo_meses, :fecha_otorgamiento, :fecha_vencimiento, :tipo_credito, :estado, :saldo_pendiente_usd, :cuotas_totales, :cuotas_pagadas)
    """, loans_list)
    
    cursor.executemany("""
    INSERT INTO pagos_creditos (id, credito_id, monto_pago_usd, fecha_pago, dias_atraso, estado_pago)
    VALUES (:id, :credito_id, :monto_pago_usd, :fecha_pago, :dias_atraso, :estado_pago)
    """, loan_payments_list)
    
    db_conn.commit()
    
    # 5. Actualizar saldos finales de las cuentas
    print("5/6 Actualizando balances finales de cuentas...")
    final_saldos = [(v["saldo"], k) for k, v in acct_map.items()]
    cursor.executemany("UPDATE cuentas SET saldo_actual = ? WHERE id = ?", final_saldos)
    db_conn.commit()
    
    # 6. Insertar Indicadores Macro y Resúmenes Diarios
    print("6/6 Insertando series macroeconómicas y balances de tesorería...")
    macro_records_list = []
    for k, v in macro_data.items():
        macro_records_list.append({
            "fecha": k,
            "tasa_bcv_usd_ves": v["bcv"],
            "tasa_paralela_usd_ves": v["paralela"],
            "inflacion_mensual_pct": v["inflacion"],
            "variacion_pib_mensual_pct": v["pib"],
            "tasa_activa_ves_anual": v["activa"],
            "tasa_pasiva_ves_anual": v["pasiva"]
        })
        
    cursor.executemany("""
    INSERT INTO indicadores_macro (fecha, tasa_bcv_usd_ves, tasa_paralela_usd_ves, inflacion_mensual_pct, variacion_pib_mensual_pct, tasa_activa_ves_anual, tasa_pasiva_ves_anual)
    VALUES (:fecha, :tasa_bcv_usd_ves, :tasa_paralela_usd_ves, :inflacion_mensual_pct, :variacion_pib_mensual_pct, :tasa_activa_ves_anual, :tasa_pasiva_ves_anual)
    """, macro_records_list)
    
    cursor.executemany("""
    INSERT INTO resumen_liquidez_diario (fecha, total_depositos_ves, total_depositos_usd, total_creditos_ves, total_creditos_usd, disponible_caja_ves, encaje_legal_bcv_ves, tasa_liquidez, brecha_liquidez_usd)
    VALUES (:fecha, :total_depositos_ves, :total_depositos_usd, :total_creditos_ves, :total_creditos_usd, :disponible_caja_ves, :encaje_legal_bcv_ves, :tasa_liquidez, :brecha_liquidez_usd)
    """, daily_liquidity_list)
    
    cursor.executemany("""
    INSERT INTO operaciones_tesoreria (id, fecha, tipo_operacion, monto_usd, tasa_anual, plazo_dias, contraparte)
    VALUES (:id, :fecha, :tipo_operacion, :monto_usd, :tasa_anual, :plazo_dias, :contraparte)
    """, treasury_ops_list)
    
    db_conn.commit()
    print("Datos insertados exitosamente.")

def generate_postgres_sql(db_conn):
    print("Generando backup SQL compatible con PostgreSQL...")
    os.makedirs(os.path.dirname(SQL_BACKUP_FILE), exist_ok=True)
    
    with open(SQL_BACKUP_FILE, 'w', encoding='utf-8') as f:
        f.write("-- REPOSITORIO DE BASE DE DATOS BANCARIA VENEZUELA\n")
        f.write("-- Copia de respaldo compatible con PostgreSQL para modelos de Machine Learning\n\n")
        
        f.write("""
DROP TABLE IF EXISTS transacciones;
DROP TABLE IF EXISTS cuentas;
DROP TABLE IF EXISTS pagos_creditos;
DROP TABLE IF EXISTS creditos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS indicadores_macro;
DROP TABLE IF EXISTS resumen_liquidez_diario;
DROP TABLE IF EXISTS operaciones_tesoreria;

CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    tipo_documento CHAR(1) CHECK(tipo_documento IN ('V', 'E', 'J')) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero CHAR(1) CHECK(genero IN ('M', 'F')) NOT NULL,
    estado_civil VARCHAR(20) CHECK(estado_civil IN ('Soltero', 'Casado', 'Divorciado', 'Viudo')) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    estado_residencia VARCHAR(50) NOT NULL,
    fecha_registro DATE NOT NULL,
    estado_cliente VARCHAR(10) CHECK(estado_cliente IN ('Activo', 'Inactivo')) NOT NULL,
    fecha_desafiliacion DATE,
    score_credito INT NOT NULL,
    ingresos_mensuales_usd NUMERIC(15,2) NOT NULL,
    actividad_economica VARCHAR(100) NOT NULL,
    nivel_riesgo_interno VARCHAR(10) CHECK(nivel_riesgo_interno IN ('Bajo', 'Medio', 'Alto')) NOT NULL
);

CREATE TABLE cuentas (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL,
    numero_cuenta CHAR(20) UNIQUE NOT NULL,
    tipo_cuenta VARCHAR(15) CHECK(tipo_cuenta IN ('Corriente', 'Ahorros')) NOT NULL,
    moneda CHAR(3) CHECK(moneda IN ('VES', 'USD')) NOT NULL,
    fecha_apertura DATE NOT NULL,
    saldo_actual NUMERIC(18,2) NOT NULL,
    estado_cuenta VARCHAR(15) CHECK(estado_cuenta IN ('Activa', 'Bloqueada', 'Cerrada')) NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE transacciones (
    id SERIAL PRIMARY KEY,
    cuenta_id INT NOT NULL,
    tipo_transaccion VARCHAR(30) NOT NULL,
    monto NUMERIC(18,2) NOT NULL,
    monto_usd NUMERIC(18,2) NOT NULL,
    tasa_cambio NUMERIC(12,4) NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    canal VARCHAR(30) NOT NULL,
    estado VARCHAR(15) CHECK(estado IN ('Completada', 'Rechazada', 'Fallida')) NOT NULL,
    codigo_error VARCHAR(30),
    es_fraude INT DEFAULT 0,
    latitud NUMERIC(9,6),
    longitud NUMERIC(9,6),
    dispositivo_id VARCHAR(30),
    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
);

CREATE TABLE creditos (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL,
    monto_aprobado_usd NUMERIC(15,2) NOT NULL,
    tasa_interes_anual NUMERIC(5,2) NOT NULL,
    plazo_meses INT NOT NULL,
    fecha_otorgamiento DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    tipo_credito VARCHAR(20) CHECK(tipo_credito IN ('Consumo', 'Comercial', 'Microcredito', 'Hipotecario')) NOT NULL,
    estado VARCHAR(15) CHECK(estado IN ('Vigente', 'Pagado', 'Vencido', 'En Litigio')) NOT NULL,
    saldo_pendiente_usd NUMERIC(15,2) NOT NULL,
    cuotas_totales INT NOT NULL,
    cuotas_pagadas INT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE pagos_creditos (
    id SERIAL PRIMARY KEY,
    credito_id INT NOT NULL,
    monto_pago_usd NUMERIC(15,2) NOT NULL,
    fecha_pago DATE NOT NULL,
    dias_atraso INT NOT NULL,
    estado_pago VARCHAR(15) CHECK(estado_pago IN ('A Tiempo', 'Atrasado', 'No Pagado')) NOT NULL,
    FOREIGN KEY (credito_id) REFERENCES creditos(id)
);

CREATE TABLE indicadores_macro (
    fecha DATE PRIMARY KEY,
    tasa_bcv_usd_ves NUMERIC(12,4) NOT NULL,
    tasa_paralela_usd_ves NUMERIC(12,4) NOT NULL,
    inflacion_mensual_pct NUMERIC(5,2) NOT NULL,
    variacion_pib_mensual_pct NUMERIC(5,2) NOT NULL,
    tasa_activa_ves_anual NUMERIC(5,2) NOT NULL,
    tasa_pasiva_ves_anual NUMERIC(5,2) NOT NULL
);

CREATE TABLE resumen_liquidez_diario (
    fecha DATE PRIMARY KEY,
    total_depositos_ves NUMERIC(20,2) NOT NULL,
    total_depositos_usd NUMERIC(20,2) NOT NULL,
    total_creditos_ves NUMERIC(20,2) NOT NULL,
    total_creditos_usd NUMERIC(20,2) NOT NULL,
    disponible_caja_ves NUMERIC(20,2) NOT NULL,
    encaje_legal_bcv_ves NUMERIC(20,2) NOT NULL,
    tasa_liquidez NUMERIC(8,4) NOT NULL,
    brecha_liquidez_usd NUMERIC(18,2) NOT NULL
);

CREATE TABLE operaciones_tesoreria (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo_operacion VARCHAR(30) CHECK(tipo_operacion IN ('Colocacion Interbancaria', 'Compra Divisas BCV', 'Venta Divisas', 'Inversion Corto Plazo')) NOT NULL,
    monto_usd NUMERIC(15,2) NOT NULL,
    tasa_anual NUMERIC(5,2) NOT NULL,
    plazo_dias INT NOT NULL,
    contraparte VARCHAR(100) NOT NULL
);

CREATE INDEX idx_transacciones_cuenta ON transacciones(cuenta_id);
CREATE INDEX idx_transacciones_fecha ON transacciones(fecha_hora);
CREATE INDEX idx_clientes_cedula ON clientes(cedula);
CREATE INDEX idx_creditos_cliente ON creditos(cliente_id);
CREATE INDEX idx_pagos_credito ON pagos_creditos(credito_id);
\n""")
        
        tables = ["indicadores_macro", "clientes", "cuentas", "creditos", "pagos_creditos", "resumen_liquidez_diario", "operaciones_tesoreria", "transacciones"]
        sqlite_cursor = db_conn.cursor()
        
        for table in tables:
            print(f"Exportando tabla {table} a PostgreSQL dump...")
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in sqlite_cursor.fetchall()]
            cols_str = ", ".join(columns)
            
            f.write(f"\n-- Datos para la tabla {table}\n")
            
            chunk_size = 1000
            for k in range(0, len(rows), chunk_size):
                chunk = rows[k:k+chunk_size]
                f.write(f"INSERT INTO {table} ({cols_str}) VALUES\n")
                
                values_list = []
                for row in chunk:
                    row_vals = []
                    for val in row:
                        if val is None:
                            row_vals.append("NULL")
                        elif isinstance(val, str):
                            escaped = val.replace("'", "''")
                            row_vals.append(f"'{escaped}'")
                        else:
                            row_vals.append(str(val))
                    values_list.append("(" + ", ".join(row_vals) + ")")
                
                f.write(",\n".join(values_list) + ";\n")
                
        f.write("\n-- Ajustar secuencias serial\n")
        f.write("SELECT setval('clientes_id_seq', COALESCE((SELECT MAX(id)+1 FROM clientes), 1), false);\n")
        f.write("SELECT setval('cuentas_id_seq', COALESCE((SELECT MAX(id)+1 FROM cuentas), 1), false);\n")
        f.write("SELECT setval('transacciones_id_seq', COALESCE((SELECT MAX(id)+1 FROM transacciones), 1), false);\n")
        f.write("SELECT setval('creditos_id_seq', COALESCE((SELECT MAX(id)+1 FROM creditos), 1), false);\n")
        f.write("SELECT setval('pagos_creditos_id_seq', COALESCE((SELECT MAX(id)+1 FROM pagos_creditos), 1), false);\n")
        f.write("SELECT setval('operaciones_tesoreria_id_seq', COALESCE((SELECT MAX(id)+1 FROM operaciones_tesoreria), 1), false);\n")

    print(f"PostgreSQL backup generado exitosamente en: {SQL_BACKUP_FILE}")

def main():
    if os.path.exists(DB_FILE):
        print(f"Borrando base de datos existente {DB_FILE}...")
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    
    try:
        init_db(conn)
        generate_all_data(conn)
        generate_postgres_sql(conn)
        print("¡Proceso de generación completado con éxito!")
    except Exception as e:
        print(f"Error durante la generación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
