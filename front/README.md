# Frontend

Next.js frontend for Xiaobaicai Space.

This app provides:

- public pages for the homepage and blog
- an admin console for logging in, managing posts, categories, tags, and settings
- a frontend-to-backend integration against the FastAPI API under `/api/v1`

## Stack

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- Framer Motion
- Lucide React

## Before You Start

The frontend depends on the backend API.

Default API base:

```text
http://127.0.0.1:8001/api/v1
```

If your backend is not running, the public pages will still render, but dynamic data such as site config, posts, and admin data will be empty.

## Install

```powershell
cd front
npm install
```

## Run In Development

```powershell
cd front
npm run dev
```

Open:

```text
http://localhost:3000
```

Current dev script uses Webpack instead of Turbopack to avoid the resolver issues that were previously causing runaway Node processes.

## Environment Variables

Create a `.env.local` file in the frontend root when you need to override the backend URL.

Example:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Use this when:

- your backend runs on a different port such as `8000`
- you want to point the frontend at a remote API
- you want correct metadata URLs in development or deployment

If the backend runs on `8000`, set:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

## Available Scripts

- `npm run dev`: start the development server
- `npm run build`: create a production build
- `npm run start`: run the production build
- `npm run lint`: run ESLint

## Page Map

- `/`: homepage
- `/blog`: public article list
- `/blog/[slug]`: public article detail
- `/admin`: admin login and dashboard
- `/admin/posts/new`: create a new article
- `/admin/categories`: manage categories
- `/admin/tags`: manage tags
- `/admin/settings`: manage site settings

## What Each Page Does

### Home

The homepage shows:

- a hero section
- site subtitle from backend site config if available
- a quick snapshot of published posts

When the database is empty, the page still works but shows fallback copy and empty stats.

### Blog

The blog page lists public posts only.

Important behavior:

- only published posts appear here
- draft posts do not appear here
- if there are no published posts, the page shows `No articles published yet.`

### Admin

The admin page is the real entry point for operating the project.

It supports:

- logging in with a backend user account
- reading dashboard stats
- listing posts including drafts
- navigating to category, tag, settings, and article creation pages

The admin console requires a backend user whose role is `admin`.

## First-Time Use With An Empty Database

If the database is empty, the best workflow is:

1. start the backend API
2. start the frontend
3. create a user in the backend API docs
4. promote that user to `admin` in the database
5. log in at `/admin`
6. create categories and tags
7. create your first article and set its status to `Published`
8. open `/blog` to verify the article is public

### 1. Start The Backend

From the backend folder:

```powershell
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
```

Open API docs:

```text
http://127.0.0.1:8001/docs
```

### 2. Create The First User

Use `POST /api/v1/users` in the backend docs.

Example payload:

```json
{
	"username": "admin",
	"email": "admin@example.com",
	"password": "12345678",
	"avatar": null,
	"bio": "first admin",
	"social_links": {}
}
```

### 3. Promote The User To Admin

The public user creation API creates a normal user by default.

For the first admin account, update the database manually:

```sql
UPDATE users
SET role = 'admin'
WHERE username = 'admin';
```

After that, log in at:

```text
http://localhost:3000/admin
```

### 4. Create Initial Content

Recommended order:

1. go to `/admin/posts/new`
2. create a category if none exists
3. create tags if none exist
4. write title, summary, and content
5. set status to `Published`
6. save the article
7. verify it appears in `/blog`

## Admin Usage Notes

### Authentication

- login uses the backend endpoint `POST /users/login`
- the frontend stores the access token in `localStorage`
- admin requests send `Authorization: Bearer <token>`

### Categories And Tags

You can manage categories and tags from their own admin pages.

You can also create them directly from the new article page using the inline `New` actions.

### Settings

The settings page edits backend settings rows that already exist.

Important limitation:

- if the `settings` table is empty, the settings page may show no items
- the public site config still falls back to defaults when no settings exist

Common backend setting keys used by the frontend include:

- `site.title`
- `site.subtitle`
- `site.description`
- `site.icp_beian`
- `site.social_links`
- `site.footer.text`
- `site.footer.copyright`
- `site.footer.links`

## API Integration Notes

Public frontend data comes from endpoints such as:

- `GET /site-config`
- `GET /posts`
- `GET /posts/slug/{slug}`
- `POST /posts/slug/{slug}/like`

Admin frontend data comes from endpoints such as:

- `POST /users/login`
- `GET /admin/dashboard`
- `GET /admin/posts`
- `POST /admin/posts`
- `GET /admin/categories`
- `POST /admin/categories`
- `GET /admin/tags`
- `POST /admin/tags`
- `GET /admin/settings`
- `PUT /admin/settings/{key}`

## Troubleshooting

### The frontend shows empty content

Check these first:

1. the backend is running
2. the backend port matches `NEXT_PUBLIC_API_URL`
3. there is at least one published post

### `/blog` is empty after creating a post

Make sure the post status is `Published`, not `Draft`.

### Admin login fails

Check these first:

1. the user exists in the backend database
2. the password is correct
3. the user role is `admin`
4. the backend API is reachable from the frontend

### The site config does not change

If the settings table has no rows, the frontend falls back to default values. Add or update the expected keys in the backend settings data.

## Suggested First Content

If you just want to make the app feel alive quickly, create:

### Categories

- Backend
- Frontend
- Notes

### Tags

- fastapi
- nextjs
- mysql
- architecture
- devlog

### First Article

- Title: `Bootstrapping Xiaobaicai Space`
- Slug: `bootstrapping-xiaobaicai-space`
- Summary: `A short walkthrough of the first setup, admin workflow, and content publishing path.`
- Status: `Published`

## Project Structure

```text
front/
	app/
		admin/
		blog/
		globals.css
		layout.tsx
		page.tsx
	components/
		blog/
		layout/
		ui/
	lib/
		api/
	public/
```

## Related Docs

- root project overview: `../readme.md`
- backend setup and API details: `../backend/README.md`
