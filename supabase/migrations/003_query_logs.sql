-- 003_query_logs.sql
-- Table to store telemetry and evaluation metrics for RAG queries
create table if not exists public.query_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    document_id uuid references public.documents(id) on delete cascade not null,
    question text not null,
    retrieved jsonb,
    answer text,
    latency_ms int,
    created_at timestamptz default now() not null
);

-- Indexes for performance
create index if not exists idx_query_logs_user_id on public.query_logs(user_id);
create index if not exists idx_query_logs_document_id on public.query_logs(document_id);

-- Enable RLS
alter table public.query_logs enable row level security;

-- Policies
create policy "Users can view their own query logs"
    on public.query_logs for select
    using (auth.uid() = user_id);

create policy "Users can insert their own query logs"
    on public.query_logs for insert
    with check (auth.uid() = user_id);
