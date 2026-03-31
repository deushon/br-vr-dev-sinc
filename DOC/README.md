# VR Teleop (br-vr-dev-sinc) — индекс документации

Вся подробная документация в **`DOC/`**. Корневые [README.md](../README.md) и [DEV_AI.md](../DEV_AI.md) содержат входные точки и ссылки сюда.

## Архитектура стека

- [ARCHITECTURE.md](ARCHITECTURE.md) — уровни абстракции, топики, поток Quest → remapper → IK → `teleop_fetch`.
- Пост-оплата оператору SOL после `close_session`: вызов `/x402/complete_teleop_payment` из `teleop_node` (зависимость `rospy_x402`); спека ответа RAID: [../../rospy_x402/DOC/RAID_APP_TELEOP_HELP_FULL_CYCLE_X402_SPEC.md](../../rospy_x402/DOC/RAID_APP_TELEOP_HELP_FULL_CYCLE_X402_SPEC.md).

## Состояние проекта и задачи

- [PROJECT_STATE.md](PROJECT_STATE.md) — статус пакетов и компонентов.
- [TODO.md](TODO.md) — известные проблемы и бэклог.

## Датасеты и формат HBR

- Локально на роботе: при `enable_dataset_recording` в `teleop.launch` поднимаются REST **:9191** и веб-дашборд **`dataset_web_server`** → `http://<робот>:3002/dataset_dashboard.html` (см. [ARCHITECTURE.md](ARCHITECTURE.md) §6).
- [TELEOP_DATAS.md](TELEOP_DATAS.md) — события шлема, контракт upload API.
- [HBR.md](HBR.md) — формат контейнера `.hbr`, хранение.
- [RAID_APP_DATASET_PROXY_SPEC.md](RAID_APP_DATASET_PROXY_SPEC.md) — спецификация для **RAID App** (`x402_raid_app`): HTTP reverse proxy к dataset API на роботе (`:9191`) для операторов через JWT.
- [RAID_APP_PEAQ_CLAIM_SPEC.md](RAID_APP_PEAQ_CLAIM_SPEC.md) — **RAID App**: peaq claim на Agung, расширение `teleop/help` и `GET …/peaq/claim`.
- [DATA_NODE_OPERATOR_SESSION_SPEC.md](DATA_NODE_OPERATOR_SESSION_SPEC.md) — для **DATA_NODE**: расширенные поля сессии телеопа, `metadata.json`, multipart `operatorSessionMeta` при `POST /sessions/upload`.
- [DATA_NODE_PEAQ_CLAIM_SPEC.md](DATA_NODE_PEAQ_CLAIM_SPEC.md) — **DATA_NODE**: опциональная multipart-часть `peaqClaim` при выгрузке датасета с робота.

---

Новые функциональные области оформляйте отдельными файлами в `DOC/` и добавляйте пункт в этот индекс + обновляйте README и DEV_AI при смене контрактов.
