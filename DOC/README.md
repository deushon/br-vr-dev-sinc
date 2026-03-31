# VR Teleop (br-vr-dev-sinc) — documentation index

All detailed docs live in **`DOC/`**. Root [README.md](../README.md) and [DEV_AI.md](../DEV_AI.md) are entry points with links here.

## Stack architecture

- [ARCHITECTURE.md](ARCHITECTURE.md) — abstraction layers, topics, flow Quest → remapper → IK → `teleop_fetch`.
- Post-close operator SOL payment: `/x402/complete_teleop_payment` from `teleop_node` (depends on `rospy_x402`); RAID response spec: [../../rospy_x402/DOC/RAID_APP_TELEOP_HELP_FULL_CYCLE_X402_SPEC.md](../../rospy_x402/DOC/RAID_APP_TELEOP_HELP_FULL_CYCLE_X402_SPEC.md).

## Project state and tasks

- [PROJECT_STATE.md](PROJECT_STATE.md) — package and component status.
- [TODO.md](TODO.md) — known issues and backlog.
- [SPRINT_STATUS_ROS_WORKSPACE.md](SPRINT_STATUS_ROS_WORKSPACE.md) — sprint semaphores/tests vs teleop_fetch / datasets / VR pipeline.
- Public release: [../../br_bringup/DOC/PUBLIC_RELEASE_CHECKLIST.md](../../br_bringup/DOC/PUBLIC_RELEASE_CHECKLIST.md).

## Datasets and HBR format

- On the robot: with `enable_dataset_recording` in `teleop.launch`, REST **:9191** and **`dataset_web_server`** start → `http://<robot>:3002/dataset_dashboard.html` (see [ARCHITECTURE.md](ARCHITECTURE.md) §6).
- [TELEOP_DATAS.md](TELEOP_DATAS.md) — headset events, upload API contract.
- [HBR.md](HBR.md) — `.hbr` container format, storage.
- [RAID_APP_DATASET_PROXY_SPEC.md](RAID_APP_DATASET_PROXY_SPEC.md) — **RAID App** (`x402_raid_app`): HTTP reverse proxy to dataset API on robot (`:9191`) for operators via JWT.
- [RAID_APP_PEAQ_CLAIM_SPEC.md](RAID_APP_PEAQ_CLAIM_SPEC.md) — **RAID App**: peaq claim on Agung, `teleop/help` extension and `GET …/peaq/claim`.
- [DATA_NODE_OPERATOR_SESSION_SPEC.md](DATA_NODE_OPERATOR_SESSION_SPEC.md) — **DATA_NODE**: extended teleop session fields, `metadata.json`, multipart `operatorSessionMeta` on `POST /sessions/upload`.
- [DATA_NODE_PEAQ_CLAIM_SPEC.md](DATA_NODE_PEAQ_CLAIM_SPEC.md) — **DATA_NODE**: optional multipart part `peaqClaim` when uploading dataset from robot.

---

New functional areas → new `DOC/` file + index line here; update README and DEV_AI when contracts change.
