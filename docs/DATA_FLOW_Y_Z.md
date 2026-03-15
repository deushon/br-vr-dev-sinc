# Поток данных VR → MoveIt (Y/Z)

## 1. Цепочка топиков

```
[Quest VR]  →  /quest/poses  (PoseArray: head, left_hand, right_hand)
                    │
                    ▼
            vr_remapper_node.py
            Подписка: rospy.Subscriber('/quest/poses', ...)
            Читает:  p.x, p.y, p.z  из poses[1], poses[2]
            Пишет:   out.poses[1].position.x/y/z, out.poses[2].position.x/y/z
                    │
                    ▼
            /teleop_fetch/quest_poses_remapped
                    │
                    ▼
            pose_source_node.py
            Подписка: /teleop_fetch/quest_poses_remapped
            Просто пересылает (без изменений)
                    │
                    ▼
            /teleop_fetch/poses
                    │
                    ▼
            fast_ik_node.cpp  pointCallback()
            Подписка: poses_topic = "/teleop_fetch/poses"
            Читает:   left_point = mut_msg.poses[1], right_point = mut_msg.poses[2]
            Использует: left_point.position.x, .y, .z  → offset_pose, scale_pose → IK
                    │
                    ▼
            MoveIt setFromIK()  →  joint values  →  servo positions
```

## 2. Где что лежит

| Место | Файл:строка | Переменные |
|-------|-------------|------------|
| **Подписка на VR** | vr_remapper_node.py:67 | `rospy.Subscriber('/quest/poses', ...)` |
| **Чтение Quest** | vr_remapper_node.py:94,103 | `p = self.quest_poses.poses[1].position` → `p.x, p.y, p.z` |
| **Запись после ремапа** | vr_remapper_node.py:97-99, 106-108 | `out.poses[1].position.x = x` (и y, z) |
| **Передача в fast_ik** | pose_source_node.py:42 | `self.pub.publish(self.quest_poses_remapped)` |
| **Подписка fast_ik** | fast_ik_node.cpp:137 | `sub_quest_ = node.subscribe(poses_topic, ...)` |
| **Чтение в fast_ik** | fast_ik_node.cpp:271-275 | `left_point.position.x/y/z`, `right_point.position.x/y/z` |
| **offset_pose** | fast_ik_node.cpp:796-807 | Модифицирует `Pose.position.x, .y, .z` |
| **scale_pose** | fast_ik_node.cpp:763-781 | Масштабирует x,y,z, добавляет robot_z_offset |
| **В IK** | fast_ik_node.cpp:331-333 | `left_target`, `right_target` → `computeIK()` |

## 3. Ожидаемые оси

- **body_link (робот):** X вперёд, Y влево, Z вверх
- **offset_pose** ждёт: Y = горизонталь (влево/вправо), Z = вертикаль (вверх/вниз)
- **Quest** (типично): своя система, часто Y=up или Z=up — нужно проверить по факту

## 4. Текущие преобразования (космысли)

1. **vr_remapper** axis_mapping "xy": `(-y, -x, z)` → body_link.x=-Quest.y, .y=-Quest.x, .z=Quest.z
2. **vr_remapper** post_mapping swap: `y,z = z,y` → меняет местами .y и .z
3. **fast_ik** offset_pose: при swap_yz_ применяет neck/hand_center к другим осям
4. **fast_ik** scale_pose: при swap_yz_ добавляет robot_z_offset к y вместо z
5. **UI scalePose**: дублирует логику с учётом post_mapping

## 5. Реализованный фикс (2025-03)

Если Quest отдаёт Y и Z «наоборот» (например, Quest.y=vertical, Quest.z=horizontal), достаточно **один раз** поменять их местами в vr_remapper.

**Вариант A:** Встроить swap в axis_mapping "xy", убрать post_mapping:

```python
# vr_remapper_node.py, _apply_axis_mapping для "xy":
# Было: return (-y, -x, z)
# Стало: return (-y, z, -x)   # swap: body_link.y=Quest.z, body_link.z=-Quest.x
```

Тогда offset_pose в fast_ik должен применять neck к y, hand_center к z (как при swap_yz_=true). То есть **по умолчанию** считать, что приходит уже «swap’нутый» формат.

**Вариант B:** Оставить только swap в vr_remapper, убрать из fast_ik логику swap_yz_:

В vr_remapper после axis_mapping всегда делать `y, z = z, y` (если Quest Y/Z перепутаны). Тогда на выходе body_link.y = горизонталь, body_link.z = вертикаль, и offset_pose в fast_ik работает как раньше (без swap_yz_).

Проблема: при swap в vr_remapper body_link.y = Quest.z, body_link.z = -Quest.x. Если Quest.z=vertical, Quest.x=horizontal, то body_link.y=vertical, body_link.z=horizontal — снова не то. Нужно body_link.y=horizontal, body_link.z=vertical. Значит swap даёт body_link.y=Quest.z, body_link.z=-Quest.x. Если Quest.z=horizontal и Quest.x=vertical, то body_link.y=horizontal, body_link.z=vertical. OK.

Итого: если Quest отдаёт X=vertical, Z=horizontal, то axis "xy" даёт body_link.y=-Quest.x (vertical), body_link.z=Quest.z (horizontal). Swap даёт body_link.y=Quest.z (horizontal), body_link.z=-Quest.x (vertical). Верно.

## 6. Асимметрия при swap

offset_pose применяет `hand_center`: left +0.05, right -0.05. Это смещение по **горизонтали** (Y в body_link). При swap_yz_=true мы применяем hand_center к **z**. Но тогда left и right получают +0.05 и -0.05 к z. Если z — горизонталь, то это симметрично. Асимметрия может быть из‑за:
- `swap_right_only` — swap только для правой руки, левая остаётся в другой системе
- Разный `left_hand_offset_sign_` для левой руки
