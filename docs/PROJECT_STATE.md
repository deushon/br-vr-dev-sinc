# Состояние проекта — VR Teleop Ainex

**Дата:** 2025-03-15

## Обзор

Единая VR-телеманипуляция для робота Ainex: голова, руки, грипперы, X/Y start/stop. Один издатель в bus_servo.

---

## Пакеты и их состояние

### teleop_fetch (основной пакет телопа)

| Компонент | Описание | Статус |
|-----------|----------|--------|
| `teleop_node.py` | Главный узел: head, arms, start/stop | ✅ Работает |
| `vr_adapter.py` | Подписка на /quest/poses, /quest/joints | ✅ |
| `head_controller.py` | Pan/tilt по ориентации головы | ✅ |
| teleop_node._arm_targets_callback | Пересылка arm_servo_targets → bus_servo при controlling | ✅ |
| `start_stop_controller.py` | X=включить руки, Y=выключить (стартовая поза) | ✅ |
| `config/teleop.yaml` | Конфиг: VR topics, scale, servo IDs, head | ✅ |
| `web/teleop_debug.html` | HTML-визуализация (Three.js, rosbridge) | ✅ + маппинг осей |

**Запуск:** `roslaunch teleop_fetch teleop.launch`

---

### my_package (fast_ik_node)

| Компонент | Описание | Статус |
|-----------|----------|--------|
| `fast_ik_node.cpp` | IK обеих рук, грипперы, conversion joint→servo | ✅ |
| `config/fast_ik.yaml` | axis_mapping, robot_scale, left_hand, gripper | ✅ |
| Публикует | `/teleop_fetch/arm_servo_targets` | ✅ |
| Публикует | `/teleop_fetch/teleop_state` (TeleopState) | ✅ |
| Debug | `/teleop_fetch/debug_target_poses` (PoseArray) | ✅ |

**Особенности:**
- Правая рука: работает в малом диапазоне (см. TODO.md)
- Левая рука: настройка через `left_hand/offset_sign`, `left_hand/conversion_preset`
- axis_mapping: `xy` (default), `xz`, `yz`, `none`

---

### robot

| Компонент | Описание | Статус |
|-----------|----------|--------|
| planning_context, move_group, SRDF | MoveIt, kinematics | ✅ |
| robot_description | URDF, ainex_description | ✅ |

---

### ainex_interfaces

| Компонент | Описание | Статус |
|-----------|----------|--------|
| HeadState | Сообщение для головы | ✅ |
| HeadCommand | Совместим с HeadState | ✅ |

---

### ros_robot_controller

| Компонент | Описание | Статус |
|-----------|----------|--------|
| SetBusServosPosition | Команды сервоприводам | ✅ |
| bus_servo/set_position | Топик | ✅ |

---

## Архитектура данных

```
/quest/poses (PoseArray: head, left, right)
/quest/joints (JointState: L_index, L_grip, R_index, R_grip)
        │
        ▼
fast_ik_node
  - rotate_pose_in_axis (axis_mapping)
  - offset_pose (hand_center_outer_offset, ± по руке)
  - scale_pose (robot_to_human_scale)
  - IK (MoveIt) → joint values
  - conversion (joint → servo, left/right)
        │
        ▼
/teleop_fetch/arm_servo_targets (SetBusServosPosition)
        │
        ▼
teleop_fetch (single publisher) → /ros_robot_controller/bus_servo/set_position
        │
        ├── head_pan_controller/command
        └── head_tilt_controller/command
```

---

## Конфигурация

| Файл | Ключевые параметры |
|------|--------------------|
| `config/teleop.yaml` | vr_input, robot_scale, servo_ids, arm_start_positions, head |
| `config/fast_ik.yaml` (my_package) | axis_mapping, robot_scale, left_hand, gripper, move_groups |

---

## Отладка

- **RViz:** `roslaunch teleop_fetch teleop_debug.launch`
- **Web viz:** rosbridge + `teleop_debug.html` (Display axes: body_link→Three.js)
- **Топики:** `/teleop_fetch/debug_target_poses`, `/teleop_fetch/teleop_state`, `/visualization_marker`

---

## Топик /teleop_fetch/teleop_state

**Тип:** `ainex_interfaces/TeleopState`

Публикуется fast_ik_node при каждом обновлении poses. Содержит состояние IK и ошибки.

| Поле | Тип | Описание |
|------|-----|----------|
| header | std_msgs/Header | stamp, frame_id |
| left_arm_ok | bool | IK успешен для левой руки |
| right_arm_ok | bool | IK успешен для правой руки |
| left_arm_out_of_bounds | bool | Цель вне досягаемости; рука следует в ближайшей точке (clamp_to_workspace) |
| right_arm_out_of_bounds | bool | Аналогично для правой руки |
| errors | string[] | Текстовые сообщения: "Left arm IK failed", "Right arm IK failed" при неудаче |

---

## Известные проблемы

См. [TODO.md](TODO.md).
