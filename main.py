import logging
import os
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 1. CLIENTE DE SUPABASE
# ─────────────────────────────────────────────
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_BUCKET = "fotos-reportes"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─────────────────────────────────────────────
# 2. APP FASTAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title="Plataforma Inteligente de Reportes - API",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = "static"


@app.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ─────────────────────────────────────────────
# 3. HEALTH CHECK — prueba la conexión a Supabase
#    Visita http://127.0.0.1:8000/api/health
# ─────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    try:
        result = supabase.table("reportes").select("folio").limit(1).execute()
        return {"status": "ok", "supabase": "conectado", "tabla_reportes": "existe"}
    except Exception as e:
        logger.error(f"[HEALTH] Error: {e}")
        return {"status": "error", "detalle": str(e)}


# ─────────────────────────────────────────────
# 4. MOTOR DE IA
# ─────────────────────────────────────────────
def analizar_reporte_con_ia(descripcion: str):
    d = descripcion.lower()
    if any(p in d for p in ["fuga", "inundacion", "agua", "tuberia", "tubería", "drenaje"]):
        return ("Infraestructura Hidraulica", "Alta", 2,
                "El sistema detectó un riesgo hidráulico severo. Se notificó a la cuadrilla de Agua y Saneamiento.")
    elif any(p in d for p in ["bache", "socavon", "socavón", "grieta", "pavimento"]):
        return ("Vialidad y Pavimentacion", "Media", 3,
                "Reporte clasificado en obras públicas. Se integró al mapa de bacheo prioritario.")
    elif any(p in d for p in ["luminaria", "luz", "obscuro", "poste", "cables"]):
        return ("Alumbrado Publico", "Normal", 4,
                "Falla en el circuito eléctrico detectada. Turnado a servicios públicos.")
    else:
        return ("Servicios Generales", "Normal", 4,
                "Reporte recibido. La IA institucional lo canalizó al departamento correspondiente.")


# ─────────────────────────────────────────────
# 5. ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/api/reportes")
async def crear_reporte(
    descripcion: str = Form(...),
    ubicacion: str = Form(...),
    foto: Optional[UploadFile] = File(None),
):
    try:
        folio = f"FOL-2026-{str(uuid.uuid4())[:8].upper()}"
        categoria, prioridad, prioridad_num, mensaje_ia = analizar_reporte_con_ia(descripcion)

        # ── Subir foto (opcional) ───────────────────────────────────
        foto_url = None
        if foto and foto.filename:
            try:
                extension = os.path.splitext(foto.filename)[1] or ".jpg"
                storage_path = f"{folio}{extension}"
                content = await foto.read()
                supabase.storage.from_(SUPABASE_BUCKET).upload(
                    path=storage_path,
                    file=content,
                    file_options={"content-type": foto.content_type or "image/jpeg"},
                )
                foto_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{storage_path}"
            except Exception as foto_err:
                # No abortar si la foto falla, solo loguear
                logger.warning(f"[FOTO] No se pudo subir la foto: {foto_err}")

        # ── Insertar en Supabase ────────────────────────────────────
        row = {
            "folio":               folio,
            "descripcion":         descripcion,
            "ubicacion":           ubicacion,
            "foto_url":            foto_url,
            "categoria":           categoria,
            "prioridad":           prioridad,
            "prioridad_num":       prioridad_num,
            "mensaje_ia":          mensaje_ia,
            "estatus":             "Recibido",
            "progreso_porcentaje": 0,
        }

        logger.info(f"[INSERT] Insertando reporte {folio}...")
        result = supabase.table("reportes").insert(row).execute()
        logger.info(f"[INSERT] Resultado: {result}")

        if not result.data:
            raise ValueError("Supabase no devolvió datos. ¿Ejecutaste el schema.sql?")

        return _formato_frontend(result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] POST /api/reportes → {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reportes/{folio}")
async def consultar_reporte(folio: str):
    try:
        folio_upper = folio.strip().upper()
        result = supabase.table("reportes").select("*").eq("folio", folio_upper).limit(1).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Folio no encontrado en el sistema.")

        return _formato_frontend(result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] GET /api/reportes/{folio} → {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reportes/{folio}/historial")
async def historial_reporte(folio: str):
    folio_upper = folio.strip().upper()
    result = (supabase.table("historial_estatus").select("*")
              .eq("folio", folio_upper).order("created_at").execute())
    return {"folio": folio_upper, "historial": result.data}


# ─────────────────────────────────────────────
# 6. HELPER
# ─────────────────────────────────────────────
def _formato_frontend(row: dict) -> dict:
    return {
        "folio":               row["folio"],
        "descripcion":         row["descripcion"],
        "ubicacion":           row["ubicacion"],
        "foto_url":            row.get("foto_url"),
        "categoria":           row["categoria"],
        "prioridad":           row["prioridad_num"],
        "mensaje_ia":          row["mensaje_ia"],
        "estatus":             row["estatus"],
        "progreso_porcentaje": row["progreso_porcentaje"],
        "fecha_creacion":      row.get("created_at", ""),
    }
