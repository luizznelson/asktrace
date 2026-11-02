-- Initial ingestion ledger. Domain tables follow the verified source contract.
CREATE SCHEMA IF NOT EXISTS asktrace;
CREATE TABLE IF NOT EXISTS asktrace.ingestion_runs (
    run_id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    source text NOT NULL CHECK (source = 'pncp'),
    date_start date NOT NULL,
    date_end date NOT NULL CHECK (date_end >= date_start),
    scope jsonb NOT NULL CHECK (jsonb_typeof(scope) = 'object'),
    status text NOT NULL CHECK (status IN ('running', 'complete', 'failed')),
    manifest_sha256 text CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (status <> 'complete' OR manifest_sha256 IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS asktrace.source_pages (
    run_id uuid NOT NULL REFERENCES asktrace.ingestion_runs(run_id),
    resource text NOT NULL,
    request_sha256 text NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    page_number integer NOT NULL CHECK (page_number >= 1),
    fetched_at timestamptz NOT NULL,
    body_sha256 text NOT NULL CHECK (body_sha256 ~ '^[0-9a-f]{64}$'),
    relative_path text NOT NULL,
    records_count integer NOT NULL CHECK (records_count >= 0),
    PRIMARY KEY (run_id, resource, request_sha256, page_number)
);
