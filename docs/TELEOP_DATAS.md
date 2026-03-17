# TELEOP_DATAS Implementation Status

Implemented in `teleop_fetch`:

- ROS recorder control topic: `/record_sessions` (`dataset_recorder_node.py`)
- Upload API endpoint: `POST /upload_dataset` on port `9191` (`dataset_upload_server.py`)
- Session binding logic: upload payload is attached to existing `recordId` session and persisted into `.hbr/operator/*`

---

# 1. JSON события записи в ROS (`/record_sessions`)

Это сообщение, которое вы шлёте при старте и остановке записи.

## Формат `std_msgs/String`

В rosbridge это уйдёт как:
```json
{  
  "op": "publish",  
  "topic": "/record_sessions",  
  "msg": {  
    "data": "{\"record_id\":\"7d7d3d7c4f1b4f2c8d5c2b0e0a123456\",\"event_type\":\"start\",\"app_session_id\":\"f1d2d2f924e986ac86fdf7b36c94bcdf\",\"timestamp_unix_ns\":1760700000123456789,\"timestamp_ros_unix_ns\":1760700000223456789,\"ntp_time_synchronized\":true,\"ros_time_synchronized\":true,\"pose_topic\":\"/quest/poses\",\"joint_topic\":\"/quest/joints\",\"send_hz\":10.0}"  
  }  
}

```

А полезная нагрузка внутри `msg.data` выглядит так:

```json
{  
  "record_id": "7d7d3d7c4f1b4f2c8d5c2b0e0a123456",  
  "event_type": "start",  
  "app_session_id": "f1d2d2f924e986ac86fdf7b36c94bcdf",  
  "timestamp_unix_ns": 1760700000123456789,  
  "timestamp_ros_unix_ns": 1760700000223456789,  
  "ntp_time_synchronized": true,  
  "ros_time_synchronized": true,  
  "pose_topic": "/quest/poses",  
  "joint_topic": "/quest/joints",  
  "send_hz": 10.0  
}
```

Для окончания записи будет то же самое, только:

```json
{  
  "event_type": "stop"  
}
```

---

# 2. Большой JSON для REST `upload_dataset`

Это итоговый payload, который собирает `DatasetManager`.

## Верхний уровень

```json
{  
  "source": "unity_quest_dataset",  
  "generatedUtcIso": "2026-03-17T18:45:12.3456789Z",  
  "records": []  
}
```

---

# 3. Структура одного элемента `records[]`

```json
{  
  "recordId": "7d7d3d7c4f1b4f2c8d5c2b0e0a123456",  
  "label": "Подъезд к точке A",  
  "taskName": "Доехать до маркера у стены",  
  "data": {}  
}
```

Где:

- `recordId` — уникальный id записи
- `label` — подпись/метка из `RecordData.TextField`
- `taskName` — имя выбранного задания
- `data` — записанная телеметрическая сессия

---

# 4. Структура `data` (`RecordedSession`)

```json
{  
  "recordId": "7d7d3d7c4f1b4f2c8d5c2b0e0a123456",  
  
  "startedLocalUnixTimeNs": 1760700000000000000,  
  "endedLocalUnixTimeNs": 1760700005000000000,  
  
  "startedEstimatedExternalUnixTimeNs": 1760700000100000000,  
  "endedEstimatedExternalUnixTimeNs": 1760700005100000000,  
  
  "startedEstimatedRosUnixTimeNs": 1760700000200000000,  
  "endedEstimatedRosUnixTimeNs": 1760700005200000000,  
  
  "rosTimeWasSynchronizedAtStart": true,  
  "rosTimeWasSynchronizedAtEnd": true,  
  
  "ntpTimeWasSynchronizedAtStart": true,  
  "ntpTimeWasSynchronizedAtEnd": true,  
  
  "sourceWsUrl": "ws://192.168.1.100:9090",  
  "sourceSendHz": 10.0,  
  
  "frames": []  
}
```

### Значение полей

- `startedLocalUnixTimeNs`, `endedLocalUnixTimeNs`  
    локальное время устройства в ns
- `startedEstimatedExternalUnixTimeNs`, `endedEstimatedExternalUnixTimeNs`  
    время, скорректированное по NTP
- `startedEstimatedRosUnixTimeNs`, `endedEstimatedRosUnixTimeNs`  
    время, дополнительно скорректированное под ROS clock
- `rosTimeWasSynchronizedAtStart/End`  
    была ли активна синхронизация с ROS
- `ntpTimeWasSynchronizedAtStart/End`  
    была ли активна синхронизация с NTP
- `sourceWsUrl`  
    адрес rosbridge
- `sourceSendHz`  
    частота отправки данных
- `frames`  
    массив кадров телеметрии

---

# 5. Структура одного `frame` (`RecordedFrame`)

