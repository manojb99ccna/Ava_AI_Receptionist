# Ava AI Receptionist

## Run with Docker (recommended)

```bash
docker compose up -d --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5180        |
| Backend  | http://localhost:8310        |
| API docs | http://localhost:8310/docs   |
| Admin    | http://localhost:5180/admin  |
| phpMyAdmin | http://localhost:8320 (user `ava` / `ava_secret`, or `root` / `root_secret`) |
| MySQL    | host `127.0.0.1`, port `3325`, db `ava_ai`, user `ava` / `ava_secret` |

Default admin login: `admin` / `admin123` (set in `backend/.env`, created on first start).
Admin passwords are stored as MD5 hashes in the `admins` table.

Source folders are mounted into the containers, so code changes hot-reload.

```bash
docker compose logs -f     # follow logs
docker compose down        # stop
```

After changing `requirements.txt` or `package.json`, rebuild with `docker compose up -d --build`.

## Run locally (without Docker)

```bash
# backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```
