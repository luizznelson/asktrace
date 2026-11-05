-- Maintenance only. Never execute schema changes from the public application.
CREATE TABLE IF NOT EXISTS asktrace.deployment_artifacts (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    body bytea NOT NULL CHECK (octet_length(body) <= 33554432)
);
GRANT SELECT ON asktrace.deployment_artifacts TO asktrace_reader;

CREATE TABLE IF NOT EXISTS asktrace.runtime_state (
    name text PRIMARY KEY CHECK (name IN ('provider-health', 'public-budget')),
    value jsonb NOT NULL CHECK (jsonb_typeof(value) = 'object')
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'asktrace_service') THEN
        CREATE ROLE asktrace_service LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END $$;
ALTER ROLE asktrace_service SET statement_timeout = '5s';
GRANT USAGE ON SCHEMA asktrace TO asktrace_service;
GRANT SELECT, INSERT, UPDATE ON asktrace.runtime_state TO asktrace_service;
