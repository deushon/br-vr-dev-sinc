# TODO / Bug Report

## Известные проблемы (2025-03-15)

### Правая рука — ограниченная зона управления

**Описание:** Правая рука работает более-менее корректно, но только в **малом диапазоне** действий. За пределами этого диапазона поведение становится некорректным или неожиданным.

**Статус:** Требует доработки  
**Приоритет:** Высокий

**Возможные направления:**
- Проверить масштабирование (robot_scale, human_arm_length vs robot_arm_length)
- Расширить рабочую зону IK (move_group limits, joint limits)
- Калибровка offset'ов (neck_offset, big_head_x_offset, hand_center_outer_offset)
- Проверить axis_mapping для Quest/Unity → body_link

---

### Левая рука — некорректное поведение

**Описание:** Левая рука ведёт себя странно. Ранее применялись инверсии и правки от программиста, которые не были полноценно протестированы.

**Статус:** В процессе настройки  
**Приоритет:** Высокий

**Текущие опции в `fast_ik.yaml` (my_package):**
- `left_hand/offset_sign`: +1 или -1
- `left_hand/conversion_preset`: `current` | `mirror_right` | `simple`

---

### HTML-визуализация — оси

**Описание:** Подозрение, что оси перепутаны в HTML-рендере (Three.js), а не в управлении. Добавлен выпадающий список Display axes для подбора маппинга body_link → Three.js.

**Статус:** Частично решено (настраиваемый маппинг)  
**Приоритет:** Средний

---

## Запланировано

- [ ] Калибровка зоны управления (руки)
- [ ] Полноценное тестирование левой руки с разными conversion_preset
- [ ] Проверка и фиксация корректного axis_mapping для HTML
- [x] End-to-end dataset recording (`/record_sessions` -> `.hbr`)
- [x] Upload API (`POST /upload_dataset` on `:9191`)

---

## Dataset recording follow-ups

- [x] Push to DATA_NODE via `POST /sessions/upload` (multipart, per ROBOT_SERVICE_INTEGRATION.md)
- [ ] Optional video transcoding pipeline (`cam_main_frames.jsonl` -> `cam_main.mp4` real stream)
- [ ] Add automated integration tests for recorder/upload API
