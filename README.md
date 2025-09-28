# Teleop Fetch

ROS пакет для телеоперации робота Fetch с использованием VR гарнитуры Quest.

## Возможности

- Управление головой робота на основе положения головы оператора
- Готовность к добавлению управления руками
- Настраиваемые параметры чувствительности

## Зависимости

- ROS (tested with ROS Noetic)
- Python 3
- NumPy
- geometry_msgs
- sensor_msgs
- std_msgs

## Установка

1. Убедитесь, что у вас установлен ROS
2. Скопируйте пакет в ваш workspace
3. Выполните `catkin_make` или `catkin build`

## Использование

### Запуск ноды

```bash
# Прямой запуск
rosrun teleop_fetch fetcher.py

# Или через launch файл
roslaunch teleop_fetch teleop_fetch.launch
```

### Параметры

- `head_sensitivity` (по умолчанию: 1.0) - чувствительность управления головой
- `max_head_pan` (по умолчанию: 2.0) - максимальный поворот головы влево/вправо
- `max_head_tilt` (по умолчанию: 2.0) - максимальный наклон головы вверх/вниз
- `movement_duration` (по умолчанию: 0.2) - время на перемещение головы

### Топики

#### Входные топики:
- `/quest/poses` (geometry_msgs/PoseArray) - данные о положении головы и рук оператора
- `/quest/joints` (sensor_msgs/JointState) - данные о суставах рук оператора

#### Выходные топики:
- `/head_pan_controller/command` (teleop_fetch/HeadCommand) - команды поворота головы {position, duration}
- `/head_tilt_controller/command` (teleop_fetch/HeadCommand) - команды наклона головы {position, duration}

## Структура кода

Код организован в класс `TeleopFetcher` с методами:

- `pose_callback()` - обработка данных о положении головы и рук
- `joints_callback()` - обработка данных о суставах рук
- `process_head_control()` - логика управления головой
- `process_arms_control()` - заготовка для управления руками

## Будущие расширения

Код готов для добавления управления руками робота. Методы `process_arms_control()` и соответствующие публикаторы можно легко добавить в будущем.
