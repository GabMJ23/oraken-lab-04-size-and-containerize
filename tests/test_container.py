"""Automated checks for Lab 4, Part B. Run with: pytest -q

These checks read your Dockerfile, .dockerignore, docker-compose.yml and
app/requirements.txt. They do not need Docker. On GitHub, a second job
really builds and runs your image.
"""
import fnmatch
import json
import pathlib
import re
import shlex

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
COMPOSE = ROOT / "docker-compose.yml"
APP_REQUIREMENTS = ROOT / "app" / "requirements.txt"


# ---------------------------------------------------------------- helpers

def instructions():
    """The Dockerfile as a list of (INSTRUCTION, arguments), comments and line continuations handled."""
    assert DOCKERFILE.exists(), "Dockerfile is missing at the root of the lab."
    result, current = [], ""
    for raw in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not current and (not line or line.startswith("#")):
            continue
        if current and line.startswith("#"):
            continue  # a comment inside a continued instruction
        if line.endswith("\\"):
            current += line[:-1] + " "
            continue
        current += line
        if current.strip():
            word, _, rest = current.strip().partition(" ")
            result.append((word.upper(), rest.strip()))
        current = ""
    if current.strip():
        word, _, rest = current.strip().partition(" ")
        result.append((word.upper(), rest.strip()))
    return result


def copy_sources(args):
    """The source paths of a COPY/ADD instruction (flags like --chown removed, destination removed)."""
    args = args.strip()
    if args.startswith("["):
        parts = json.loads(args)
    else:
        parts = shlex.split(args)
    parts = [p for p in parts if not p.startswith("--")]
    return parts[:-1]


def is_requirements(src):
    return "requirements" in src.lower()


def is_app_code(src):
    s = src.replace("\\", "/").rstrip("/")
    return s in (".", "", "app", "./app", "/app") or s.startswith("app/") and not is_requirements(s)


def final_stage(instr):
    starts = [i for i, (word, _) in enumerate(instr) if word == "FROM"]
    assert starts, "The Dockerfile has no FROM line yet. Start with  FROM python:3.12-slim"
    return instr[starts[-1]:]


def compose():
    assert COMPOSE.exists(), "docker-compose.yml is missing at the root of the lab."
    data = yaml.safe_load(COMPOSE.read_text(encoding="utf-8")) or {}
    services = data.get("services") or {}
    assert isinstance(services, dict) and services, "docker-compose.yml has no service yet: add an app service and a db service."
    return data, services


def db_service(services):
    for name, svc in services.items():
        image = str((svc or {}).get("image", ""))
        if image.startswith("pgvector/pgvector:"):
            return name, svc
    pytest.fail("No service uses the image pgvector/pgvector:pg16. Add a db service with  image: pgvector/pgvector:pg16")


def app_service(services):
    for name, svc in services.items():
        if (svc or {}).get("build") is not None:
            return name, svc
    pytest.fail("No service is built from your Dockerfile. Give the app service  build: .")


def environment(svc):
    """A service's environment as a dict, whatever the syntax (mapping or list of KEY=value)."""
    env = (svc or {}).get("environment") or {}
    if isinstance(env, list):
        out = {}
        for item in env:
            key, _, value = str(item).partition("=")
            out[key.strip()] = value
        return out
    return {str(k): ("" if v is None else str(v)) for k, v in env.items()}


# ---------------------------------------------------------------- app/requirements.txt

def test_app_requirements_are_pinned():
    lines = [
        line.split("#")[0].strip()
        for line in APP_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
    ]
    lines = [line for line in lines if line]
    names = [re.split(r"[\[=<>~! ]", line)[0].lower() for line in lines]
    for needed in ("fastapi", "uvicorn", "psycopg"):
        assert needed in names, f"app/requirements.txt must still list {needed}: the service needs it."
    loose = [line for line in lines if not re.fullmatch(r"[A-Za-z0-9_.\-]+(\[[A-Za-z0-9_,\-]+\])?==[0-9][A-Za-z0-9.\-+!]*", line)]
    assert not loose, (
        f"These lines of app/requirements.txt are not pinned to one exact version: {loose}. "
        "Write them like  fastapi==0.115.6  (pip index versions <name> lists the versions)."
    )


