import os
import random
from flask import Flask, jsonify, render_template, request

# =========================================================================
# ⚙️ INICIALIZACIÓN DEL BACKEND MUNICIPAL FLASK
# =========================================================================
app = Flask(__name__, template_folder=".", static_folder=".")# =========================================================================
# 🗄️ PERSISTENCIA DE REGISTROS MUNICIPALES (BASE DE DATOS EN MEMORIA)
# =========================================================================
# Inicializamos el sistema con el folio por defecto incluido en tu interfaz
# original para asegurar la compatibilidad retroactiva inmediata al consultar.
REPORTES_DB = {
    "RPT-2026-00847": {
        "folio": "RPT-2026-00847",
        "categoria": "🚧 Vialidad",
        "subcategoria": "Bache profundo en calzada o avenida principal",
        "dependencia": "Dirección de Obras Públicas",
        "prioridad": "🔴 Prioridad Alta",
        "prioridad_clase": "prioridad-2",
        "eta": "48–72 horas",
        "estado": "🟡 En proceso",
        "tracking_level": "proceso",
        "mensaje": "Hola, gracias por tu reporte. Hemos registrado el desperfecto urbano con folio institucional #RPT-2026-00847. Tu solicitud fue enrutada con éxito a la Dirección de Obras Públicas del municipio.",
        "ubicacion": "Calle Hidalgo #42, Col. Centro"
    }
}

# =========================================================================
# 🛣️ ENRUTAMIENTOS HTTP DE LA APLICACIÓN
# =========================================================================

@app.route("/")
def home():
    """
    Ruta raíz del servidor. Entrega la plantilla HTML completa de forma nativa.
    """
    return render_template("index.html")


@app.route("/api/reportes", methods=["POST"])
def procesar_reporte():
    """
    Controlador encargado de recibir los formularios, analizar las cadenas de
    texto con reglas lógicas de categorización inteligente y asignar folios unívocos.
    """
    descripcion = request.form.get("descripcion", "").strip()
    ubicacion = request.form.get("ubicacion", "Ubicación Georreferenciada").strip()
    
    # Manejo opcional del archivo binario de la imagen
    archivo_foto = request.files.get("foto")

    if not descripcion:
        return jsonify({"status": "error", "message": "La descripción del reporte es obligatoria"}), 400

    # Generación aleatoria segura de folios consecutivos (Siguiendo el correlativo 800)
    consecutivo = random.randint(852, 999)
    folio_generado = f"RPT-2026-00{consecutivo}"

    # 🤖 MOTOR DE ANALÍTICA INTEGRADOR:
    # Examina tokens en la descripción para mapear dependencias y prioridades (SLA)
    desc_normalizada = descripcion.lower()

    if any(palabra in desc_normalizada for palabra in ["agua", "fuga", "tuber", "manguera", "drenaje"]):
        categoria = "💧 Agua y Saneamiento"
        subcategoria = "Fuga de agua potable / Colapso de drenaje"
        dependencia = "Comisión Municipal de Agua"
        prioridad = "🔴 Prioridad Crítica"
        prioridad_clase = "prioridad-2"
        eta = "12–24 horas"
        tracking_level = "proceso"
    elif any(palabra in desc_normalizada for palabra in ["luz", "lampara", "oscur", "poste", "alumbrado"]):
        categoria = "💡 Alumbrado"
        subcategoria = "Luminaria inoperante en vía pública"
        dependencia = "Dirección de Servicios Públicos"
        prioridad = "🟡 Prioridad Media"
        prioridad_clase = "prioridad-3"
        eta = "48–96 horas"
        tracking_level = "recibido"
    elif any(palabra in desc_normalizada for palabra in ["arbol", "parque", "basura", "maleza", "jardin"]):
        categoria = "🌳 Parques y Ecología"
        subcategoria = "Mantenimiento y desbroce de áreas comunitarias"
        dependencia = "Coordinación de Ecología"
        prioridad = "🔵 Prioridad Ordinaria"
        prioridad_clase = "prioridad-4"
        eta = "5 a 7 días hábiles"
        tracking_level = "recibido"
    else:
        # Fallback predeterminado para temas de asfalto/vialidades generales
        categoria = "🚧 Vialidad"
        subcategoria = "Desperfecto severo en la carpeta asfáltica"
        dependencia = "Dirección de Obras Públicas"
        prioridad = "🔴 Prioridad Alta"
        prioridad_clase = "prioridad-2"
        eta = "48–72 horas"
        tracking_level = "proceso"

    # Redacción del string automatizado con base en las variables procesadas
    mensaje_ia = (
        f"Hola, ciudadano. Agradecemos tu reporte. Hemos clasificado tu incidencia en la categoría de "
        f"{categoria} con el folio institucional {folio_generado}. Tu solicitud ha sido canalizada a la "
        f"{dependencia} con un nivel de despacho clasificado como {prioridad}. El tiempo estimado para la "
        f"inspección física y atención en sitio es de {eta}. Puedes usar este folio para verificar avances."
    )

    # Registro y escritura en memoria de datos
    REPORTES_DB[folio_generado] = {
        "folio": folio_generado,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "dependencia": dependencia,
        "prioridad": prioridad,
        "prioridad_clase": prioridad_clase,
        "eta": eta,
        "estado": "🟡 En proceso" if tracking_level != "resuelto" else "🟢 Resuelto",
        "tracking_level": tracking_level,
        "mensaje": mensaje_ia,
        "ubicacion": ubicacion
    }

    return jsonify({
        "status": "success",
        "data": REPORTES_DB[folio_generado]
    }), 201


@app.route("/api/reportes/<folio>", methods=["GET"])
def obtener_reporte(folio):
    """
    Ruta de lectura para la consulta por número de folio en el buscador.
    """
    reporte_encontrado = REPORTES_DB.get(folio.strip().upper())
    
    if not reporte_encontrado:
        return jsonify({"status": "error", "message": "Folio inexistente"}), 404

    return jsonify({
        "status": "success",
        "data": reporte_encontrado
    }), 200


# =========================================================================
# ⚙️ CONFIGURACIÓN DE ARRANQUE LOCAL
# =========================================================================
if __name__ == "__main__":
    # Arranca el servidor local expuesto en el puerto 5000 con Hot-Reload activo
    app.run(debug=True, port=5000)