### xiaobaicai-space

a personal blog and website collection project.

using Next.js(React) and FastApi(Python)

### tech stack

#### front

next.js

react

shadecn

tailwindcss

#### backend

python

uv

fastapi

sqlalchemy

### database

mysql

## quick start

cd front

npm install

npm run dev

+++++++++++++++++++++++++++++++++++++++++

cd backend

Rename ".env.example" File to ".env" 
and fill in your database information 

uv sync

#### init database
(in mysql)
CREATE DATABASE xiaobaicai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

cd backend

uv run alembic upgrade head

uv run uvicorn app.main:app --reload

#### stop-process(windows):
In CMD: Ctrl + C
Or
Stop-Process -Name uv,uvicorn,python -Force

