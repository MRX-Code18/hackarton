# Plataforma Inteligente de Reportes

Aplicación fullstack: frontend HTML integrado con backend FastAPI (Python).

## Estructura del proyecto

```
reporte-urbano/
├── main.py              ← Backend FastAPI + sirve el frontend
├── requirements.txt     ← Dependencias Python
├── static/
│   └── index.html       ← Frontend (servido por FastAPI en /)
└── uploads/             ← Fotos adjuntas a los reportes (auto-creada)
```

## Instalación y arranque

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar el servidor
uvicorn main:app --reload --port 8000
```

## Uso

Abre tu navegador en **http://127.0.0.1:8000**

El frontend y el backend comparten el mismo origen → sin problemas de CORS.

## Endpoints API

| Método | Ruta                    | Descripción                         |
|--------|-------------------------|-------------------------------------|
| GET    | `/`                     | Sirve el frontend (index.html)      |
| POST   | `/api/reportes`         | Crea un nuevo reporte ciudadano     |
| GET    | `/api/reportes/{folio}` | Consulta el estatus de un reporte   |
| GET    | `/uploads/{archivo}`    | Accede a fotos adjuntas             |
| GET    | `/docs`                 | Documentación interactiva (Swagger) |

## Producción

- Reemplaza `DB_REPORTES` por SQLAlchemy + PostgreSQL/MySQL
- Cambia `allow_origins=["*"]` en CORS por tu dominio real
- Considera un bucket S3/GCS para almacenar imágenes
