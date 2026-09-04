from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from processor import analizar_reclamo_con_ia, guardar_en_postgres

app = FastAPI(
    title="Intelligent Claims Categorization API",
    description="API REST para procesar reclamos con Gemini AI y almacenarlos en PostgreSQL",
    version="1.0.0"
)

# Esquema de validación para la entrada HTTP
class ReclamoRequest(BaseModel):
    nombre: str
    dni: str
    email: EmailStr
    texto: str

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Juan Pérez",
                "dni": "72819203",
                "email": "juan.perez@email.com",
                "texto": "Intenté hacer una transferencia por la app y me debitaron pero no llegó."
            }
        }

@app.get("/", tags=["Health Check"])
def root():
    return {"status": "ok", "message": "API de Categorización de Reclamos activa"}

@app.post("/api/v1/reclamos", status_code=status.HTTP_201_CREATED, tags=["Reclamos"])
def procesar_reclamo(reclamo: ReclamoRequest):
    try:
        datos_cliente = reclamo.model_dump()
        
        # 1. Analizar con IA
        analisis = analizar_reclamo_con_ia(datos_cliente["texto"])
        
        # 2. Guardar en PostgreSQL
        reclamo_id = guardar_en_postgres(datos_cliente, analisis)
        
        if not reclamo_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo guardar el reclamo en la base de datos."
            )

        # Devolver respuesta JSON explícita
        return JSONResponse(
            status_code=201,
            content={
                "id": reclamo_id,
                "nombre": datos_cliente["nombre"],
                "dni": datos_cliente["dni"],
                "email": datos_cliente["email"],
                "reclamo": datos_cliente["texto"],
                "categoria": analisis["categoria"],
                "urgencia": analisis["urgencia"],
                "resumen": analisis["resumen_ejecutivo"]
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el procesamiento: {str(e)}"
        )