# Lab 4 hints

Read one hint at a time.

<details>
<summary>Hint 1: the units, and what "a copy" means</summary>

Little's law only works when λ and W use the same unit. 6 questions per minute is 0.1 question per second; times 40 seconds, that is 4 questions in progress on average. One copy has 4 slots, so 4 questions fill exactly one copy.

You cannot start a quarter of a copy: always round **up**. `math.ceil(11.25)` is 12. Be careful with `int(x) + 1`: it gives 3 for exactly 2.0.

In case 3, the duration doubles, so L doubles. Ask yourself who made the analyses slower, and whether a new copy of *your* service makes the provider answer faster.

</details>

<details>
<summary>Hint 2: why the order of the Dockerfile matters</summary>

Each instruction of a Dockerfile makes a layer. When you rebuild, Docker reuses a layer from its cache as long as nothing changed in that instruction and in everything above it. As soon as one layer changes, every layer below it is rebuilt.

So put what changes rarely at the top (the base image, the user, the dependencies) and what changes often at the bottom (your code). If you `COPY . .` before `pip install`, every code change reinstalls every dependency.

In `docker-compose.yml`, each service is reachable from the others by its **service name**. Inside the app container, `localhost` is the app container itself, not the database.

</details>

<details>
<summary>Hint 3: almost the answer</summary>

A Dockerfile in the right order:

```dockerfile
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 appuser
WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app.main"]
```

The skeleton of `docker-compose.yml` (fill in the environment of each service):

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      PORT: "8000"
      DATABASE_URL: postgresql://<user>:<password>@<database service name>:5432/<database>
    depends_on:
      - db
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ...
      POSTGRES_PASSWORD: ...
      POSTGRES_DB: ...
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

The user, password and database name must be the same in `DATABASE_URL` and in the `db` service. The database takes a few seconds to start: if `/health` answers `503` at first, wait and reload.

</details>