# ---------------------------------------------------------------- .dockerignore

def ignore_patterns():
    assert DOCKERIGNORE.exists(), ".dockerignore is missing at the root of the lab."
    patterns = []
    for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def ignored(path, patterns):
    """Roughly how Docker decides: the last matching pattern wins, '!' re-includes."""
    result = False
    for pattern in patterns:
        negate = pattern.startswith("!")
        p = pattern[1:] if negate else pattern
        p = p.strip().lstrip("/").rstrip("/")
        if p.startswith("**/"):
            p = p[3:]
        if p.startswith("./"):
            p = p[2:]
        candidates = [path]
        parts = path.split("/")
        candidates += ["/".join(parts[:i]) for i in range(1, len(parts))]  # a parent folder excluded excludes its content
        if any(fnmatch.fnmatchcase(c, p) for c in candidates):
            result = not negate
    return result


@pytest.mark.parametrize(
    "path, why",
    [
        (".env", "your secrets"),
        (".venv/bin/python", "your virtualenv (big, and built for your machine, not for the image)"),
        ("data/dump.sql", "local data"),
    ],
    ids=[".env", ".venv", "data"],
)
def test_dockerignore_excludes(path, why):
    patterns = ignore_patterns()
    assert ignored(path, patterns), (
        f".dockerignore must exclude {path.split('/')[0]} ({why}). Add a line for it."
    )


def test_dockerignore_keeps_the_code():
    patterns = ignore_patterns()
    for path in ("app/main.py", "app/requirements.txt"):
        assert not ignored(path, patterns), (
            f".dockerignore excludes {path}, but the image needs it. Remove the pattern that matches it."
        )


# ---------------------------------------------------------------- Dockerfile

def test_dockerfile_starts_from_python_312_slim():
    instr = instructions()
    froms = [args for word, args in instr if word == "FROM"]
    assert froms, "The Dockerfile has no FROM line yet. Start with  FROM python:3.12-slim"
    image = froms[-1].split()[0]
    assert re.fullmatch(r"python:3\.12(\.\d+)?-slim(-[a-z]+)?(@sha256:[0-9a-f]{64})?", image), (
        f"The final image starts FROM {image}. Use the pinned, small official image: python:3.12-slim "
        "(never :latest, which changes under your feet)."
    )


def test_dependencies_are_installed_before_the_code_is_copied():
    instr = instructions()
    copy_req = copy_code = pip = None
    for i, (word, args) in enumerate(instr):
        if word in ("COPY", "ADD") and "--from" not in args:
            sources = copy_sources(args)
            if copy_req is None and sources and all(is_requirements(s) for s in sources):
                copy_req = i
            elif copy_code is None and any(is_app_code(s) for s in sources):
                copy_code = i
        if word == "RUN" and pip is None and "pip" in args and "install" in args and "requirements" in args:
            pip = i
    assert copy_req is not None, (
        "No COPY of app/requirements.txt on its own. Copy it alone first:  COPY app/requirements.txt ."
    )
    assert pip is not None, "No RUN pip install -r ... requirements.txt. Install the dependencies in the image."
    assert copy_code is not None, "No COPY of the code. Copy the app/ folder into the image:  COPY app/ ./app/"
    assert copy_req < pip < copy_code, (
        "Order matters for the layer cache: COPY requirements.txt, then RUN pip install, and only THEN copy the code. "
        "Otherwise every code change reinstalls every dependency."
    )


def test_image_does_not_run_as_root():
    stage = final_stage(instructions())
    users = [args.split()[0] for word, args in stage if word == "USER"]
    assert users, "No USER instruction: the container runs as root. Create a user and switch to it with USER."
    last = users[-1].split(":")[0]
    assert last not in ("root", "0"), f"The last USER is {users[-1]}: that is root. Switch to a normal user."


def test_image_has_a_start_command():
    stage = final_stage(instructions())
    assert any(word in ("CMD", "ENTRYPOINT") for word, _ in stage), (
        "No CMD (or ENTRYPOINT): the image does not say how to start the service. Add  CMD [\"python\", \"-m\", \"app.main\"]"
    )


