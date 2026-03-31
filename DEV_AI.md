# DEV_AI — контекст для агентов (br-vr-dev-sinc / VR Teleop)

## Единая точка входа экосистемы (KYR + x402 + teleop_fetch)

Запуск всей связки и ссылки на документацию: **[../br_bringup/DEV_AI.md](../br_bringup/DEV_AI.md)**, **[../br_bringup/README.md](../br_bringup/README.md)**.

## Назначение

Репозиторий с телеоперацией с Quest VR для двурукого робота (ROS 1 Noetic). Главный пакет: **`teleop_fetch`** — единая публикация команд рук в **`/kyr/bus_servo_in`** → KYR proxy → `/bus_servo/set_position`. Поток данных:

`Quest` → `vr_remapper` (в т.ч. **R_A**) → `pose_source` → `fast_ik` → `teleop_fetch` → KYR. **Голова** при ACTIVE сразу; **руки** на KYR после **L_X**. **`/teleop_state`**: старт и новая сессия — `stop_control`; **L_X** → `get_control`; **L_Y** (если был armed) → `stop_control`. IK: `/teleop_fetch/teleop_state`.

Полный стек по умолчанию: `roslaunch br_bringup ecosystem.launch` (включает `teleop.launch`). Только KYR-шлюз без IK: `with_vr_pipeline:=false`. Узел legacy `teleop_calibration` (T-pose) по умолчанию выключен; включить: `enable_legacy_teleop_calibration:=true` (пробрасывается из `ecosystem.launch` в `teleop.launch`). Руки на KYR при `arm_stream_requires_lx:=true` только после фронта `L_X` на joints — иначе см. `DOC/ARCHITECTURE.md` и параметр `~arm_stream_requires_lx`. Датасеты: по умолчанию **`dataset_recorder` + `dataset_upload_server` (:9191) + `dataset_web_server` (:3002, `web/dataset_dashboard.html`)**; выключить: `enable_dataset_recording:=false`. Peaq-клейм в `metadata.json` / multipart: **`/teleop_fetch/set_peaq_dataset_claim`**, см. [DOC/DATA_NODE_PEAQ_CLAIM_SPEC.md](DOC/DATA_NODE_PEAQ_CLAIM_SPEC.md).

`ERR_CONNECTION_REFUSED` на **:3002**: нода `/dataset_web_server` не слушает (часто второй `roslaunch` на тот же rosmaster — см. лог `new node registered with same name`); при **`with_vr_pipeline:=false`** веб датасетов не стартует. Подробнее: [DOC/ARCHITECTURE.md](DOC/ARCHITECTURE.md) §6.

## Ключевые пути

- `teleop_fetch/` — `vr_remapper_node.py`, `pose_source_node.py`, `teleop_node.py`, `config/vr_remapper.yaml`, датасеты `.hbr`.
- `my_package/` — `fast_ik_node.cpp`, `config/fast_ik.yaml`.

## Документация

Индекс: [DOC/README.md](DOC/README.md). Обязательно читать [DOC/ARCHITECTURE.md](DOC/ARCHITECTURE.md) и [DOC/PROJECT_STATE.md](DOC/PROJECT_STATE.md). Баги и долг: [DOC/TODO.md](DOC/TODO.md).

## Обязанности при правках

1. **Документация** — обновлять все затронутые файлы в `DOC/`; новые подсистемы — новый `.md` в `DOC/` + строка в [DOC/README.md](DOC/README.md) + при необходимости правки [README.md](README.md) и этого файла.
2. **Тесты** — для новой логики добавлять тесты и прогонять весь доступный набор пакета/воркспейса:
   ```bash
   cd /home/ubuntu/ros_ws && source devel/setup.bash
   catkin_make run_tests --pkg teleop_fetch
   # при наличии тестов в my_package:
   # catkin_make run_tests --pkg my_package
   ```
3. **Коммит** — понятное сообщение (область изменения + суть).

## Workspace rule

В каталоге `ros_ws` может быть `.cursor/rules/project-context.mdc` с кратким напоминанием потока VR Teleop; при расхождении с `DOC/` приоритет у **`DOC/`**.
