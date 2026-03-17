# HBR Compatibility Notes

## Required Input

Every dataset directory must be named `<datasetId>.hbr` and contain:

- `metadata.json`
- `robot/robot_state.bin`
- `operator/operator_state.bin` (may appear after `/upload_dataset` processing)
- `operator/events.jsonl`
- `video/cam_main.mp4` (placeholder allowed for now)
- `video/cam_main_frames.jsonl`
- `lerobot_manifest/info.json`
- `lerobot_manifest/episodes.jsonl`
- `lerobot_manifest/mapping.json`

## Validation Rules

- `metadata.datasetId` must match directory name.
- `metadata.startedLocalUnixTimeNs <= metadata.endedLocalUnixTimeNs`.
- `lerobot_manifest/info.json` must reference valid paths.
- Binary files must be non-empty unless explicitly allowed by version policy.

## Mapping to LeRobot

- `observation.images.cam_main` -> `video/cam_main_frames.jsonl` (or transcoded MP4).
- `observation.state` -> decode `robot/robot_state.bin`.
- `observation.operator` -> decode `operator/operator_state.bin`.
- `episode_index` fixed to `0` per `.hbr`.

## Versioning

- Current expected `hbrVersion`: `1.0.0`.
- Future incompatible changes must bump major version and include migration notes.