```json
{  
  "localUnixTimeNs": 1760700000123456789,  
  "localMonotonicSec": 123.456789,  
  
  "estimatedExternalUnixTimeNs": 1760700000223456789,  
  "estimatedRosUnixTimeNs": 1760700000323456789,  
  
  "ntpTimeSynchronized": true,  
  "ntpClockOffsetSec": 0.102314,  
  "ntpSyncRttSec": 0.0184,  
  
  "rosClockOffsetSec": 0.054211,  
  "syncRttSec": 0.0128,  
  "rosTimeSynchronized": true,  
  
  "inputMode": "controllers",  
  
  "head": {},  
  "left": {},  
  "right": {},  
  
  "joints": []  
}
```

---

# 6. Структура позы (`RecordedPose`)

```json
{  
  "position": {  
    "x": 0.12,  
    "y": 1.43,  
    "z": -0.55  
  },  
  "orientation": {  
    "x": 0.0,  
    "y": 0.707,  
    "z": 0.0,  
    "w": 0.707  
  }  
}
```

Это одинаково для:

- `head`
- `left`
- `right`
    

---

# 7. Структура `joints`

```json
[  
  { "name": "L_grip", "value": 0.72 },  
  { "name": "L_index", "value": 0.15 },  
  { "name": "R_grip", "value": 0.01 },  
  { "name": "R_index", "value": 0.84 },  
  { "name": "L_X", "value": 1.0 },  
  { "name": "L_Y", "value": 0.0 },  
  { "name": "R_A", "value": 0.0 },  
  { "name": "R_B", "value": 1.0 },  
  { "name": "L_stick_x", "value": -0.23 },  
  { "name": "L_stick_y", "value": 0.91 },  
  { "name": "L_stick_click", "value": 0.0 },  
  { "name": "L_stick_touch", "value": 1.0 }  
]
```
Если режим `hands`, то там будут, например:

```json
[  
  { "name": "L_grip", "value": 0.31 },  
  { "name": "L_index", "value": 0.85 },  
  { "name": "L_pinch_index", "value": 0.92 },  
  { "name": "L_pinch_middle", "value": 0.11 },  
  { "name": "L_pinch_ring", "value": 0.04 },  
  { "name": "L_pinch_little", "value": 0.01 }  
]
```

---

# 8. Полный пример итогового payload

```json
{  
  "source": "unity_quest_dataset",  
  "generatedUtcIso": "2026-03-17T18:45:12.3456789Z",  
  "records": [  
    {  
      "recordId": "7d7d3d7c4f1b4f2c8d5c2b0e0a123456",  
      "label": "Подъезд к точке A",  
      "taskName": "Доехать до маркера у стены",  
      "data": {  
        "recordId": "7d7d3d7c4f1b4f2c8d5c2b0e0a123456",  
        "startedLocalUnixTimeNs": 1760700000000000000,  
        "endedLocalUnixTimeNs": 1760700005000000000,  
        "startedEstimatedExternalUnixTimeNs": 1760700000100000000,  
        "endedEstimatedExternalUnixTimeNs": 1760700005100000000,  
        "startedEstimatedRosUnixTimeNs": 1760700000200000000,  
        "endedEstimatedRosUnixTimeNs": 1760700005200000000,  
        "rosTimeWasSynchronizedAtStart": true,  
        "rosTimeWasSynchronizedAtEnd": true,  
        "ntpTimeWasSynchronizedAtStart": true,  
        "ntpTimeWasSynchronizedAtEnd": true,  
        "sourceWsUrl": "ws://192.168.1.100:9090",  
        "sourceSendHz": 10.0,  
        "frames": [  
          {  
            "localUnixTimeNs": 1760700000123456789,  
            "localMonotonicSec": 123.456789,  
            "estimatedExternalUnixTimeNs": 1760700000223456789,  
            "estimatedRosUnixTimeNs": 1760700000323456789,  
            "ntpTimeSynchronized": true,  
            "ntpClockOffsetSec": 0.102314,  
            "ntpSyncRttSec": 0.0184,  
            "rosClockOffsetSec": 0.054211,  
            "syncRttSec": 0.0128,  
            "rosTimeSynchronized": true,  
            "inputMode": "controllers",  
            "head": {  
              "position": { "x": 0.12, "y": 1.43, "z": -0.55 },  
              "orientation": { "x": 0.0, "y": 0.707, "z": 0.0, "w": 0.707 }  
            },  
            "left": {  
              "position": { "x": -0.23, "y": -0.18, "z": 0.44 },  
              "orientation": { "x": 0.01, "y": 0.12, "z": -0.02, "w": 0.99 }  
            },  
            "right": {  
              "position": { "x": 0.28, "y": -0.16, "z": 0.41 },  
              "orientation": { "x": -0.03, "y": -0.10, "z": 0.04, "w": 0.99 }  
            },  
            "joints": [  
              { "name": "L_grip", "value": 0.72 },  
              { "name": "L_index", "value": 0.15 },  
              { "name": "R_grip", "value": 0.01 },  
              { "name": "R_index", "value": 0.84 },  
              { "name": "L_X", "value": 1.0 },  
              { "name": "L_Y", "value": 0.0 },  
              { "name": "R_A", "value": 0.0 },  
              { "name": "R_B", "value": 1.0 },  
              { "name": "L_stick_x", "value": -0.23 },  
              { "name": "L_stick_y", "value": 0.91 },  
              { "name": "L_stick_click", "value": 0.0 },  
              { "name": "L_stick_touch", "value": 1.0 }  
            ]  
          }  
        ]  
      }  
    }  
  ]  
}
```

