# VR Teleop (br-vr-dev-sinc) — индекс документации

Вся подробная документация в **`DOC/`**. Корневые [README.md](../README.md) и [DEV_AI.md](../DEV_AI.md) содержат входные точки и ссылки сюда.

## Архитектура стека

- [ARCHITECTURE.md](ARCHITECTURE.md) — уровни абстракции, топики, поток Quest → remapper → IK → `teleop_fetch`.

## Состояние проекта и задачи

- [PROJECT_STATE.md](PROJECT_STATE.md) — статус пакетов и компонентов.
- [TODO.md](TODO.md) — известные проблемы и бэклог.

## Датасеты и формат HBR

- Локально на роботе: при `enable_dataset_recording` в `teleop.launch` поднимаются REST **:9191** и веб-дашборд **`dataset_web_server`** → `http://<робот>:3002/dataset_dashboard.html` (см. [ARCHITECTURE.md](ARCHITECTURE.md) §6).
- [TELEOP_DATAS.md](TELEOP_DATAS.md) — события шлема, контракт upload API.
- [HBR.md](HBR.md) — формат контейнера `.hbr`, хранение.
- [RAID_APP_DATASET_PROXY_SPEC.md](RAID_APP_DATASET_PROXY_SPEC.md) — спецификация для **RAID App** (`x402_raid_app`): HTTP reverse proxy к dataset API на роботе (`:9191`) для операторов через JWT.
- [DATA_NODE_OPERATOR_SESSION_SPEC.md](DATA_NODE_OPERATOR_SESSION_SPEC.md) — для **DATA_NODE**: расширенные поля сессии телеопа, `metadata.json`, multipart `operatorSessionMeta` при `POST /sessions/upload`.

---

Новые функциональные области оформляйте отдельными файлами в `DOC/` и добавляйте пункт в этот индекс + обновляйте README и DEV_AI при смене контрактов.
