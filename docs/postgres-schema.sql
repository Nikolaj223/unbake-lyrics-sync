create table lyrics_jobs (
    job_id uuid primary key,
    status text not null check (status in ('queued', 'processing', 'completed', 'failed')),
    audio_url text not null,
    language_hint text null,
    track_name text null,
    artist_name text null,
    duration_ms integer null,
    shazam_track_id text null,
    is_custom_cover boolean not null default false,
    result jsonb null,
    error text null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index lyrics_jobs_status_created_at_idx
    on lyrics_jobs (status, created_at desc);
