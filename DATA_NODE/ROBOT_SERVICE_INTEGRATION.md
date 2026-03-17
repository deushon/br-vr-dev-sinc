# Robot Service Integration with DATA_NODE

This document defines the robot-side contract for pushing datasets to DATA_NODE.

## Endpoint

- Method: `POST`
- Path: `/sessions/upload`
- Content type: `multipart/form-data`

## Multipart fields

- `datasetId` (required, text)
- `file` (required, binary) - archive file `<datasetId>.hbr.tar.gz`
- `taskName` (optional, text) - falls back to `metadata.json.taskName` or `unknown_task`
- `label` (optional, text) - falls back to `metadata.json.label` or `unlabeled`

## Request example

```bash
curl -X POST http://<data-node-host>:8088/sessions/upload \
  -F "datasetId=example_001" \
  -F "taskName=pick_place" \
  -F "label=good" \
  -F "file=@/tmp/example_001.hbr.tar.gz"
```

## Success response

```json
{
  "status": "ok",
  "datasetId": "example_001",
  "ingestState": "ingested"
}
```

## Error behavior

- `400` - invalid payload/archive:
  - wrong file extension
  - malformed archive
  - archive traversal attempt (`../` paths)
  - missing `<datasetId>.hbr` directory in archive
- `500` - server-side ingest/storage failure

## Backward compatibility

The legacy endpoint is still available:

- `POST /sessions` with JSON body including `sourcePath`
- Use this only when DATA_NODE can access that path on the same filesystem/network mount.

## Robot-side checklist

- Archive root contains `<datasetId>.hbr/`
- `metadata.json.datasetId` equals multipart `datasetId`
- Required files from `HBR_COMPAT.md` are present
- `video/cam_main_frames.jsonl` included (source of truth for video conversion)
- Retry failed uploads with same `datasetId` (idempotent upsert behavior)

## Recommended retry strategy

- Retry on `5xx`, connection reset, timeouts
- Do not retry on `400` without fixing payload/data
- Backoff: 1s, 2s, 4s, 8s (max 5 attempts)

## Troubleshooting (DATA_NODE side)

If robot logs show `Connection reset by peer` or `Broken pipe` on `/sessions/upload`:

- **Request body limit** — ensure DATA_NODE allows large multipart bodies (archives can be 10–100+ MB)
- **Read timeout** — server must read full body before responding; increase read timeout if needed
- **Content-Type** — must accept `multipart/form-data` with boundary
- **Field order** — robot sends: `datasetId`, `taskName`, `label`, `file` (binary)
