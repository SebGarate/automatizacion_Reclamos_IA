# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

USER = "postgres"
PASSWORD = "sebas"  # 
HOST = "localhost"
PORT = "5432"
DBNAME = "claims_db"      # Tu base de datos

DATABASE_URL = f"postgresql+pg8000://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DBNAME}"
engine = create_engine(DATABASE_URL)

# 1. Crear un pool fijo de 50 clientes reales
NOMBRES = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Lucia", "Diego", "Sofia", "Fernando", "Elena", "Mateo", "Camila"]
APELLIDOS = ["Mendoza", "Torres", "Delgado", "Gomez", "Rojas", "Fernandez", "Vargas", "Silva", "Castro", "Rios"]

POOL_CLIENTES = []
for _ in range(50):
    nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
    dni = str(random.randint(10000000, 99999999))
    email = f"{nombre.lower().replace(' ', '.')}@email.com"
    POOL_CLIENTES.append({"nombre": nombre, "dni": dni, "email": email})

CATEGORIAS = ["Cobros Indebidos", "Falla Tecnica", "Atencion al Cliente", "Retraso en Servicio", "Fraude / Seguridad"]
SENTIMIENTOS = ["Enojado", "Frustrado", "Neutral", "Urgente"]
URGENCIAS = ["Baja", "Media", "Alta"]

MOTIVOS_POR_CATEGORIA = {
    "Cobros Indebidos": [
        "Me cobraron la suscripcion dos veces en el mismo mes.",
        "Aparece un cargo no reconocido en mi estado de cuenta por mantenimiento.",
        "Se aplico una comision por cobro tardio cuando pague a tiempo."
    ],
    "Falla Tecnica": [
        "La aplicacion no me permite realizar transferencias desde ayer.",
        "Error al intentar validar la firma digital en el portal web.",
        "La sesion se cierra automaticamente cada vez que intento adjuntar un archivo."
    ],
    "Atencion al Cliente": [
        "El operador me trato de forma inadecuada al solicitar soporte telefonico.",
        "Llevo mas de 45 minutos en espera en el canal de atencion y cortaron la llamada.",
        "No me brindaron respuesta clara sobre el estado de mi reclamo previo."
    ],
    "Retraso en Servicio": [
        "El tramite de desafiliacion no se completo en las 24 horas prometidas.",
        "La entrega de la tarjeta de reemplazo supero el plazo maximo estipulado.",
        "Llevo 5 dias esperando la devolucion de fondos aprobada."
    ],
    "Fraude / Seguridad": [
        "Detecte una transaccion sospechosa en mi cuenta durante la madrugada.",
        "Recibi alertas de inicio de sesion no autorizado desde un dispositivo desconocido.",
        "Bloquearon mi cuenta por supuesto fraude sin haberme notificado previamente."
    ]
}

def regenerar_datos(total_registros=1000):
    print("Limpiando tabla e insertando 1000 registros con clientes recurrentes...")
    
    truncate_sql = text("TRUNCATE TABLE reclamos RESTART IDENTITY;")
    
    insert_sql = text("""
        INSERT INTO reclamos (
            cliente_nombre, cliente_dni, cliente_email, texto_reclamo, 
            categoria, sentimiento, urgencia, resumen_ejecutivo, fecha_registro
        )
        VALUES (
            :cliente_nombre, :cliente_dni, :cliente_email, :texto_reclamo, 
            :categoria, :sentimiento, :urgencia, :resumen_ejecutivo, :fecha_registro
        );
    """)
    
    registros = []
    fecha_actual = datetime.now()
    
    for _ in range(total_registros):
        # Seleccionar un cliente de nuestro pool fijo
        cliente = random.choice(POOL_CLIENTES)
        
        categoria = random.choice(CATEGORIAS)
        sentimiento = random.choice(SENTIMIENTOS)
        urgencia = random.choices(URGENCIAS, weights=[50, 35, 15])[0]
        reclamo = random.choice(MOTIVOS_POR_CATEGORIA[categoria])
        resumen = f"Reclamo de {categoria} analizado por IA. Severidad: {urgencia}."
        
        dias_atras = random.randint(0, 180)
        horas_atras = random.randint(0, 23)
        minutos_atras = random.randint(0, 59)
        fecha_reg = fecha_actual - timedelta(days=dias_atras, hours=horas_atras, minutes=minutos_atras)
        
        registros.append({
            "cliente_nombre": cliente["nombre"],
            "cliente_dni": cliente["dni"],
            "cliente_email": cliente["email"],
            "texto_reclamo": reclamo,
            "categoria": categoria,
            "sentimiento": sentimiento,
            "urgencia": urgencia,
            "resumen_ejecutivo": resumen,
            "fecha_registro": fecha_reg
        })
        
    with engine.begin() as connection:
        connection.execute(truncate_sql)
        connection.execute(insert_sql, registros)
        
    print(f"Exito: Se insertaron {total_registros} registros distribuidos entre 50 clientes recurrentes.")

if __name__ == "__main__":
    regenerar_datos(1000)