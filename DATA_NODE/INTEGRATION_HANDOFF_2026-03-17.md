# DATA_NODE Integration Handoff (from teleop_fetch)

## Context

Robot-side dataset recording is working end-to-end (robot + operator data are collected into `.hbr` locally).

Push from robot to DATA_NODE is currently failing due API contract mismatch:

- `POST /sessions/upload` is not available (405, GET only).
- `POST /sessions` accepts JSON but requires `sourcePath` to an existing directory on DATA_NODE host.
- Robot and DATA_NODE are on different hosts; DATA_NODE cannot access robot-local paths directly.

## Observed Errors

- `Connection reset by peer` when trying old upload endpoint.
- `HTTP 400` with message:
  - `sourcePath must point to an existing directory.`

## What teleop_fetch currently does

- After dataset finalize and upload payload apply, teleop_fetch attempts auto push.
- It supports:
  1. Multipart upload mode (if upload endpoint exists).
  2. Fallback JSON mode (`POST /sessions`) with `sourcePath`.
- Dataset status tracks:
  - `uploadStatus` (`pending`, `uploaded`, `failed`)
  - `uploadLastError`
  - timestamps and target URL.

## Required DATA_NODE changes (recommended)

Implement one of these contracts:

### Option A (recommended): direct file ingest endpoint

- `POST /sessions/upload`
- Accept `multipart/form-data`:
  - `datasetId` (text)
  - `file` (`<datasetId>.hbr.tar.gz`)
- DATA_NODE unpacks into managed storage and registers metadata in DB.

This is best for decoupled hosts (no shared FS required).

### Option B: pull endpoint from robot URL

- Keep `POST /sessions` JSON contract, but allow:
  - `sourcePath` as HTTP/HTTPS URL to a tar/dir export endpoint
- DATA_NODE downloads remotely and ingests.

## Optional enhancements on DATA_NODE

- Add idempotency by `datasetId` (`upsert` semantics).
- Expose ingest state endpoint for UI polling:
  - `pending`, `processing`, `uploaded`, `failed`.
- Return structured error body with machine-readable code.

## Sample multipart request (Option A)

```
POST /sessions/upload
Content-Type: multipart/form-data; boundary=...

datasetId=<id>
file=<id>.hbr.tar.gz
```

Success:

```json
{
  "status": "ok",
  "datasetId": "<id>",
  "ingestState": "uploaded"
}
```

## Notes

Robot side UI now includes:

- Fullscreen dataset dashboard
- Manual re-push for failed datasets
- Delete/download actions
- Local clear-all for cache reset

Once DATA_NODE upload contract is available, auto-push should converge to `uploadStatus=uploaded`.