---

# 9. Формальная схема

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/unity-quest-dataset.schema.json",
  "title": "Unity Quest Dataset Upload",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source",
    "generatedUtcIso",
    "records"
  ],
  "properties": {
    "source": {
      "type": "string",
      "minLength": 1
    },
    "generatedUtcIso": {
      "type": "string",
      "format": "date-time"
    },
    "records": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/DatasetUploadRecord"
      }
    }
  },
  "$defs": {
    "UnixTimeNs": {
      "type": "integer",
      "description": "Unix timestamp in nanoseconds"
    },
    "JsonVec3": {
      "type": "object",
      "additionalProperties": false,
      "required": ["x", "y", "z"],
      "properties": {
        "x": { "type": "number" },
        "y": { "type": "number" },
        "z": { "type": "number" }
      }
    },
    "JsonQuat": {
      "type": "object",
      "additionalProperties": false,
      "required": ["x", "y", "z", "w"],
      "properties": {
        "x": { "type": "number" },
        "y": { "type": "number" },
        "z": { "type": "number" },
        "w": { "type": "number" }
      }
    },
    "RecordedPose": {
      "type": "object",
      "additionalProperties": false,
      "required": ["position", "orientation"],
      "properties": {
        "position": { "$ref": "#/$defs/JsonVec3" },
        "orientation": { "$ref": "#/$defs/JsonQuat" }
      }
    },
    "RecordedJointValue": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "value"],
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1
        },
        "value": {
          "type": "number"
        }
      }
    },
    "RecordedFrame": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "localUnixTimeNs",
        "localMonotonicSec",
        "estimatedExternalUnixTimeNs",
        "estimatedRosUnixTimeNs",
        "ntpTimeSynchronized",
        "ntpClockOffsetSec",
        "ntpSyncRttSec",
        "rosClockOffsetSec",
        "syncRttSec",
        "rosTimeSynchronized",
        "inputMode",
        "head",
        "left",
        "right",
        "joints"
      ],
      "properties": {
        "localUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "localMonotonicSec": {
          "type": "number"
        },
        "estimatedExternalUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "estimatedRosUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "ntpTimeSynchronized": {
          "type": "boolean"
        },
        "ntpClockOffsetSec": {
          "type": "number"
        },
        "ntpSyncRttSec": {
          "type": "number",
          "minimum": 0
        },
        "rosClockOffsetSec": {
          "type": "number"
        },
        "syncRttSec": {
          "type": "number",
          "minimum": 0
        },
        "rosTimeSynchronized": {
          "type": "boolean"
        },
        "inputMode": {
          "type": "string",
          "enum": ["controllers", "hands", "none"]
        },
        "head": {
          "$ref": "#/$defs/RecordedPose"
        },
        "left": {
          "$ref": "#/$defs/RecordedPose"
        },
        "right": {
          "$ref": "#/$defs/RecordedPose"
        },
        "joints": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/RecordedJointValue"
          }
        }
      }
    },
    "RecordedSession": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "recordId",
        "startedLocalUnixTimeNs",
        "endedLocalUnixTimeNs",
        "startedEstimatedExternalUnixTimeNs",
        "endedEstimatedExternalUnixTimeNs",
        "startedEstimatedRosUnixTimeNs",
        "endedEstimatedRosUnixTimeNs",
        "rosTimeWasSynchronizedAtStart",
        "rosTimeWasSynchronizedAtEnd",
        "ntpTimeWasSynchronizedAtStart",
        "ntpTimeWasSynchronizedAtEnd",
        "sourceWsUrl",
        "sourceSendHz",
        "frames"
      ],
      "properties": {
        "recordId": {
          "type": "string",
          "minLength": 1
        },
        "startedLocalUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "endedLocalUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "startedEstimatedExternalUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "endedEstimatedExternalUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "startedEstimatedRosUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "endedEstimatedRosUnixTimeNs": {
          "$ref": "#/$defs/UnixTimeNs"
        },
        "rosTimeWasSynchronizedAtStart": {
          "type": "boolean"
        },
        "rosTimeWasSynchronizedAtEnd": {
          "type": "boolean"
        },
        "ntpTimeWasSynchronizedAtStart": {
          "type": "boolean"
        },
        "ntpTimeWasSynchronizedAtEnd": {
          "type": "boolean"
        },
        "sourceWsUrl": {
          "type": "string",
          "minLength": 1
        },
        "sourceSendHz": {
          "type": "number",
          "exclusiveMinimum": 0
        },
        "frames": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/RecordedFrame"
          }
        }
      }
    },
    "DatasetUploadRecord": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "recordId",
        "label",
        "taskName",
        "data"
      ],
      "properties": {
        "recordId": {
          "type": "string",
          "minLength": 1
        },
        "label": {
          "type": "string"
        },
        "taskName": {
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/RecordedSession"
        }
      }
    }
  }
}
```