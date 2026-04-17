alter table public.posts
add column if not exists tags text[] not null default '{}'::text[];

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