-- 002_match_chunks_function.sql
-- Vector similarity search function for RAG queries
-- Accepts p_user_id to support service-role backend execution while preserving strict user isolation.
-- If p_user_id is not passed, falls back to auth.uid() for authenticated client calls.

create or replace function match_chunks (
    query_embedding vector(768),
    match_document_id uuid,
    p_user_id uuid default null,
    match_count int default 6
)
returns table (
    id uuid,
    content text,
    page_start int,
    page_end int,
    chunk_index int,
    similarity float
)
language plpgsql
security definer
as $$
declare
    effective_user_id uuid;
begin
    effective_user_id := coalesce(p_user_id, auth.uid());
    
    if effective_user_id is null then
        raise exception 'User ID must be provided either via auth context or p_user_id parameter.';
    end if;

    return query
    select
        c.id,
        c.content,
        c.page_start,
        c.page_end,
        c.chunk_index,
        1 - (c.embedding <=> query_embedding) as similarity
    from public.chunks c
    where c.document_id = match_document_id
      and c.user_id = effective_user_id
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
