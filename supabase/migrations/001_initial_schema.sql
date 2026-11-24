-- 001_initial_schema.sql
-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Documents table to track uploaded files and processing state
create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    filename text not null,
    storage_path text not null,
    page_count int,
    status text check (status in ('uploaded', 'processing', 'ready', 'failed')) default 'uploaded',
    error text,
    created_at timestamptz default now() not null
);

-- Chunks table to store text passages and Gemini vector embeddings (default 768 dimensions)
create table if not exists public.chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references public.documents(id) on delete cascade not null,
    user_id uuid not null,
    chunk_index int not null,
    content text not null,
    page_start int not null,
    page_end int not null,
    token_estimate int,
    embedding vector(768),
    created_at timestamptz default now() not null
);

-- Indexes for performance
-- btree index on document_id for fast retrieval & cascade deletes
create index if not exists idx_chunks_document_id on public.chunks(document_id);
create index if not exists idx_chunks_user_id on public.chunks(user_id);
create index if not exists idx_documents_user_id on public.documents(user_id);

-- HNSW index for high performance approximate nearest neighbor cosine similarity search
create index if not exists idx_chunks_embedding_hnsw 
on public.chunks using hnsw (embedding vector_cosine_ops);

-- Enable Row Level Security (RLS) on both tables
alter table public.documents enable row level security;
alter table public.chunks enable row level security;

-- Documents RLS policies: Users can only manage their own documents
create policy "Users can view their own documents"
    on public.documents for select
    using (auth.uid() = user_id);

create policy "Users can insert their own documents"
    on public.documents for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own documents"
    on public.documents for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "Users can delete their own documents"
    on public.documents for delete
    using (auth.uid() = user_id);

-- Chunks RLS policies: Users can only manage their own chunks
create policy "Users can view their own chunks"
    on public.chunks for select
    using (auth.uid() = user_id);

create policy "Users can insert their own chunks"
    on public.chunks for insert
    with check (auth.uid() = user_id);

create policy "Users can update their own chunks"
    on public.chunks for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "Users can delete their own chunks"
    on public.chunks for delete
    using (auth.uid() = user_id);
