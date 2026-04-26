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

### quick start

cd front

npm install

npm run dev

++++++++++

cd backend

Rename ".env.example" File to ".env" 
and fill in your database information 

import database file (backend/mysql.sql)

uv sync

uv run uvicorn app.main:app --reload

+++

stop-process(windows):
In CMD: Ctrl + C
Or
Stop-Process -Name uv,uvicorn,python -Force

