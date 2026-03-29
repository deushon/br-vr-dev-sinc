# DEV_AI — контекст для агентов (br-vr-dev-sinc / VR Teleop)

## Единая точка входа экосистемы (KYR + x402 + teleop_fetch)

Запуск всей связки и ссылки на документацию: **[../br_bringup/DEV_AI.md](../br_bringup/DEV_AI.md)**, **[../br_bringup/README.md](../br_bringup/README.md)**.

## Назначение

Репозиторий с телеоперацией с Quest VR для двурукого робота (ROS 1 Noetic). Главный пакет: **`teleop_fetch`** — единая публикация команд рук в **`/kyr/bus_servo_in`** → KYR proxy → `/bus_servo/set_position`. Поток данных:

`Quest` → `vr_remapper` → `pose_source` → `fast_ik` (`my_package`) → `teleop_fetch` → KYR. Обратная связь: **`/teleop_state`** (String, latched: `get_control` / `stop_control`) и **`/teleop_fetch/teleop_state`** (TeleopState от fast_ik).

Полный стек по умолчанию: `roslaunch br_bringup ecosystem.launch` (включает `teleop.launch`). Только KYR-шлюз без IK: `with_vr_pipeline:=false`.

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
