-- A pilot has explicit coverage; purchases outside it remain unqueried.
CREATE TABLE IF NOT EXISTS asktrace.contract_runs (
    run_id uuid PRIMARY KEY,
    parent_run_id uuid NOT NULL REFERENCES asktrace.ingestion_runs(run_id),
    manifest_sha256 text NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    quality jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS asktrace.contract_coverage (
    run_id uuid NOT NULL REFERENCES asktrace.contract_runs(run_id),
    parent_run_id uuid NOT NULL,
    purchase_id text NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('with_contracts', 'none_returned')),
    body_sha256 text NOT NULL CHECK (body_sha256 ~ '^[0-9a-f]{64}$'),
    contracts_count integer NOT NULL CHECK (contracts_count >= 0),
    PRIMARY KEY (run_id, purchase_id),
    FOREIGN KEY (parent_run_id, purchase_id) REFERENCES asktrace.purchases(run_id, control_id),
    CHECK ((outcome = 'none_returned') = (contracts_count = 0))
);
CREATE TABLE IF NOT EXISTS asktrace.contracts (
    run_id uuid NOT NULL REFERENCES asktrace.contract_runs(run_id),
    contract_id text NOT NULL,
    parent_run_id uuid NOT NULL,
    purchase_id text NOT NULL,
    initial_value numeric(38,8) CHECK (initial_value >= 0),
    global_value numeric(38,8) CHECK (global_value >= 0),
    source_record_index integer NOT NULL CHECK (source_record_index >= 0),
    PRIMARY KEY (run_id, contract_id),
    FOREIGN KEY (run_id, purchase_id) REFERENCES asktrace.contract_coverage(run_id, purchase_id),
    FOREIGN KEY (parent_run_id, purchase_id) REFERENCES asktrace.purchases(run_id, control_id)
);
