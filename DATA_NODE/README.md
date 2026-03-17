# DATA_NODE

DATA_NODE is a dedicated local-network service for storing, indexing, and exporting `.hbr` datasets produced by `teleop_fetch`.

## Responsibilities

- Register incoming `.hbr` sessions.
- Store dataset files in S3-compatible storage.
- Provide REST APIs for metadata and download.
- Export merged datasets to LeRobot-compatible outputs.

## Core Components

- REST API service (session registry, query, export).
- Object storage (S3-compatible, e.g. MinIO).
- Metadata database (SQLite/PostgreSQL).
- Background worker for LeRobot export tasks.

## Ports

- `8088` - DATA_NODE REST API
- `9000` - S3 API (MinIO)
- `9001` - MinIO console

## Required Docs

- `ARCHITECTURE.md`
- `OPENAPI.yaml`
- `STORAGE_LAYOUT.md`
- `HBR_COMPAT.md`
- `DEPLOYMENT.md`
- `ENV.example`
- `AGENT_HANDOFF.md`
