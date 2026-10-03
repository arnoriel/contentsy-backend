# Contentsy Backend

FastAPI + PostgreSQL + Redis (Celery) — local dev via Docker.

## Setup Pertama Kali

```bash
cp .env.example .env
# edit .env kalau perlu (default sudah jalan langsung)

docker compose up -d
```

Cek service jalan:

```bash
docker compose ps
curl http://localhost:8001/health
```

> **Kalau punya backend project lain yang jalan bareng** (mis. Postgres/Redis project lain di local): compose file ini sudah pakai `container_name` (`contentsy_*`) dan `name: contentsy-backend` yang unik, jadi gak akan bentrok nama. Default port host juga sudah digeser (`5433`, `6380`, `8001`) supaya gak rebutan sama port default 5432/6379/8000. Kalau masih bentrok, tinggal ganti `POSTGRES_PORT` / `REDIS_PORT` / `API_PORT` di `.env` ke angka bebas lain.

## Command Dasar

| Command | Fungsi |
|---|---|
| `docker compose up -d` | Jalankan semua service (db, redis, api) di background |
| `docker compose down` | Stop & hapus container (data Postgres tetap ada, volume persist) |
| `docker compose down -v` | Stop & hapus container **+ volume** (data Postgres ikut hilang) |
| `docker compose logs -f api` | Lihat log FastAPI realtime |
| `docker compose ps` | Cek status semua service |

## Run Migration (Alembic) di Dalam Container

```bash
docker compose exec api alembic upgrade head
```

Generate migration baru (setelah ubah model — lihat BE-Azriel-01):

```bash
docker compose exec api alembic revision --autogenerate -m "pesan migrasi"
```

## Struktur Service

- `db` — PostgreSQL 16, data persist di named volume `contentsy_pgdata`
- `redis` — Redis 7, dipakai Celery sebagai broker (task BE-Azriel-01+)
- `worker` — Celery worker (broker/backend: Redis)
- `api` — FastAPI app, auto-reload saat development, depends_on `db` & `redis` dengan healthcheck (tidak start sebelum db & redis benar-benar ready)

## Setup Auth

Isi `JWT_SECRET_KEY` di `.env` (wajib, min 32 karakter): `openssl rand -hex 32`. Lalu:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
```

## API — Auth & Credit (BE-Azriel-02)

| Endpoint | Auth | Request | Response |
|---|---|---|---|
| `POST /api/auth/register` | - | `{email, password}` (password 8–128 char) | `201` `{id, email, credits, created_at}` (credits awal = 10) |
| `POST /api/auth/login` | - | `{email, password}` | `200` `{access_token, token_type: "bearer", expires_in}` |
| `GET /api/auth/me` | Bearer | - | `{id, email, credits, created_at}` |
| `GET /api/user/credits` | Bearer | - | `{credits: int}` |

Header protected endpoint: `Authorization: Bearer <access_token>`.

| Status | Kondisi |
|---|---|
| `401` | Token tidak ada / invalid / expired, atau login salah |
| `402` | Credit habis (dependency `require_credit`, dipakai di `/api/jobs`) |
| `403` | Akun nonaktif |
| `409` | Email sudah terdaftar |
| `422` | Validasi input gagal |

Email dinormalisasi (trim + lowercase). Password di-hash Argon2id.

## API — Upload (BE-Azriel-03)

`POST /api/upload` — Bearer wajib, `multipart/form-data`, field `file`.

Response `201`:
```json
{"upload_id": "uuid", "filename": "My Video.mp4", "size_bytes": 1234, "content_type": "video/mp4", "created_at": "..."}
```

| Status | Kondisi |
|---|---|
| `400` | Lebih dari 1 file / multipart rusak |
| `401` | Token tidak ada / invalid |
| `402` | Credit habis (upload diblok, credit baru dipotong saat submit job) |
| `411` | Header `Content-Length` tidak ada (chunked upload ditolak) |
| `413` | File melebihi `MAX_UPLOAD_SIZE_MB` (default 500) |
| `415` | Format tidak didukung, atau isi file tidak cocok dengan ekstensi |
| `422` | Field `file` tidak ada / file kosong |

Format: `.mp4 .mov .m4v .mkv .webm .avi`. Validasi pakai ekstensi **dan** magic bytes (Content-Type dari client diabaikan).
File disimpan sebagai `{upload_id}.{ext}` di `UPLOAD_DIR` (`/data/uploads`, named volume `contentsy_storage` yang dishare `api` dan `worker`). Nama asli file hanya disimpan di DB (tabel `uploads`) sebagai metadata, tidak pernah dipakai sebagai path.

> Upload yang tidak pernah dipakai submit job akan jadi orphan — cleanup-nya masuk BE-Azriel-10.
> Production: set juga `client_max_body_size` di reverse proxy (nginx) sesuai `MAX_UPLOAD_SIZE_MB`.

## Test Manual (sesuai Task Flow to Test)

```bash
# BE-02: register → login → credits
curl -X POST localhost:8001/api/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"a@b.com","password":"supersecret1"}'
curl -X POST localhost:8001/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"a@b.com","password":"supersecret1"}'
curl localhost:8001/api/user/credits -H "Authorization: Bearer <TOKEN>"   # 200 {"credits":10}
curl -i localhost:8001/api/user/credits                                    # 401

# cek hash di DB (harus $argon2id$..., bukan plaintext)
docker compose exec db psql -U contentsy -d contentsy_db -c "select email, hashed_password from users;"

# BE-03: upload (pakai TOKEN dari login)
curl -X POST localhost:8001/api/upload -H "Authorization: Bearer <TOKEN>" -F "file=@sample.mp4"
docker compose exec api ls -lh /data/uploads    # file {upload_id}.mp4 ada

# BE-01: Celery worker terima dummy task
docker compose exec api python -c "from app.worker.tasks import ping; print(ping.delay().get(timeout=10))"  # pong


```bash
# fresh clone
docker compose up -d
docker compose ps          # semua "healthy" / "running"

# restart, cek data postgres tetap ada
docker compose restart db
docker compose exec db psql -U contentsy -d contentsy_db -c "\dt"
```
