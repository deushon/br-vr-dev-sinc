# Storage Layout

## Bucket

- Bucket name: `hbr-datasets`

## Key Pattern

```text
hbr-datasets/<datasetId>.hbr/metadata.json
hbr-datasets/<datasetId>.hbr/robot/robot_state.bin
hbr-datasets/<datasetId>.hbr/operator/operator_state.bin
hbr-datasets/<datasetId>.hbr/operator/events.jsonl
hbr-datasets/<datasetId>.hbr/video/cam_main.mp4
hbr-datasets/<datasetId>.hbr/video/cam_main_frames.jsonl
hbr-datasets/<datasetId>.hbr/lerobot_manifest/info.json
...
```

## Export Outputs

```text
hbr-datasets/exports/<exportId>/dataset_info.json
hbr-datasets/exports/<exportId>/episodes.jsonl
hbr-datasets/exports/<exportId>/frames.parquet
hbr-datasets/exports/<exportId>/videos/<episode>.mp4
```

## Metadata Index Requirements

Persist these fields for fast filtering:

- `datasetId`
- `taskName`
- `label`
- `robotType`
- `createdUtcIso`
- `durationSec`
- `numRobotFrames`
- `numOperatorFrames`
- `storageState` (`ingested|missing|error`)

## Retention

- `.hbr` source data: no automatic deletion by default.
- Export outputs: configurable TTL (`EXPORT_RETENTION_DAYS`).
