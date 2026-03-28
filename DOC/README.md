# VR Teleop (br-vr-dev-sinc) — индекс документации

Вся подробная документация в **`DOC/`**. Корневые [README.md](../README.md) и [DEV_AI.md](../DEV_AI.md) содержат входные точки и ссылки сюда.

## Архитектура стека

- [ARCHITECTURE.md](ARCHITECTURE.md) — уровни абстракции, топики, поток Quest → remapper → IK → `teleop_fetch`.

## Состояние проекта и задачи

- [PROJECT_STATE.md](PROJECT_STATE.md) — статус пакетов и компонентов.
- [TODO.md](TODO.md) — известные проблемы и бэклог.

## Датасеты и формат HBR

- [TELEOP_DATAS.md](TELEOP_DATAS.md) — события шлема, контракт upload API.
- [HBR.md](HBR.md) — формат контейнера `.hbr`, хранение.

---

Новые функциональные области оформляйте отдельными файлами в `DOC/` и добавляйте пункт в этот индекс + обновляйте README и DEV_AI при смене контрактов.
