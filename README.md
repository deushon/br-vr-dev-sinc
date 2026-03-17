# Teleop Fetch

VR teleoperation for Ainex robot — unified head, arms, grippers, start/stop. Single point of publication to bus_servo.

## Quick start

```bash
# Full stack: robot, move_group, fast_ik, teleop
roslaunch teleop_fetch teleop.launch

# With RViz for debugging
roslaunch teleop_fetch teleop_debug.launch

# Minimal: teleop node only (no robot, move_group, fast_ik)
roslaunch teleop_fetch teleop_fetch.launch
```

## Features

- **Head control** — VR head orientation → pan/tilt (ainex_interfaces/HeadState)
- **Arms** — fast_ik_node publishes to `/teleop_fetch/arm_servo_targets`, teleop_fetch forwards to bus_servo when enabled
- **Grippers** — reset on stop
- **X/Y buttons** — X = enable arm control, Y = disable (return to start pose)
- **Dataset recording** — `/record_sessions` start/stop drives robot-side `.hbr` recording
- **Upload API** — headset sends `POST /upload_dataset` to port `9191`, payload is attached to matching dataset session

## Dependencies

- rospy, geometry_msgs, sensor_msgs, std_msgs
- ainex_interfaces (HeadState)
- ros_robot_controller
- robot, my_package (for full stack)

## Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/quest/poses` | PoseArray | VR head + hands |
| `/quest/joints` | JointState | VR buttons (L_X, L_Y, R_A, etc.) |
| `/teleop_fetch/quest_poses_remapped` | PoseArray | VR hands after vr_remapper (map + calibration + scale) |
| `/teleop_fetch/poses` | PoseArray | VR or manual (pose_source merge) |
| `/teleop_fetch/scale` | Float64 | Sensitivity 0.0001..100, from UI |
| `/teleop_fetch/arm_servo_targets` | SetBusServosPosition | From fast_ik_node |
| `/head_pan_controller/command` | HeadState | Pan |
| `/head_tilt_controller/command` | HeadState | Tilt |
| `/ros_robot_controller/bus_servo/set_position` | SetBusServosPosition | Single output to servos |
| `/record_sessions` | String(JSON) | Dataset lifecycle event (`start|stop`, `record_id`, timing metadata) |

## Dataset recording quick start

Dataset services are enabled in `teleop.launch` by default. You can disable them with:

```bash
roslaunch teleop_fetch teleop.launch enable_dataset_recording:=false
```

Default recorder config:

- `config/dataset_recorder.yaml`
- camera topic: `/camera/image_raw`
- imu topic: `/imu`
- joints topic: `/joint_states`
- upload API: `http://<robot-ip>:9191/upload_dataset`

## Config

`config/teleop.yaml` — VR topics, servo IDs, arm start positions, head params, arm_servo_targets_topic.

## Web debug

`web/teleop_debug.html` — 3D visualization: robot model, operator hands, robot targets. Manual mode: drag green spheres to control arms (publishes to `/teleop_fetch/manual_poses`). Requires rosbridge.

```bash
# Terminal 1: rosbridge (WebSocket on port 9090)
roslaunch rosbridge_server rosbridge_websocket.launch

# Terminal 2: serve HTML (or open web/teleop_debug.html in browser)
cd $(rospack find teleop_fetch)/web && python3 -m http.server 8080
# Open http://localhost:8080/teleop_debug.html
```

**Calibration (beta 1.0):** Bring hands to natural position (in front, slightly lower), press R_A on right joystick. Reference pose is in `config/vr_remapper.yaml`. SCALE (0.0001..100) — sensitivity, live update from UI (`/teleop_fetch/scale`).

## Docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — abstraction levels, mappings, data flows
- [PROJECT_STATE.md](docs/PROJECT_STATE.md) — package status
- [REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) — refactoring plan (done)
- [TODO.md](docs/TODO.md) — known issues, bugs
- [TELEOP_DATAS.md](docs/TELEOP_DATAS.md) — headset event and upload payload contract
- [HBR.md](docs/HBR.md) — `.hbr` container format and DATA_NODE requirements
