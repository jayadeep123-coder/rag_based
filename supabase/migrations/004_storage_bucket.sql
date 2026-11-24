-- 004_storage_bucket.sql
-- Create private storage bucket 'pdfs' for uploaded user files
insert into storage.buckets (id, name, public)
values ('pdfs', 'pdfs', false)
on conflict (id) do update set public = false;

-- Storage policies to enforce folder isolation: {user_id}/{document_id}.pdf
-- Ensure users can only read, upload, update, and delete files inside their own user_id directory

create policy "Users can upload their own PDFs"
    on storage.objects for insert
    with check (
        bucket_id = 'pdfs' 
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Users can view their own PDFs"
    on storage.objects for select
    using (
        bucket_id = 'pdfs' 
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Users can update their own PDFs"
    on storage.objects for update
    using (
        bucket_id = 'pdfs' 
        and auth.uid()::text = (storage.foldername(name))[1]
    )
    with check (
        bucket_id = 'pdfs' 
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Users can delete their own PDFs"
    on storage.objects for delete
    using (
        bucket_id = 'pdfs' 
        and auth.uid()::text = (storage.foldername(name))[1]
    );
