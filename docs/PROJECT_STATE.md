# Состояние проекта — VR Teleop Ainex

**Версия:** beta 1.0  
**Дата:** 2025-03-15

## Обзор

Единая VR-телеманипуляция для робота Ainex: голова, руки, грипперы, X/Y start/stop. Один издатель в bus_servo.

---

## Пакеты и их состояние

### teleop_fetch (основной пакет телопа)

| Компонент | Описание | Статус |
|-----------|----------|--------|
| `teleop_node.py` | Главный узел: head, arms, start/stop | ✅ |
| `vr_remapper_node.py` | Маппинг осей, R_A калибровка, scale | ✅ beta 1.0 |
| `pose_source_node.py` | VR (remapped) + manual → /teleop_fetch/poses | ✅ |
| `head_controller.py` | Pan/tilt по ориентации головы | ✅ |
| `start_stop_controller.py` | X=включить руки, Y=выключить | ✅ |
| `config/teleop.yaml` | servo IDs, arm start, head | ✅ |
| `config/vr_remapper.yaml` | reference_pose, scale | ✅ |
| `web/teleop_debug.html` | 3D визуализация, scale, manual drag | ✅ |

**Запуск:** `roslaunch teleop_fetch teleop.launch`

---

### my_package (fast_ik_node)

| Компонент | Описание | Статус |
|-----------|----------|--------|
| `fast_ik_node.cpp` | IK обеих рук, gripper, joint→servo conversion | ✅ |
| `config/fast_ik.yaml` | gripper, move_groups, left_hand | ✅ |
| Публикует | `/teleop_fetch/arm_servo_targets` | ✅ |
| Публикует | `/teleop_fetch/debug_target_poses` | ✅ |

**Примечание:** Маппинг, калибровка, scale — в vr_remapper. fast_ik получает готовые координаты в body_link.

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

См. [ARCHITECTURE.md](ARCHITECTURE.md) — уровни абстракции, потоки, схема.

Кратко: `/quest/poses` → vr_remapper (map + R_A calib + scale) → pose_source → fast_ik (IK) → teleop_fetch → bus_servo.

---

## Конфигурация

| Файл | Ключевые параметры |
|------|--------------------|
| `config/teleop.yaml` | servo_ids, arm_start_positions, head, VR topics |
| `config/vr_remapper.yaml` | reference_pose (left/right), scale |
| `config/fast_ik.yaml` (my_package) | gripper, move_groups, left_hand |

---

## Калибровка (beta 1.0)

**R_A на правом джойстике:** Оператор приводит руки в естественное положение (перед собой, слегка внизу). vr_remapper вычисляет offset = reference_pose - mapped_vr. Эталонная поза робота — в `vr_remapper.yaml`.

**SCALE:** Чувствительность 0.0001..100, топик `/teleop_fetch/scale`, обновляется из UI на лету.

---

## Отладка

- **RViz:** `roslaunch teleop_fetch teleop_debug.launch`
- **Web viz:** rosbridge + `teleop_debug.html`
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
