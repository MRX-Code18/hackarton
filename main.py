import os
import random
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Plataforma Inteligente de Reportes - API",
    description="Backend en Python para la gestión ciudadana de reportes con IA",
    version="1.0.0",
)

# ─────────────────────────────────────────────
# 1. CORS — permite peticiones desde cualquier
#    origen local durante desarrollo.
#    En producción reemplaza "*" por tu dominio.
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# 2. Carpeta de imágenes subidas por ciudadanos
# ─────────────────────────────────────────────
UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)p.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ─────────────────────────────────────────────
# 3. Sirve el frontend (index.html) en la raíz.
#    Así el frontend y el backend comparten el
#    mismo origen → sin problemas de CORS.
# ─────────────────────────────────────────────
@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ─────────────────────────────────────────────
# 4. Base de Datos en Memoria (simulada)
#    En producción usa SQLAlchemy + PostgreSQL
# ─────────────────────────────────────────────
DB_REPORTES: dict = {}


# ─────────────────────────────────────────────
# 5. Motor de Inteligencia Artificial (simulado)
# ─────────────────────────────────────────────
def analizar_reporte_con_ia(descripcion: str):
    """
    Simula el análisis semántico de la IA institucional para determinar
    la prioridad, categoría y una respuesta automatizada.
    """
    desc_lower = descripcion.lower()

    if any(p in desc_lower for p in ["fuga", "inundacion", "agua", "tubería", "drenaje"]):
        categoria = "Infraestructura Hidráulica"
        prioridad = 2
        mensaje_ia = (
            "El sistema inteligente detectó un riesgo hidráulico severo. "
            "Se ha notificado inmediatamente a la cuadrilla de Agua y Saneamiento "
            "de la zona geográfica delimitada."
        )
    elif any(p in desc_lower for p in ["bache", "socavón", "grieta", "pavimento"]):
        categoria = "Vialidad y Pavimentación"
        prioridad = 3
        mensaje_ia = (
            "Reporte clasificado en el área de obras públicas. "
            "Se integró la anomalía vial al mapa de bacheo prioritario "
            "para su pronta atención programada."
        )
    elif any(p in desc_lower for p in ["luminaria", "luz", "obscuro", "poste", "cables"]):
        categoria = "Alumbrado Público"
        prioridad = 4
        mensaje_ia = (
            "Se identificó una falla en el circuito eléctrico comunitario. "
            "Turnado al departamento de servicios públicos para la "
            "sustitución del componente lumínico."
        )
    else:
        categoria = "Servicios Generales"
        prioridad = 4
        mensaje_ia = (
            "Reporte recibido con éxito. La IA institucional ha canalizado "
            "los detalles al departamento administrativo correspondiente "
            "para su evaluación manual."
        )

    return categoria, prioridad, mensaje_ia


# ─────────────────────────────────────────────
# 6. ENDPOINTS DE LA API
# ─────────────────────────────────────────────

@app.post("/api/reportes")
async def crear_reporte(
    descripcion: str = Form(...),
    ubicacion: str = Form(...),
    foto: Optional[UploadFile] = File(None),
):
    """
    Recibe los datos del formulario (FormData), procesa la foto opcional,
    ejecuta el motor de IA y almacena el reporte generando un folio único.
    """
    try:
        nuevo_id = str(uuid.uuid4())[:8].upper()
        folio = f"FOL-2026-{nuevo_id}"

        foto_url = None
        if foto and foto.filename:
            extension = os.path.splitext(foto.filename)[1]
            nombre_archivo = f"{folio}{extension}"
            ruta_archivo = os.path.join(UPLOAD_DIR, nombre_archivo)

            with open(ruta_archivo, "wb") as buffer:
                content = await foto.read()
                buffer.write(content)

            foto_url = f"/uploads/{nombre_archivo}"

        categoria, prioridad, mensaje_ia = analizar_reporte_con_ia(descripcion)

        reporte_data = {
            "folio": folio,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "foto_url": foto_url,
            "categoria": categoria,
            "prioridad": prioridad,
            "mensaje_ia": mensaje_ia,
            "estatus": "Recibido",
            "progreso_porcentaje": 0,
            "fecha_creacion": "2026-05-21",
        }

        DB_REPORTES[folio] = reporte_data
        return reporte_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al procesar el reporte: {str(e)}",
        )


@app.get("/api/reportes/{folio}")
async def consultar_reporte(folio: str):
    """
    Permite el seguimiento del reporte mediante su folio institucional.
    Devuelve los datos de estatus y progreso dinámico para las barras de nivel.
    """
    folio_upper = folio.strip().upper()

    if folio_upper not in DB_REPORTES:
        raise HTTPException(
            status_code=404,
            detail="El folio institucional ingresado no fue encontrado en el sistema.",
        )

    reporte = DB_REPORTES[folio_upper]

    estados_posibles = [
        {"status": "Recibido",      "pct": 0,   "node": 1},
        {"status": "Validado por IA","pct": 33,  "node": 2},
        {"status": "En Cuadrilla",  "pct": 66,  "node": 3},
        {"status": "Resuelto",      "pct": 100, "node": 4},
    ]

    estado_actual = random.choice(estados_posibles)
    reporte["estatus"] = estado_actual["status"]
    reporte["progreso_porcentaje"] = estado_actual["pct"]

    return reporte
