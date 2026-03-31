# DEV_AI — agent context (br-vr-dev-sinc / VR Teleop)

## Ecosystem entry point (KYR + x402 + teleop_fetch)

Full stack launch and doc links: **[../br_bringup/DEV_AI.md](../br_bringup/DEV_AI.md)**, **[../br_bringup/README.md](../br_bringup/README.md)**.

## Purpose

Quest VR teleoperation for a dual-arm robot (ROS 1 Noetic). Main package: **`teleop_fetch`** — single publisher for arm commands to **`/kyr/bus_servo_in`** → KYR proxy → `/bus_servo/set_position`. Data flow:

`Quest` → `vr_remapper` (incl. **R_A**) → `pose_source` → `fast_ik` → `teleop_fetch` → KYR. **Head** moves on ACTIVE immediately; **arms** to KYR after **L_X**. **`/teleop_state`**: on node start and new session — `stop_control`; **L_X** → `get_control`; **L_Y** (if armed) → `stop_control`. IK status: `/teleop_fetch/teleop_state`.

Default full stack: `roslaunch br_bringup ecosystem.launch` (includes `teleop.launch`). KYR gateway only without IK: `with_vr_pipeline:=false`. Legacy `teleop_calibration` (T-pose) off by default; enable: `enable_legacy_teleop_calibration:=true` (from `ecosystem.launch` into `teleop.launch`). Arms on KYR with `arm_stream_requires_lx:=true` only after **L_X** rising edge on joints — else see `DOC/ARCHITECTURE.md` and `~arm_stream_requires_lx`. Datasets: default **`dataset_recorder` + `dataset_upload_server` (:9191) + `dataset_web_server` (:3002, `web/dataset_dashboard.html`)**; disable: `enable_dataset_recording:=false`. Peaq claim in `metadata.json` / multipart: **`/teleop_fetch/set_peaq_dataset_claim`**, see [DOC/DATA_NODE_PEAQ_CLAIM_SPEC.md](DOC/DATA_NODE_PEAQ_CLAIM_SPEC.md).

`ERR_CONNECTION_REFUSED` on **:3002**: node `/dataset_web_server` not listening (often second `roslaunch` on same rosmaster — log `new node registered with same name`); with **`with_vr_pipeline:=false`** dataset web does not start. Details: [DOC/ARCHITECTURE.md](DOC/ARCHITECTURE.md) §6.

## Key paths

- `.gitignore` — Python cache (`__pycache__/`, `*.pyc`), venv, `.env`, pytest/mypy caches, IDE, `*.log`; do not commit bytecode. Publishing: [../br_bringup/DOC/PUBLIC_RELEASE_CHECKLIST.md](../br_bringup/DOC/PUBLIC_RELEASE_CHECKLIST.md).
- `teleop_fetch/` — `vr_remapper_node.py`, `pose_source_node.py`, `teleop_node.py`, `config/vr_remapper.yaml`, `.hbr` datasets.
- `my_package/` — `fast_ik_node.cpp`, `config/fast_ik.yaml`.

## Documentation

Index: [DOC/README.md](DOC/README.md). Read [DOC/ARCHITECTURE.md](DOC/ARCHITECTURE.md) and [DOC/PROJECT_STATE.md](DOC/PROJECT_STATE.md). Bugs and backlog: [DOC/TODO.md](DOC/TODO.md). Sprint vs VR/datasets: [DOC/SPRINT_STATUS_ROS_WORKSPACE.md](DOC/SPRINT_STATUS_ROS_WORKSPACE.md).

## Responsibilities when editing

1. **Documentation** — update all touched `DOC/` files; new subsystems → new `.md` in `DOC/` + line in [DOC/README.md](DOC/README.md) + README/DEV_AI if needed.
2. **Tests** — new logic needs tests; run full package/workspace tests:
   ```bash
   cd /home/ubuntu/ros_ws && source devel/setup.bash
   catkin_make run_tests --pkg teleop_fetch
   # if my_package has tests:
   # catkin_make run_tests --pkg my_package
   ```
3. **Commit** — clear message (area + essence).

## Workspace rule

`ros_ws` may have `.cursor/rules/project-context.mdc` with a short VR Teleop reminder; if it conflicts with `DOC/`, **`DOC/`** wins.
