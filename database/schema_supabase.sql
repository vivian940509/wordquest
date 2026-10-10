-- WordQuest Supabase schema. Run in Supabase SQL Editor.
create extension if not exists pgcrypto;

create table if not exists public.users_profile (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique references auth.users(id) on delete cascade,
  username text not null default '見習勇者', level int not null default 1, exp int not null default 0,
  hp int not null default 100, coins int not null default 0, current_streak int not null default 1,
  streak_freezes int not null default 0, last_login date not null default current_date,
  unlocked_chapter int not null default 1, equipped_gear text not null default '', created_at timestamptz not null default now()
);
create table if not exists public.user_vocabulary (
  id bigserial primary key, user_id uuid not null references public.users_profile(id) on delete cascade,
  word text not null, proficiency_level int not null default 0 check (proficiency_level between 0 and 5),
  next_review_time timestamptz not null default now(), mistake_count int not null default 0,
  correct_count int not null default 0, weak_word boolean not null default false, last_wrong_at timestamptz,
  last_seen_at timestamptz not null default now(), unique(user_id, word)
);
create table if not exists public.answer_history (
  id bigserial primary key, user_id uuid not null references public.users_profile(id) on delete cascade,
  chapter_id int, stage_id int, difficulty text, mode text, prompt text, selected_answer text,
  correct_answer text, is_correct boolean not null, response_ms int not null default 0, speech_score int,
  created_at timestamptz not null default now()
);
create table if not exists public.stage_progress (
  user_id uuid not null references public.users_profile(id) on delete cascade, stage_id int not null,
  stars int not null default 0 check (stars between 0 and 3), best_score int not null default 0,
  completed boolean not null default false, attempts int not null default 0, updated_at timestamptz not null default now(),
  primary key(user_id, stage_id)
);
create table if not exists public.daily_progress (
  user_id uuid not null references public.users_profile(id) on delete cascade, progress_date date not null default current_date,
  correct_answers int not null default 0, speech_attempts int not null default 0, review_attempts int not null default 0,
  claimed_json jsonb not null default '[]'::jsonb, primary key(user_id, progress_date)
);
create table if not exists public.user_items (
  user_id uuid not null references public.users_profile(id) on delete cascade, item_key text not null,
  quantity int not null default 1, equipped boolean not null default false, acquired_at timestamptz not null default now(),
  primary key(user_id, item_key)
);
create table if not exists public.challenges (
  code text primary key, creator_user_id uuid not null references public.users_profile(id) on delete cascade,
  chapter_id int not null, stage_id int, seed bigint not null, created_at timestamptz not null default now(),
  expires_at timestamptz default (now() + interval '7 days')
);
create table if not exists public.challenge_results (
  id bigserial primary key, code text not null references public.challenges(code) on delete cascade,
  user_id uuid not null references public.users_profile(id) on delete cascade, username text not null,
  correct_count int not null default 0, total_questions int not null default 0, elapsed_ms int not null default 0,
  max_combo int not null default 0, created_at timestamptz not null default now()
);
create index if not exists idx_vocab_due on public.user_vocabulary(user_id, next_review_time);
create index if not exists idx_history_user_created on public.answer_history(user_id, created_at desc);

alter table public.users_profile enable row level security;
alter table public.user_vocabulary enable row level security;
alter table public.answer_history enable row level security;
alter table public.stage_progress enable row level security;
alter table public.daily_progress enable row level security;
alter table public.user_items enable row level security;
alter table public.challenges enable row level security;
alter table public.challenge_results enable row level security;

-- These policies apply when you later switch from server-side DB access to Supabase Auth/JWT.
do $$ begin
  create policy "profile owner" on public.users_profile for all using (auth.uid() = auth_user_id) with check (auth.uid() = auth_user_id);
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "vocab owner" on public.user_vocabulary for all using (user_id in (select id from public.users_profile where auth_user_id = auth.uid())) with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "history owner" on public.answer_history for all using (user_id in (select id from public.users_profile where auth_user_id = auth.uid())) with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "progress owner" on public.stage_progress for all using (user_id in (select id from public.users_profile where auth_user_id = auth.uid())) with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "daily owner" on public.daily_progress for all using (user_id in (select id from public.users_profile where auth_user_id = auth.uid())) with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "items owner" on public.user_items for all using (user_id in (select id from public.users_profile where auth_user_id = auth.uid())) with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "challenges readable" on public.challenges for select using (true);
exception when duplicate_object then null; end $$;
do $$ begin
  create policy "challenge results readable" on public.challenge_results for select using (true);
exception when duplicate_object then null; end $$;

create table if not exists public.user_achievements (
  user_id uuid not null references public.users_profile(id) on delete cascade,
  achievement_key text not null, earned_at timestamptz not null default now(),
  primary key(user_id, achievement_key)
);
alter table public.user_achievements enable row level security;
do $$ begin
  create policy "achievements owner" on public.user_achievements for all
  using (user_id in (select id from public.users_profile where auth_user_id = auth.uid()))
  with check (user_id in (select id from public.users_profile where auth_user_id = auth.uid()));
exception when duplicate_object then null; end $$;


-- Safe migration for existing projects
alter table public.user_vocabulary add column if not exists weak_word boolean not null default false;
alter table public.user_vocabulary add column if not exists last_wrong_at timestamptz;
update public.user_vocabulary set weak_word = (mistake_count >= 3);
