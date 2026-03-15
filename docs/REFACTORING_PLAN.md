# План рефакторинга системы телеоперации VR

**Статус:** Рефакторинг выполнен (2025-03). Единый пакет `teleop_fetch`, `ainex_teleop` удалён.

---

## 1. Текущая реализация (актуальная архитектура)

### Поток данных

**Вход (VR Quest):**
| Топик | Тип | Содержимое |
|-------|-----|------------|
| `/quest/poses` | PoseArray | poses[0]=head, [1]=left_hand, [2]=right_hand (relative-to-head) |
| `/quest/joints` | JointState | L_grip, L_index, R_grip, R_index, L_X, L_Y, R_A, R_B (0..1) |

**Выход (робот):**
| Топик | Тип | Назначение |
|-------|-----|------------|
| `/ros_robot_controller/bus_servo/set_position` | SetBusServosPosition | Руки + grippers (единственная точка публикации) |
| `/head_pan_controller/command` | HeadState | Поворот головы |
| `/head_tilt_controller/command` | HeadState | Наклон головы |

**Примечание:** teleop_fetch публикует `ainex_interfaces/HeadState` (совместимо с ainex_controller).

### Архитектура (реализовано)

```
/quest/poses, /quest/joints
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│   fast_ik_node      │              │   teleop_fetch      │
│   (my_package)      │              │   (единый узел)      │
│                     │              │                     │
│ IK → arm_servo_     │   ────────►  │ Подписка на         │
│ targets             │   /teleop_   │ arm_servo_targets   │
│                     │   fetch/     │                     │
│ Публикует:          │   arm_servo_ │ X=enable, Y=disable │
│ /teleop_fetch/      │   targets    │ Голова: HeadState   │
│ arm_servo_targets   │              │ → bus_servo         │
│ /teleop_fetch/      │              │ (единственный       │
│ debug_target_poses  │              │  издатель)          │
└─────────────────────┘              └─────────────────────┘
```

### Маппинг сервоприводов (ID из URDF)
| ID | Сустав | Рука |
|----|--------|------|
| 13 | l_sho_pitch | Left |
| 15 | l_sho_roll | Left |
| 17 | l_el_pitch | Left |
| 19 | l_el_yaw | Left |
| 21 | l_gripper | Left |
| 14 | r_sho_pitch | Right |
| 16 | r_sho_roll | Right |
| 18 | r_el_pitch | Right |
| 20 | r_el_yaw | Right |
| 22 | r_gripper | Right |

### Gripper limits (безопасные)
| Gripper | Closed | Open |
|---------|--------|------|
| Left (21) | 500 | 100 |
| Right (22) | 400 | 800 |

### Стартовые позиции рук (teleop_fetch/config/teleop.yaml)
```
Left:  13=874, 15=833, 17=502, 19=44,  21=500
Right: 14=126, 16=167, 18=498, 20=956, 22=500
```

### Пакеты и роли
- **teleop_fetch** — единый узел: голова (HeadState), X/Y (enable/disable), пересылка arm_servo_targets → bus_servo при controlling, reset grippers/head при stop.
- **my_package** — fast_ik_node: IK обеих рук, gripper, публикует в `/teleop_fetch/arm_servo_targets` и `/teleop_fetch/debug_target_poses`.
- **robot** — MoveIt (full, full_2), kinematics, SRDF.
- **ainex_simulations** — URDF (ainex_description).

### Запуск
```bash
roslaunch teleop_fetch teleop.launch          # полный стек
roslaunch teleop_fetch teleop_debug.launch   # с RViz
roslaunch teleop_fetch teleop_fetch.launch   # только teleop_fetch (без robot, move_group, fast_ik)
```

### Конфигурация
- `teleop_fetch/config/teleop.yaml` — VR topics, servo_ids, arm_start_positions, head, arm_servo_targets_topic
- `my_package/config/fast_ik.yaml` — robot_scale, gripper, move_groups, axis_mapping, left_hand

### IK conversion (fast_ik_node)
MoveIt возвращает joint angles (rad). Перед отправкой:
1. **conversion()** — разные формулы для левой/правой руки
2. **radians_to_servo_position():** angle_deg = clamp(angle_rad×180/π, −120, 120), position = (angle_deg + 120) × (1000/240)

---

## 2. Выполненные этапы рефакторинга

- [x] Единый конфиг (teleop.yaml в teleop_fetch)
- [x] Объединённая логика в teleop_fetch (head, start/stop, arm targets forwarding)
- [x] HeadState (ainex_interfaces) вместо HeadCommand
- [x] Единый launch (teleop.launch)
- [x] Миграция ainex_teleop → teleop_fetch, удаление ainex_teleop
- [x] Топики `/teleop_fetch/arm_servo_targets`, `/teleop_fetch/debug_target_poses`

---

## 3. Известные проблемы (см. TODO.md)

- Правая рука — ограниченная зона управления
- Левая рука — некорректное поведение, настройка left_hand/conversion_preset
- HTML-визуализация — оси, настраиваемый маппинг
