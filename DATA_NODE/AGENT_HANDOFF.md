# DATA_NODE Agent Handoff

This file is intended for the deployment/code agent on the DATA_NODE host.

## Objective

Implement and deploy a local service that stores `.hbr` datasets in S3-compatible storage and exposes API operations defined in `OPENAPI.yaml`.

## Must Implement

1. API server with endpoints from `OPENAPI.yaml`.
2. S3 integration using bucket/key rules from `STORAGE_LAYOUT.md`.
3. Metadata persistence (SQLite or PostgreSQL).
4. Export pipeline for `/lerobot/export`:
   - Input: list of `datasetId`.
   - Output: merged LeRobot-formatted dataset and export manifest.
5. Health endpoints and structured logs.

## Ingestion Expectations

- Source datasets arrive as `<datasetId>.hbr` directories.
- Validate against `HBR_COMPAT.md`.
- Reject invalid datasets with actionable error messages.

## Security and Reliability

- Validate all request payloads.
- Enforce path safety (no traversal in file paths).
- Add retries for object storage uploads.
- Make session registration idempotent by `datasetId`.

## Deliverables

- Running services (docker compose or systemd).
- API smoke tests.
- Minimal operator runbook:
  - start/stop services
  - inspect failed ingestion
  - recover or re-run export jobs
