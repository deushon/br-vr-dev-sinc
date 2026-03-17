# Deployment

## Option A: Docker Compose (recommended)

Services:

- `data-node-api`
- `data-node-worker`
- `minio`
- `postgres` (or sqlite in single-node mode)

### Steps

1. Copy `ENV.example` to `.env`.
2. Fill S3 and DB credentials.
3. Start stack:

```bash
docker compose up -d
```

4. Verify:

```bash
curl http://localhost:8088/health
```

## Option B: systemd services

- `data-node-api.service`
- `data-node-worker.service`
- `minio.service`

Use the same env file and ensure restart policy `on-failure`.

## Health Checks

- API: `/health`
- Storage probe: `/health/storage`
- DB probe: `/health/db`

## Backup

- Snapshot metadata DB daily.
- Enable MinIO object versioning if available.
- Keep export manifests in DB for reproducibility.
