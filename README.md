# Lab 4: Size and containerize

**Part 3 · Lessons 9, 10 and 11 · about 2 hours · automatically checked**

## Goals

- Size a service with Little's law and the occupancy rate, before the first user arrives.
- Package a small search service into an image, and run it with its database using Docker Compose.

## Before you start

You need Python 3.12, Git and Docker (Docker Desktop on Windows and macOS, or Docker Engine with the Compose plugin on Linux). Check Docker with `docker version` and `docker compose version`. Create your own copy of this lab (**Use this template** on GitHub), clone it, then:

```bash
python -m venv .venv
# macOS / Linux: source .venv/bin/activate      Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q          # most checks fail at first: that is expected
```

Rules for every lab: one Git repository, one commit per step, your answers in `REPORT.md`, and no secret in Git.

The checks on your machine read your files and do not need Docker. On GitHub, a second job really builds your image, runs it, and starts everything with `docker compose up`.

## Part A: Size the service

One copy of the agent handles **4 questions at the same time**. You want to know how many copies to run.

Little's law says that the average number of questions in progress is the arrival rate times the time each question spends in the system: **L = λ × W**. Put λ and W in the same unit of time: the rates below are per minute, the durations in seconds.

1. For each case, compute L, then the number of copies needed without margin (L / 4, rounded up) and with a 25% margin (L × 1.25 / 4, rounded up):
   - Case 1: 6 questions per minute, 40 seconds each.
   - Case 2: 30 questions per minute, 90 seconds each.
   - Case 3: case 2 on a day the model provider slows down, and each analysis takes 180 seconds.
2. Look at case 3. Where is the bottleneck on that day? Does starting more copies solve it?
3. The occupancy rate ρ is the share of the slots that is busy on average: ρ = L / (copies × 4). A simple queue model gives the average wait before a question starts: **wait = ρ / (1 − ρ) × task duration**. Compute the wait in case 1 with one copy, then with two copies.
4. Write the four functions of `sizing.py`: `in_progress`, `copies`, `occupancy` and `wait_seconds`. Their docstrings say exactly what they take and return. `copies` rounds up (`math.ceil`), and `wait_seconds` returns `math.inf` when ρ ≥ 1.
5. Run `python sizing.py`: it prints the table for the three cases. Check it against your hand calculations, then run `pytest -q`.

Write your numbers and your explanation in `REPORT.md` (A1 to A4). Show the formula with the numbers, not only the result.

## Part B: Containerize the service

The folder `app/` holds a small search service, ready to run. You do not write its code. It reads the database address from the environment variable `DATABASE_URL` and its port from `PORT` (default 8000). It answers two routes:

- `GET /health`: `200` if the database answers, `503` if it does not.
- `GET /search?q=cache`: the documents that match the words of `q`.

Your job is to package it so that `docker compose up` starts everything on any machine with Docker, with no other step.

1. **Pin the dependencies.** In `app/requirements.txt`, pin every line to one exact version (`name==1.2.3`). `pip index versions fastapi` lists the versions that exist. Pick versions that are not brand new.
2. **Write `.dockerignore`.** Exclude at least `.env` (your secrets), `.venv` (your virtualenv) and `data/` (local data). Everything that is not excluded is sent to Docker when you build.
3. **Write the `Dockerfile`.** Start `FROM python:3.12-slim`. Copy `app/requirements.txt` alone and install it with pip **before** you copy the code: that order is what makes rebuilds fast. Then copy `app/`, create a user that is not root and switch to it with `USER`, and start the service with `CMD ["python", "-m", "app.main"]`. Never write a password or a `DATABASE_URL` in the Dockerfile.
4. **Build and check the user:**
   ```bash
   docker build -t lab04-search .
   docker run --rm --entrypoint id lab04-search -u     # must not print 0
   ```
5. **Write `docker-compose.yml`** with two services:
   - `app`: built from this folder (`build: .`), port `"8000:8000"`, with `DATABASE_URL` and `PORT` in its environment.
   - `db`: the image `pgvector/pgvector:pg16`, with `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB`, and a **named volume** mounted at `/var/lib/postgresql/data`.

   Then run `docker compose up --build` and open http://localhost:8000/health and http://localhost:8000/search?q=cache. Stop with Ctrl+C, or `docker compose down` (add `-v` to also delete the volume and its data).
6. **Time a rebuild.** Note how long the first build takes. Change one line of code (the `VERSION` line in `app/main.py`), then rebuild and time it:
   ```bash
   time docker compose build                      # macOS / Linux
   Measure-Command { docker compose build }       # Windows PowerShell
   ```
   Run `docker compose up` again and check that `/health` shows the new version.

Answer B1 to B4 in `REPORT.md`, then run `pytest -q` until every check passes.

About the database password: `docker-compose.yml` is in Git, so anything you write in it is public. A password that only protects a database on your own laptop is acceptable there. A real one is not: read it from the environment instead, with a local default, like `${POSTGRES_PASSWORD:-local-dev-only}`, and put the real value in a `.env` file that Git ignores.

## Deliverable and success criteria

- `sizing.py` written, and Part A of `REPORT.md` completed with your calculations.
- `app/requirements.txt` pinned, plus your `Dockerfile`, `docker-compose.yml` and `.dockerignore`.
- **Success:** `docker compose up` starts everything on another machine, with no other step. The image does not run as root and contains no secret. `pytest -q` is all green.
- Each time you push, GitHub runs the same checks plus the Docker job (the **Actions** tab shows a green or red mark for each).

**Going further:** the model provider caps you at 60 analyses running at the same time. On the slow day of case 3, how many questions per minute can you serve at most, however many copies you start? Then look at the size of your image with `docker images lab04-search`, and find what takes the space.

Stuck? Open `HINTS.md`: three hints, from gentle to almost the answer.
