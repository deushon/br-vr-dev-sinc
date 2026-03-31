# Спринт: семафоры и тесты — зона ответственности **br-vr-dev-sinc (teleop_fetch, IK, датасеты)**

Состояние на **2026-03-31**. Репозиторий содержит **VR pipeline**, **`teleop_fetch`**, запись **HBR**, **upload** на DATA_NODE (multipart), поля сессии оператора. **Quest / Unity-клиент** для briefing-карточки и RTT preflight в этом git не обязаны быть; проверять по фактическому репо клиента.

## Краткий вывод

| Категория | Комментарий |
|-----------|-------------|
| Реализовано | Телеоп через KYR proxy, `teleopControl` / `acceptedAtUtcIso` в upload и `metadata.json`, `operatorSessionMeta`, `sync_rtt_sec` в кадрах HBR, Peaq merge через сервис + `dataset_upload_server` |
| Частично | «Безопасный handoff»: есть `get_control` / `lost_control` в контракте и gating по **L_X** (`arm_stream_requires_lx`); **нет** явного `TELEOP_READY`, **нет** `teleop_ready_at` / `operator_confirmed_at`, **нет** кнопки «I have control» в этом Python-стеке |
| Не реализовано | RTT **блокировка** старта сессии при ≥200 мс (в коде есть только запись **sync RTT** в датасет, не gate), pre-connect briefing UI, Cosmos visual_annotation, recovery slice extractor |

---

## Семафоры → br-vr-dev-sinc

| # | Deliverable | Роль репозитория | Статус |
|---|-------------|------------------|--------|
| 3 | Event↔recording | Датасет, `metadata.json`, upload | **🟡**: `dataset_id` на стороне записи/архива; **`critical_event_ids`** в payload — если заданы Backend/другим узлом, в этом репо не найдены |
| 4 | `TELEOP_TAKEOVER` авто | Ожидается узел/интеграция, пишущая событие | **Не реализовано** (нет вхождений в Python/C++) |
| 6 | RTT preflight gate | VR + политика блокировки | **Не реализовано**; см. `sync_rtt_sec` / `syncRttSec` в [HBR.md](HBR.md), [episode_recorder.py](../src/teleop_fetch/episode_recorder.py) — телеметрия, не gate |
| 7 | `raid_task_id` + `payment_id` | Метаданные сессии | **🟡**: `taskName`, grant/task из RAID цепочки; **явные ключи спринта** в `metadata.json` нужно сверять с контрактом DATA_NODE / Backend |
| 9 | `TELEOP_READY` | Кинематика / логирование | **Не реализовано** |
| 10 | Bilateral «I have control» | VR UI + ROS | **Не реализовано** в scripts `teleop_node` (есть только состояния телеопа и L_X/L_Y) |
| 11 | Pre-connect briefing | VR + Frontend | **Не реализовано** в этом репозитории |
| 13–20 | Cosmos, recovery, quality, HF, external DB | Backend / ML pipeline | **Н/Д** |

---

## Тесты спринта → br-vr-dev-sinc

| # | Тест | Статус |
|---|------|--------|
| 4 | Авто `TELEOP_TAKEOVER` в API | **🔴 FAIL** по коду репозитория (нет генерации) |
| 6 | RTT ≥200 мс блокирует старт | **🔴 FAIL** (нет gate; есть метрика в записи) |
| 9 | Safe handoff `TELEOP_READY` → confirm | **🟡 PARTIAL**: упрощённый handoff через кнопки и `teleopControl`; не совпадает со спеком спринта |
| 10 | `teleop_ready_at` / `operator_confirmed_at` | **🔴 FAIL** (поля не найдены в спецификации `DATA_NODE_OPERATOR_SESSION_SPEC` / upload) |
| 11 | Briefing card | **Н/Д** (клиент Quest) |
| 7 | `raid_task_id` / `payment_id` в session | Ручная проверка `.hbr/metadata.json` после RAID-телеопа |
| 14 | Recovery slice | **Н/Д** (Backend) |

---

## Автотесты пакета teleop_fetch

Прогон **2026-03-31**:

```bash
cd /home/ubuntu/ros_ws && source devel/setup.bash
catkin build teleop_fetch --no-status --catkin-make-args run_tests
# или:
PYTHONPATH=/home/ubuntu/ros_ws/src/br-vr-dev-sinc/src:$PYTHONPATH python3 -m nose /home/ubuntu/ros_ws/src/br-vr-dev-sinc/tests -v
```

Результат: **8 tests OK** (`test_upload_payload_session_fields`, `test_teleop_state_contract`, `test_operator_buttons`, …). Они покрывают **контракт upload** (`teleopControl`, `acceptedAtUtcIso`), а **не** спринтовые облачные сценарии.

---

## Пробелы относительно спринта (для бэклога)

1. Явная машина состояний **TELEOP_READY** и лог события для API.
2. **Bilateral confirm** и временные метки в `metadata.json` / multipart.
3. **RTT preflight** на стороне клиента/шлюза с записью причины в `events.jsonl` и блокировкой сессии.
4. Связка **TELEOP_TAKEOVER** / CRITICAL с записью и облаком — отдельные узлы или Backend.
