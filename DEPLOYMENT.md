# WordQuest Deployment

This project is ready for GitHub + Vercel + Supabase.

## 1. Push To GitHub

Repository:

```text
https://github.com/vivian940509/wordquest.git
```

The local `.gitignore` excludes `.env`, Python caches, pytest caches, and the local SQLite database at `database/*.db`.

## 2. Create Supabase Tables

1. Open your Supabase project.
2. Go to SQL Editor.
3. Paste and run:

```text
database/schema_supabase.sql
```

The app uses `DATABASE_URL` from the server environment. Do not put the database password or `service_role` key in frontend JavaScript.

## 3. Supabase Connection String

In Supabase:

1. Go to Project Settings > Database.
2. Copy the PostgreSQL connection string.
3. Prefer the pooler connection string for Vercel serverless deployments.
4. Keep `sslmode=require` in the URL.

Example format:

```text
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:6543/postgres?sslmode=require
```

## 4. Import Into Vercel

1. Open Vercel.
2. Add New Project.
3. Import `vivian940509/wordquest`.
4. Framework Preset: Other.
5. Build Command: leave empty.
6. Output Directory: leave empty.

`vercel.json` routes every request to `app.py`.

## 5. Vercel Environment Variables

Add these in Vercel Project Settings > Environment Variables:

```text
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[HOST]:6543/postgres?sslmode=require
SECRET_KEY=use-a-long-random-secret
APP_TIMEZONE=Asia/Taipei
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

`AI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY` are optional for the current guest-session version.

## 6. Deploy

After setting the environment variables, deploy the Vercel project. If you later change code, push to GitHub and Vercel will redeploy automatically.

## Google OAuth / Password reset
After deployment, add the production URLs to Supabase Authentication > URL Configuration > Redirect URLs:
- `https://<your-domain>/auth/google/callback`
- `https://<your-domain>/reset-password`

Enable the Google provider in Supabase. In Google Cloud, the authorized OAuth callback must be the Supabase callback URL shown by the provider settings (normally `https://<project-ref>.supabase.co/auth/v1/callback`).

If upgrading an existing database, run the latest `database/schema_supabase.sql` once to add the weak-word fields used by the upgraded mistake center.
