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
| `/teleop_fetch/scale` | Float64 | Чувствительность 0.0001..100, из UI |
| `/teleop_fetch/arm_servo_targets` | SetBusServosPosition | From fast_ik_node |
| `/head_pan_controller/command` | HeadState | Pan |
| `/head_tilt_controller/command` | HeadState | Tilt |
| `/ros_robot_controller/bus_servo/set_position` | SetBusServosPosition | Single output to servos |

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

**Calibration (beta 1.0):** Приведите руки в естественное положение (перед собой, слегка внизу), нажмите R_A на правом джойстике. Эталонная поза робота задаётся в `config/vr_remapper.yaml`. SCALE (0.0001..100) — чувствительность, обновляется из UI на лету (`/teleop_fetch/scale`).

## Docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — уровни абстракции, маппинги, потоки данных
- [PROJECT_STATE.md](docs/PROJECT_STATE.md) — состояние пакетов
- [REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) — план рефакторинга (выполнен)
- [TODO.md](docs/TODO.md) — известные проблемы, баги