SECRET_NAME = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_KEY|DATABASE_URL)", re.I)


def test_no_secret_in_the_dockerfile():
    instr = instructions()
    text = DOCKERFILE.read_text(encoding="utf-8")
    code = "\n".join(f"{w} {a}" for w, a in instr)  # comments removed
    assert not re.search(r"://[^/\s:@]+:[^@\s/]+@", code), (
        "The Dockerfile contains a URL with a password in it (user:password@...). "
        "Pass DATABASE_URL at run time (docker-compose.yml), never in the image."
    )
    for word, args in instr:
        if word in ("ENV", "ARG") and SECRET_NAME.search(args) and ("=" in args or len(args.split()) > 1):
            pytest.fail(
                f"`{word} {args}` puts a secret (or the database address) inside the image. "
                "Remove it and pass the value at run time through the environment."
            )
        if word in ("COPY", "ADD") and any(pathlib.PurePosixPath(s).name.startswith(".env") for s in copy_sources(args)):
            pytest.fail("The Dockerfile copies a .env file into the image. Never ship your secrets in an image.")
    assert "sk-" not in text, "The Dockerfile seems to contain an API key (sk-...). Remove it."


# ---------------------------------------------------------------- docker-compose.yml

def test_compose_has_the_app_and_the_database():
    _, services = compose()
    assert len(services) >= 2, "docker-compose.yml needs two services: the app and the database."
    app_name, _ = app_service(services)
    db_name, db = db_service(services)
    assert app_name != db_name
    image = str(db["image"])
    assert re.search(r"(^|[:\-])pg16($|-)", image.split(":", 1)[1]), (
        f"The database image is {image}. Use pgvector/pgvector:pg16 (Postgres 16 with pgvector)."
    )


def test_database_has_a_password():
    _, services = compose()
    _, db = db_service(services)
    env = environment(db)
    assert env.get("POSTGRES_PASSWORD", "").strip(), (
        "The db service has no POSTGRES_PASSWORD: the Postgres image refuses to start without one."
    )


def test_database_data_is_in_a_named_volume():
    data, services = compose()
    _, db = db_service(services)
    named = set((data.get("volumes") or {}).keys())
    assert named, "No named volume. Declare one at the end of docker-compose.yml:  volumes:\\n  pgdata:"
    mounts = []
    for v in db.get("volumes") or []:
        if isinstance(v, dict):
            mounts.append((str(v.get("source", "")), str(v.get("target", ""))))
        else:
            source, _, rest = str(v).partition(":")
            mounts.append((source, rest.split(":")[0]))
    assert any(src in named and tgt.rstrip("/") == "/var/lib/postgresql/data" for src, tgt in mounts), (
        "Mount your named volume on the db service at /var/lib/postgresql/data (for example  - pgdata:/var/lib/postgresql/data). "
        "Without it, the data disappears with the container."
    )


def test_app_gets_the_database_address_from_the_environment():
    _, services = compose()
    _, app = app_service(services)
    db_name, _ = db_service(services)
    env = environment(app)
    url = env.get("DATABASE_URL", "")
    assert url, "The app service has no DATABASE_URL in its environment: the app cannot find the database."
    match = re.search(r"@([^:/?]+)", url) or re.search(r"://([^:/?@]+)", url)
    assert match, f"DATABASE_URL = {url} does not look like postgresql://user:password@host:5432/name"
    host = match.group(1)
    assert host not in ("localhost", "127.0.0.1"), (
        f"DATABASE_URL points at {host}. Inside the app container, localhost is the app container itself. "
        f"Use the name of the database service: {db_name}"
    )
    assert host == db_name, f"DATABASE_URL points at host {host}, but the database service is called {db_name}."


def test_app_is_published_on_port_8000():
    _, services = compose()
    _, app = app_service(services)
    published = []
    for p in app.get("ports") or []:
        if isinstance(p, dict):
            published.append(str(p.get("published", "")))
        else:
            parts = str(p).split(":")
            if len(parts) >= 2:
                published.append(parts[-2])
    assert "8000" in published, (
        "Publish the app on port 8000 of your machine:  ports: [\"8000:8000\"]. The GitHub check calls http://localhost:8000/health."
    )
