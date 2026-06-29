-- Run once in Supabase → SQL Editor

create table if not exists public.feedback (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  message text not null,
  predicted_action text not null,
  predicted_verdict text not null,
  user_rating text not null check (user_rating in ('correct', 'wrong')),
  correct_label text check (correct_label in ('safe', 'suspicious', 'scam')),
  source text not null default 'api',
  merged boolean not null default false
);

create index if not exists feedback_unmerged_wrong_idx
  on public.feedback (merged, user_rating)
  where merged = false and user_rating = 'wrong';

alter table public.feedback enable row level security;

-- API (publishable/anon key) can insert feedback from the demo client.
create policy "Allow public feedback inserts"
  on public.feedback
  for insert
  to anon, authenticated
  with check (true);

-- Retrain job uses the service role key, which bypasses RLS.
