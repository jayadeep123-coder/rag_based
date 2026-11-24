-- 005_grant_permissions.sql
-- Grant table privileges on public tables to service_role, authenticated, and anon
GRANT ALL ON TABLE public.documents TO postgres, service_role, authenticated, anon;
GRANT ALL ON TABLE public.chunks TO postgres, service_role, authenticated, anon;
GRANT ALL ON TABLE public.query_logs TO postgres, service_role, authenticated, anon;

-- Grant permissions on sequences and functions/routines
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role, authenticated, anon;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO postgres, service_role, authenticated, anon;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, service_role, authenticated, anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, service_role, authenticated, anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO postgres, service_role, authenticated, anon;

