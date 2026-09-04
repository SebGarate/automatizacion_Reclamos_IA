import os
import json
import time
import psycopg2
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

# Cargar variables del .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Error: No se encontró GEMINI_API_KEY. Revisa tu archivo .env en la raíz del proyecto.")

# Inicializar cliente de Gemini con la clave obtenida
client = genai.Client(api_key=api_key)

def analizar_reclamo_con_ia(texto_reclamo: str) -> dict:
    """Envía el reclamo a Gemini intentando con modelos activos (serie 3.x) y manejo de 503."""
    prompt = f"""
    Eres un analista experto en atención al cliente bancario/retail.
    Analiza el siguiente reclamo de un cliente y genera una respuesta ÚNICAMENTE en formato JSON válido.

    Reclamo: "{texto_reclamo}"

    Estructura del JSON esperada:
    {{
        "categoria": "Falla en App | Cobro Indebido | Atención al Cliente | Transacción No Reconocida | Otro",
        "sentimiento": "Positivo | Neutro | Negativo | Muy Negativo",
        "urgencia": "Baja | Media | Alta",
        "resumen_ejecutivo": "Síntesis en máximo 15 palabras de lo sucedido."
    }}
    """
    
    # Modelos activos recomendados por la API de Google
    modelos_disponibles = ['gemini-3.6-flash', 'gemini-3.5-flash']

    for modelo in modelos_disponibles:
        for intento in range(1, 3):
            try:
                print(f"📡 Intentando con modelo: {modelo} (Intento {intento})...")
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            except errors.ServerError as e:
                if e.code == 503:
                    print(f"⚠️ {modelo} ocupado (503). Esperando 1s...")
                    time.sleep(1)
                else:
                    raise e
            except errors.ClientError as e:
                print(f"❌ Error de cliente en {modelo}: {e.message}")
                break  # Pasa al siguiente modelo
                
    raise RuntimeError("No se pudo procesar el reclamo con ninguno de los modelos disponibles.")

def guardar_en_postgres(cliente: dict, analisis: dict):
    """Inserta el reclamo y el análisis generado por la IA en PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "claims_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        cursor = conn.cursor()
        
        query = """
        INSERT INTO reclamos (cliente_nombre, cliente_dni, cliente_email, texto_reclamo, categoria, sentimiento, urgencia, resumen_ejecutivo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        valores = (
            cliente['nombre'],
            cliente['dni'],
            cliente['email'],
            cliente['texto'],
            analisis['categoria'],
            analisis['sentimiento'],
            analisis['urgencia'],
            analisis['resumen_ejecutivo']
        )
        
        cursor.execute(query, valores)
        reclamo_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Reclamo #{reclamo_id} registrado exitosamente en PostgreSQL.")
        cursor.close()
        conn.close()
        return reclamo_id

    except Exception as e:
        print(f"❌ Error al conectar o insertar en la base de datos: {e}")

if __name__ == "__main__":
    cliente_demo = {
        "nombre": "Juan Pérez",
        "dni": "72819203",
        "email": "juan.perez@email.com",
        "texto": "¡Es el colmo! Intenté hacer una transferencia de S/ 1,500 por la app, me debitaron el dinero pero la transferencia falló. Exijo mi dinero de vuelta o iré a Indecopi hoy mismo."
    }
    
    print("🤖 Procesando reclamo con Gemini AI...")
    analisis_res = analizar_reclamo_con_ia(cliente_demo["texto"])
    print(f"Resultado IA:\n{json.dumps(analisis_res, indent=2, ensure_ascii=False)}")
    
    guardar_en_postgres(cliente_demo, analisis_res)