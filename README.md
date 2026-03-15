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
| `/quest/joints` | JointState | VR buttons (L_X, L_Y, etc.) |
| `/teleop_fetch/arm_servo_targets` | SetBusServosPosition | From fast_ik_node |
| `/head_pan_controller/command` | HeadState | Pan |
| `/head_tilt_controller/command` | HeadState | Tilt |
| `/ros_robot_controller/bus_servo/set_position` | SetBusServosPosition | Single output to servos |

## Config

`config/teleop.yaml` — VR topics, servo IDs, arm start positions, head params, arm_servo_targets_topic.

## Web debug

`web/teleop_debug.html` — Rosbridge + Three.js visualization of operator vs robot target poses. Subscribes to `/quest/poses` and `/teleop_fetch/debug_target_poses`.

## Docs

- [PROJECT_STATE.md](docs/PROJECT_STATE.md) — состояние пакетов, архитектура
- [REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) — план рефакторинга (выполнен)
- [TODO.md](docs/TODO.md) — известные проблемы, баги
