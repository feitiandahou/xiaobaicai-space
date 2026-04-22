-- src/schema.sql

-- Create a table for blog posts
create table public.posts (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  slug text not null unique,
  summary text,
  content text not null,
  cover_image text,
  tags text[] not null default '{}'::text[],
  is_published boolean default false,
  likes integer default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create or replace function public.increment_post_likes(post_slug text)
returns table (likes integer)
language plpgsql
as $$
begin
  return query
  update public.posts
  set likes = coalesce(public.posts.likes, 0) + 1,
      updated_at = timezone('utc'::text, now())
  where public.posts.slug = post_slug
    and public.posts.is_published = true
  returning public.posts.likes;
end;
$$;

-- Set up Row Level Security (RLS)
-- We will handle auth in our FastAPI backend using the Service Role Key for Admin operations
-- and anon key for public read access. However, since we proxy through FastAPI, 
-- FastAPI needs to use the Service Role key to bypass RLS, or we can just disable RLS on this table
-- considering FastAPI acts as the boundary.
alter table public.posts disable row level security;
