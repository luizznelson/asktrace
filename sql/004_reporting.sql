-- The runtime login receives SELECT on these views only, never table write privileges.
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'asktrace_reader') THEN
        CREATE ROLE asktrace_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;
ALTER ROLE asktrace_reader SET default_transaction_read_only = on;
ALTER ROLE asktrace_reader SET statement_timeout = '10s';
GRANT USAGE ON SCHEMA asktrace TO asktrace_reader;
CREATE OR REPLACE VIEW asktrace.report_purchases AS
SELECT p.* FROM asktrace.live_purchases p;
CREATE OR REPLACE VIEW asktrace.report_coverage AS
SELECT c.* FROM asktrace.contract_coverage c
JOIN asktrace.ingestion_runs r ON r.run_id=c.parent_run_id
WHERE r.status='complete' AND r.scope->>'mode'='live';
CREATE OR REPLACE VIEW asktrace.report_contracts AS
SELECT c.* FROM asktrace.contracts c
JOIN asktrace.ingestion_runs r ON r.run_id=c.parent_run_id
WHERE r.status='complete' AND r.scope->>'mode'='live';
GRANT SELECT ON asktrace.report_purchases, asktrace.report_coverage,
    asktrace.report_contracts TO asktrace_reader;
