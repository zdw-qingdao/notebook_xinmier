# 数据组织设计

## 目录结构

```
user1-workspace/
├── projects_A/
│   ├── meta.json                            # 项目元信息
│   ├── data_split/                         # 每一次上传，每个split的数据
│   │   ├── data1/                              # 工位_版本
│   │   │   ├── video/                           # 原始视频
│   │   │   │   ├── 20260601_0900.mp4
│   │   │   │   └── 20260601_0900.mp4
│   │   │   ├── images/                          # 抽帧和去重后的图片
│   │   │   │   ├── 20260601_0900/               # 每个视频对应一个文件夹
│   │   │   │   │   ├── 000001.jpg
│   │   │   │   │   ├── 000002.jpg
│   │   │   │   │   └── ...
│   │   │   │   └── 20260601_0900/
│   │   │   │       ├── 000001.jpg
│   │   │   │       └── ...
│   │   │   ├── meta.json                        # 采集元信息
│   │   │   ├── annotations/                     # 图片的所有标注，包含inference的结果和手动标注的结果
│   │   │   │   └── det_sam3_0/                  # 检测标注：SAM3 自动标注
│   │   │   │       ├── labels/                  # 与 images/ 下的文件夹一一对应
│   │   │   │       │   ├── 20260601_0900/
│   │   │   │       │   │   ├── 000001.json
│   │   │   │       │   │   ├── 000002.json
│   │   │   │       │   │   └── ...
│   │   │   │       │   └── 20260601_0900/
│   │   │   │       │       └── ...
│   │   │   │       └── meta.json
    ├── datasets/                                 # 训练集（引用 project 中的数据组合而成）
          person_det_0
            dataset_info.json
            models/                                   # 训练产出的模型
            └── person_det_yolo11n_0/
                ├── weights/
                ├── deployment/
                ├── config/                           # 训练时使用的配置快照
                │   ├── dataset.json                  # 复制的训练集 json
                │   └── model.json                    # 复制的模型配置文件
                ├── meta.json
                └── inference/                        # 视频的所有标注，包含inference的结果和手动标注的结果
                    ├── collection_data/
                    │   └── 工厂1/
                    │       └── 工位A_0/
                    │           ├── video/
                    │           │   └── 20260601_0900
                    │           └── images/
                    │               └── 20260601_0900
                    ├── train_set/
                    │   └── 工厂1/
                    │       └── 工位A_0/
                    │           └── 20260601_0900/
                    │               ├── 000001.json
                    │               ├── 000002.json
                    │               └── ...
                    └── val_set/
                        └── 工厂1/
                            └── 工位A_0/
                                └── 20260601_0900/
                                    ├── 003001.json
                                    ├── 003002.json
                                    └── ...


```

## 标注版本命名

```
{任务类型}_{标注方式}_{版本号}

任务类型: det / seg / pose
标注方式: manual / sam3 ...
版本号:  0, 1, 2 ...
```

示例：
- `det_sam3_0` — SAM3 自动标注的检测框
- `det_manual_0` — 人工修正后的第二版
- `seg_labelme_0` — LabelMe 标注的分割
- `det_modelA_0` — 用已有模型 A 预标注的结果

## 项目元信息 collections/项目/meta.json

```json
{
  "project": "工厂1",
  "type": "human_detection",
  "device": "",
  "start_date": "2025-10-01",
  "end_date": "2025-10-01",
  "status": "进行中",
  "notes": "人体检测项目",
  "doc_link": ""
}
```

## 采集元信息 collections/项目/采集批次/meta.json

```json
{
  "factory": "工厂1",
  "location": "工位A",
  "date": "2026-06-01",
  "device": "",
  "resolution": "1920x1080",
  "count": 3500,
  "collector": "",
  "notes": "夜班场景，光线较暗"
}
```

## 标注版本元信息 annotations/xxx/meta.json

```json
{
  "type": "detection",
  "method": "yolo",
  "used_model": "xxxxxxxxx",
  "parent": "det_sam3_v1",   # 指向上一个标注版本，形成版本链
  "classes": ["person"],
  "reviewed": true,
  "reviewer": "",
  "create_time": "2026-06-05-xx-xx",
  "update_time": "2026-06-05-xx-xx",
  "notes": "基于 v1 人工修正了 200 张漏标"
}

{
  "type": "detection",
  "method": "manual",
  "used_model": "",
  "parent": "det_sam3_v1",   # 指向上一个标注版本，形成版本链
  "classes": ["person"],
  "reviewed": true,
  "reviewer": "",
  "create_time": "2026-06-05-xx-xx",
  "update_time": "2026-06-05-xx-xx",
  "notes": "基于 v1 人工修正了 200 张漏标"
}
```

## 创建数据集 datasets/xxxx/dataset_info.json
训练集不复制数据，只记录引用关系：
```json
{
  "name": "person_det_0",
  "created_at": "2026-06-08",
  "splits": {
    "train": [
      {
        "collection": "工厂1/工位A_0",
        "annotation": "det_sam3_0",
        "index": [0,3000]
      }
    ],
    "val": [
      {
        "collection": "工厂1/工位A_0",
        "annotation": "det_sam3_0",
        "index": [3000,3500]
      }
    ]
  }
}
```

## 模型元信息 models/xxx/meta.json
```json
{
  "name": "person_det_yolo11n_0",
  "code_config": "",
  "pretrained_model": "",
  "dataset": "datasets/xxxx.json",
  "create_time": "2026-06-08-14-30",
  "tags": [],
  "training_config": {
    "device": [0]
  },
  "training_log": {
    "precision": 0.88,
    "recall": 0.82,
    "train_time": "3h20m",
  },
}
```

## 版本关系示意

```
collections/工厂1/工位A_0/
  ├── images/                （原始图片，不变）
  ├── meta.json
  └── annotations/
        ├── det_sam3_0          （自动标注）
        │        │
        │        ▼
        ├── det_manual_1        （人工修正）  ← 训练集 person_det_0 引用这个版本
        │        │
        │        ▼
        ├── det_manual_2        （补充标注） ← 训练集 person_det_1 引用这个版本
```

## 设计要点

| 要点 | 说明 |
|------|------|
| **标注版本独立** | 每个版本是一套标签，可以进行版本对比，版本链可追溯 |
| **训练集是引用** | datasets 只记录用了哪个 collection 的哪个标注版本，不复制数据 |
| **代码集中管理** | 代码托管到bitbucket，记录每次使用的代码commit id |
| **模型训练结果集中管理** | 可以使用模型训练的结果作为之后训练的预训练模型或进行自动标注 |

