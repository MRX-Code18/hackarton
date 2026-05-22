-- ================================================================
--  PLATAFORMA DE REPORTES — Schema Supabase (sin ENUMs)
--  Pega esto en el SQL Editor de Supabase y ejecuta todo.
-- ================================================================

-- Borra las tablas si existían (útil para re-ejecutar limpio)
DROP TABLE IF EXISTS historial_estatus CASCADE;
DROP TABLE IF EXISTS reportes CASCADE;

-- ----------------------------------------------------------------
-- TABLA PRINCIPAL: reportes
-- ----------------------------------------------------------------
CREATE TABLE reportes (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    folio               TEXT        UNIQUE NOT NULL,
    descripcion         TEXT        NOT NULL,
    ubicacion           TEXT        NOT NULL,
    foto_url            TEXT,
    categoria           TEXT        NOT NULL,
    prioridad           TEXT        NOT NULL,           -- 'Alta' | 'Media' | 'Normal'
    prioridad_num       SMALLINT    NOT NULL,           -- 2 | 3 | 4
    mensaje_ia          TEXT        NOT NULL,
    estatus             TEXT        NOT NULL DEFAULT 'Recibido',
    progreso_porcentaje SMALLINT    NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------
-- TABLA DE AUDITORÍA: historial_estatus
-- ----------------------------------------------------------------
CREATE TABLE historial_estatus (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    reporte_id          UUID        NOT NULL REFERENCES reportes(id) ON DELETE CASCADE,
    folio               TEXT        NOT NULL,
    estatus_anterior    TEXT,
    estatus_nuevo       TEXT        NOT NULL,
    progreso_porcentaje SMALLINT    NOT NULL,
    nota                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ----------------------------------------------------------------
-- TRIGGERS
-- ----------------------------------------------------------------

-- Actualiza updated_at automáticamente
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reportes_updated_at
    BEFORE UPDATE ON reportes
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Registra cada cambio de estatus en historial_estatus
CREATE OR REPLACE FUNCTION fn_log_cambio_estatus()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF (TG_OP = 'INSERT') OR (OLD.estatus IS DISTINCT FROM NEW.estatus) THEN
        INSERT INTO historial_estatus (
            reporte_id, folio, estatus_anterior, estatus_nuevo, progreso_porcentaje
        ) VALUES (
            NEW.id,
            NEW.folio,
            CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.estatus END,
            NEW.estatus,
            NEW.progreso_porcentaje
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_log_estatus_insert
    AFTER INSERT ON reportes
    FOR EACH ROW EXECUTE FUNCTION fn_log_cambio_estatus();

CREATE TRIGGER trg_log_estatus_update
    AFTER UPDATE OF estatus ON reportes
    FOR EACH ROW EXECUTE FUNCTION fn_log_cambio_estatus();

-- ----------------------------------------------------------------
-- ÍNDICES
-- ----------------------------------------------------------------
CREATE INDEX idx_reportes_folio      ON reportes (folio);
CREATE INDEX idx_reportes_estatus    ON reportes (estatus);
CREATE INDEX idx_reportes_created_at ON reportes (created_at DESC);
CREATE INDEX idx_historial_folio     ON historial_estatus (folio);

-- ----------------------------------------------------------------
-- ROW LEVEL SECURITY
-- ----------------------------------------------------------------
ALTER TABLE reportes          ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_estatus ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert_reportes"  ON reportes FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_select_reportes"  ON reportes FOR SELECT TO anon USING (true);
CREATE POLICY "service_all_reportes"  ON reportes FOR ALL   TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "anon_select_historial" ON historial_estatus FOR SELECT TO anon USING (true);
CREATE POLICY "service_all_historial" ON historial_estatus FOR ALL   TO service_role USING (true) WITH CHECK (true);

-- ----------------------------------------------------------------
-- STORAGE — bucket para fotos
-- (Si ya lo creaste desde el dashboard, ignora este bloque)
-- ----------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public)
VALUES ('fotos-reportes', 'fotos-reportes', true)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "anon_upload_fotos"  ON storage.objects FOR INSERT TO anon        WITH CHECK (bucket_id = 'fotos-reportes');
CREATE POLICY "public_read_fotos"  ON storage.objects FOR SELECT TO anon        USING     (bucket_id = 'fotos-reportes');
CREATE POLICY "service_del_fotos"  ON storage.objects FOR DELETE TO service_role USING    (bucket_id = 'fotos-reportes');

-- ----------------------------------------------------------------
-- ✅ VERIFICACIÓN FINAL
-- Debe devolver las dos tablas creadas
-- ----------------------------------------------------------------
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('reportes', 'historial_estatus');
