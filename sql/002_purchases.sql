-- Explicit migration; no volume deletion is needed.
CREATE TABLE IF NOT EXISTS asktrace.organizations (
    run_id uuid NOT NULL REFERENCES asktrace.ingestion_runs(run_id),
    cnpj text NOT NULL CHECK (cnpj ~ '^[0-9]{14}$'),
    name text,
    PRIMARY KEY (run_id, cnpj)
);
CREATE TABLE IF NOT EXISTS asktrace.purchases (
    run_id uuid NOT NULL REFERENCES asktrace.ingestion_runs(run_id),
    control_id text NOT NULL,
    org_cnpj text NOT NULL,
    org_name text,
    unit_code text,
    municipality_ibge text,
    municipality_name text,
    uf text NOT NULL CHECK (uf = 'PI'),
    modality integer NOT NULL CHECK (modality = 6),
    publication_date date NOT NULL,
    object_text text,
    estimated_value numeric(38,8) CHECK (estimated_value >= 0),
    awarded_value numeric(38,8) CHECK (awarded_value >= 0),
    source_body_sha256 text NOT NULL CHECK (source_body_sha256 ~ '^[0-9a-f]{64}$'),
    source_record_index integer NOT NULL CHECK (source_record_index >= 0),
    PRIMARY KEY (run_id, control_id),
    FOREIGN KEY (run_id, org_cnpj) REFERENCES asktrace.organizations(run_id, cnpj)
);
CREATE INDEX IF NOT EXISTS purchases_municipality_date ON asktrace.purchases(municipality_ibge, publication_date);

-- Default analysis surface excludes historical samples and synthetic tests.
CREATE OR REPLACE VIEW asktrace.live_purchases AS
SELECT p.* FROM asktrace.purchases p
JOIN asktrace.ingestion_runs r USING (run_id)
WHERE r.status = 'complete' AND r.scope->>'mode' = 'live';
