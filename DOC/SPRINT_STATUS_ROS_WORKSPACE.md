# Sprint: semaphores and tests — **br-vr-dev-sinc (teleop_fetch, IK, datasets)** ownership

Status as of **2026-03-31**. This repo has the **VR pipeline**, **`teleop_fetch`**, **HBR** recording, **DATA_NODE** upload (multipart), operator session fields. **Quest / Unity client** for briefing card and RTT preflight may live elsewhere; verify in the actual client repo.

## Summary

| Category | Comment |
|----------|---------|
| Implemented | Teleop via KYR proxy, `teleopControl` / `acceptedAtUtcIso` in upload and `metadata.json`, `operatorSessionMeta`, `sync_rtt_sec` in HBR frames, Peaq merge via service + `dataset_upload_server` |
| Partial | “Safe handoff”: `get_control` / `lost_control` in contract and **L_X** gating (`arm_stream_requires_lx`); **no** explicit `TELEOP_READY`, **no** `teleop_ready_at` / `operator_confirmed_at`, **no** “I have control” button in this Python stack |
| Not implemented | RTT **blocking** session start at ≥200 ms (code only records **sync RTT** in dataset, not a gate), pre-connect briefing UI, Cosmos visual_annotation, recovery slice extractor |

---

## Semaphores → br-vr-dev-sinc

| # | Deliverable | Repo role | Status |
|---|-------------|-----------|--------|
| 3 | Event↔recording | Dataset, `metadata.json`, upload | **🟡**: `dataset_id` on record side; **`critical_event_ids`** in payload — if set by Backend/other node, not found here |
| 4 | `TELEOP_TAKEOVER` auto | Node/integration emitting event | **Not implemented** (no matches in Python/C++) |
| 6 | RTT preflight gate | VR + blocking policy | **Not implemented**; see `sync_rtt_sec` / `syncRttSec` in [HBR.md](HBR.md), [episode_recorder.py](../src/teleop_fetch/episode_recorder.py) — telemetry, not gate |
| 7 | `raid_task_id` + `payment_id` | Session metadata | **🟡**: `taskName`, grant/task from RAID chain; **sprint key names** in `metadata.json` — verify vs DATA_NODE / Backend |
| 9 | `TELEOP_READY` | Kinematics / logging | **Not implemented** |
| 10 | Bilateral “I have control” | VR UI + ROS | **Not implemented** in `teleop_node` scripts (only teleop states and L_X/L_Y) |
| 11 | Pre-connect briefing | VR + frontend | **Not implemented** in this repo |
| 13–20 | Cosmos, recovery, quality, HF, external DB | Backend / ML | **N/A** |

---

## Sprint tests → br-vr-dev-sinc

| # | Test | Status |
|---|------|--------|
| 4 | Auto `TELEOP_TAKEOVER` in API | **🔴 FAIL** in repo (no generator) |
| 6 | RTT ≥200 ms blocks start | **🔴 FAIL** (no gate; metric in recording only) |
| 9 | Safe handoff `TELEOP_READY` → confirm | **🟡 PARTIAL**: simplified handoff via buttons and `teleopControl`; not full sprint spec |
| 10 | `teleop_ready_at` / `operator_confirmed_at` | **🔴 FAIL** (fields not in `DATA_NODE_OPERATOR_SESSION_SPEC` / upload) |
| 11 | Briefing card | **N/A** (Quest client) |
| 7 | `raid_task_id` / `payment_id` in session | Manual check `.hbr`/`metadata.json` after RAID teleop |
| 14 | Recovery slice | **N/A** (Backend) |

---

## teleop_fetch automated tests

Run **2026-03-31**:

```bash
cd /home/ubuntu/ros_ws && source devel/setup.bash
catkin build teleop_fetch --no-status --catkin-make-args run_tests
# or:
PYTHONPATH=/home/ubuntu/ros_ws/src/br-vr-dev-sinc/src:$PYTHONPATH python3 -m nose /home/ubuntu/ros_ws/src/br-vr-dev-sinc/tests -v
```

Result: **8 tests OK** (`test_upload_payload_session_fields`, `test_teleop_state_contract`, `test_operator_buttons`, …). They cover **upload contract** (`teleopControl`, `acceptedAtUtcIso`), **not** full cloud sprint scenarios.

---

## Gaps vs sprint (backlog)

1. Explicit **TELEOP_READY** state machine and API-logged event.
2. **Bilateral confirm** and timestamps in `metadata.json` / multipart.
3. **RTT preflight** on client/gateway with reason in `events.jsonl` and session block.
4. **TELEOP_TAKEOVER** / CRITICAL linkage to recording and cloud — separate nodes or Backend.
