-- Supabase schema scaffolding for personal_chatbot
-- This is a placeholder aligned with docs/data-structures.md and integration-architecture.md
-- Actual constraints, RLS policies, and indexes will be completed during implementation.

create schema if not exists chatbot;

-- Users table (reference to auth.users typically in Supabase; local mirror for app metadata)
create table if not exists chatbot.app_users (
  id uuid primary key,
  display_name text,
  created_at timestamptz not null default now()
);

-- Conversations table
create table if not exists chatbot.conversations (
  id uuid primary key,
  user_id uuid not null references chatbot.app_users(id) on delete cascade,
  title text,
  created_at timestamptz not null default now()
);

-- Messages table
create table if not exists chatbot.messages (
  id uuid primary key,
  conversation_id uuid not null references chatbot.conversations(id) on delete cascade,
  user_id uuid not null references chatbot.app_users(id) on delete cascade,
  role text not null check (role in ('user','assistant','system','tool')),
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Memories table
create table if not exists chatbot.memories (
  id uuid primary key,
  user_id uuid not null references chatbot.app_users(id) on delete cascade,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Basic indexes (to be refined)
create index if not exists idx_conversations_user_id on chatbot.conversations(user_id);
create index if not exists idx_messages_conversation_id on chatbot.messages(conversation_id);
create index if not exists idx_messages_user_id_created on chatbot.messages(user_id, created_at desc);
create index if not exists idx_memories_user_id_created on chatbot.memories(user_id, created_at desc);