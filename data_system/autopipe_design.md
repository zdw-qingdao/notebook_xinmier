# 数据平台存储系统设计

## 架构总览

```
┌────────────────────────────────────┐
│            Web 平台 / API           │
└──────┬────────────────┬────────────┘
       │                │
┌──────▼──────┐   ┌─────▼───────────┐
│ PostgreSQL  │   │ MinIO (对象存储)  │
│             │   │                  │
│ • 用户/权限  │   │ • 图片/视频       │
│ • 项目元数据 │   │ • 模型权重        │
│ • 采集元数据 │   │ • 部署包          │
│ • 标注版本   │   │ • 训练配置快照     │
│ • 标注信息   │   │ • 推理结果        │
│ • 数据集定义 │   │ • 训练导出包      │
│ • 训练记录   │   │                  │
└─────────────┘   └─────────────────┘
```

---

## 一、对象存储目录结构（MinIO）

Bucket: `data-platform`

```
data-platform/
├── {workspace_name}/
│   └── {project_name}/
│       ├── data_clip/
│       │   └── {split_name}/                          # 每一次上传的数据批次
│       │       ├── video/                             # 原始视频
│       │       │   ├── 20260601_0900.mp4
│       │       │   └── 20260602_1400.mp4
│       │       └── images/                            # 抽帧和去重后的图片
│       │           ├── 20260601_0900/                 # 每个视频对应一个文件夹
│       │           │   ├── 000001.jpg
│       │           │   ├── 000002.jpg
│       │           │   └── ...
│       │           └── 20260602_1400/
│       │               ├── 000001.jpg
│       │               └── ...
│       │
│       └── datasets/
│           └── {dataset_name}/
│               └── models/
│                   └── {model_name}/
│                       ├── weights/                   # 模型权重
│                       │   ├── best.pt
│                       │   └── last.pt
│                       ├── deployment/                # 部署用的模型文件
│                       │   └── best.onnx
│                       ├── config/                    # 训练时使用的配置快照
│                       │   ├── dataset.json
│                       │   └── model.json
│                       └── inference/                 # 推理结果
│                           ├── collection_data/       # 对采集数据的推理
│                           │   └── {split_name}/
│                           │       ├── video/
│                           │       │   └── 20260601_0900/
│                           │       │       ├── 000001.json
│                           │       │       └── ...
│                           │       └── images/
│                           │           └── 20260601_0900/
│                           │               ├── 000001.json
│                           │               └── ...
│                           ├── train_set/             # 对训练集的推理
│                           │   └── {split_name}/
│                           │       └── 20260601_0900/
│                           │           ├── 000001.json
│                           │           └── ...
│                           └── val_set/               # 对验证集的推理
│                               └── {split_name}/
│                                   └── 20260601_0900/
│                                       ├── 000001.json
│                                       └── ...
```

### 目录说明

| 路径 | 内容 | 说明 |
|------|------|------|
| `data_clip/{split}/video/` | 原始视频文件 | .mp4，体积最大 |
| `data_clip/{split}/images/` | 抽帧和去重的图片 | 按来源视频分文件夹 |
| `datasets/{dataset}/models/{model}/weights/` | 模型权重 | best.pt / last.pt |
| `datasets/{dataset}/models/{model}/deployment/` | 部署文件 | ONNX / TensorRT 等 |
| `datasets/{dataset}/models/{model}/config/` | 训练配置快照 | 训练时冻结的数据集和模型配置 |
| `datasets/{dataset}/models/{model}/inference/` | 推理结果 | JSON 文件，批量生成 |

---

## 二、数据库表结构（PostgreSQL）

### 2.1 用户与权限

#### users — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 用户 ID |
| username | TEXT UNIQUE NOT NULL | 用户名 |
| password_hash | TEXT NOT NULL | 密码哈希 |
| email | TEXT | 邮箱 |
| role | TEXT DEFAULT 'user' | 全局角色：admin / user |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### workspaces — 工作空间表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 工作空间 ID |
| name | TEXT NOT NULL | 工作空间名称 |
| owner_id | INT REFERENCES users(id) | 所有者 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE workspaces (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### workspace_permissions — 工作空间权限表

允许将其他用户授权到某个 workspace 下的某些 project。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 权限 ID |
| workspace_id | INT REFERENCES workspaces(id) | 工作空间 |
| project_id | INT REFERENCES projects(id) | 项目（NULL 表示整个 workspace） |
| user_id | INT REFERENCES users(id) | 被授权用户 |
| permission | TEXT NOT NULL | 权限级别：read / write / admin |
| granted_by | INT REFERENCES users(id) | 授权人 |
| created_at | TIMESTAMP DEFAULT NOW() | 授权时间 |

```sql
CREATE TABLE workspace_permissions (
    id SERIAL PRIMARY KEY,
    workspace_id INT REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    permission TEXT NOT NULL,
    granted_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workspace_id, project_id, user_id)
);
```

权限判断逻辑：
- workspace.owner_id = 当前用户 → 拥有该 workspace 所有权限
- workspace_permissions 中 project_id IS NULL → 拥有该 workspace 下所有 project 的对应权限
- workspace_permissions 中 project_id = 具体值 → 仅拥有该 project 的对应权限

---

### 2.2 项目与数据采集

#### projects — 项目表

对应原 `projects_A/meta.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 项目 ID |
| workspace_id | INT REFERENCES workspaces(id) | 所属工作空间 |
| name | TEXT NOT NULL | 项目名称（如"工厂1"） |
| type | TEXT | 项目类型（human_detection 等） |
| status | TEXT DEFAULT '进行中' | 状态 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    workspace_id INT REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT,
    status TEXT DEFAULT '进行中',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### data_clips — 数据批次表

对应原 `data_clip/{split_name}/meta.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 批次 ID |
| project_id | INT REFERENCES projects(id) | 所属项目 |
| name | TEXT NOT NULL | 批次名称（如"工位A_0"） |
| image_count | INT DEFAULT 0 | 图片数量 |
| collector | TEXT | 采集人 |
| notes | TEXT | 备注 |
| storage_prefix | TEXT | 对象存储路径前缀 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE data_clips (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    image_count INT DEFAULT 0,
    collector TEXT,
    notes TEXT,
    storage_prefix TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### images — 图片表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 图片 ID |
| data_clip_id | INT REFERENCES data_clips(id) | 所属数据批次 |
| video_source | TEXT | 来源视频名称（如"20260601_0900"） |
| file_name | TEXT NOT NULL | 文件名（如"000001.jpg"） |
| storage_key | TEXT NOT NULL | 对象存储完整路径 |
| width | INT | 图片宽度 |
| height | INT | 图片高度 |
| hash | TEXT | 文件哈希，用于去重 |
| tag_ids | INT[] | 图片级 tag ID 列表（引用 tag_definitions 中 scope='image' 的记录） |
| status | TEXT DEFAULT 'raw' | 状态：raw / annotated / reviewed |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    data_clip_id INT REFERENCES data_clips(id) ON DELETE CASCADE,
    video_source TEXT,
    file_name TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    width INT,
    height INT,
    hash TEXT,
    tag_ids INT[],
    status TEXT DEFAULT 'raw',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_images_split ON images(data_clip_id);
CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_video ON images(video_source);
CREATE UNIQUE INDEX idx_images_hash ON images(hash);
```

---

### 2.3 标注

#### tag_definitions — 标签(tag)定义表

定义每个项目可用的 tag，分为图片级 tag 和标注级 tag。标注时从预设列表中选择。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | tag 定义 ID |
| project_id | INT REFERENCES projects(id) | 所属项目 |
| scope | TEXT NOT NULL | 作用范围：image / annotation |
| name | TEXT NOT NULL | tag 名称（如 occluded、low_light） |
| description | TEXT | tag 说明 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE tag_definitions (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    scope TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, scope, name)
);
```

scope 取值说明：
- `image` — 图片级 tag（如 low_light、blurry、daytime）
- `annotation` — 标注级 tag（如 occluded、truncated、crowd）

#### labels — 标签定义表

对应 JSON 中的 `labels` 字段，每个项目独立定义标签。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 标签 ID |
| project_id | INT REFERENCES projects(id) | 所属项目 |
| name | TEXT NOT NULL | 标签名称（person / car 等） |
| color | TEXT | 显示颜色 |
| keypoint_names | JSONB | 关键点名称列表（keypoint 类型专用） |

```sql
CREATE TABLE labels (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT,
    keypoint_names JSONB,
    UNIQUE(project_id, name)
);
```

#### annotation_versions — 标注版本表

对应原 `annotations/{version_name}/meta.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 版本 ID |
| data_clip_id | INT REFERENCES data_clips(id) | 所属数据批次 |
| name | TEXT NOT NULL | 版本名称（如"det_sam3_0"） |
| annotation_type | TEXT NOT NULL | 标注类型：detection / segmentation / keypoint
| method | TEXT | 标注方式：manual / sam3 / 使用的某一个模型
| parent_id | INT REFERENCES annotation_versions(id) | 父版本 ID |
| classes | JSONB | 标注的类别列表 |
| reviewed | BOOLEAN DEFAULT FALSE | 是否已审核 |
| reviewer | TEXT | 审核人 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP DEFAULT NOW() | 更新时间 |

```sql
CREATE TABLE annotation_versions (
    id SERIAL PRIMARY KEY,
    data_clip_id INT REFERENCES data_clips(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    annotation_type TEXT NOT NULL,
    method TEXT,
    parent_id INT REFERENCES annotation_versions(id),
    classes JSONB,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### annotations — 标注信息表

对应 JSON 中每张图片的每个标注实例。使用统一的 `data` 字段存储标注数据，根据所属标注版本的 `annotation_type` 决定数据格式。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 标注 ID |
| image_id | INT REFERENCES images(id) | 所属图片 |
| version_id | INT REFERENCES annotation_versions(id) | 所属标注版本 |
| label_id | INT REFERENCES labels(id) | 标签 ID |
| tag_ids | INT[] | 标注级 tag ID 列表（引用 tag_definitions 中 scope='annotation' 的记录） |
| confidence | REAL | 置信度（0-1，手动标注可为 NULL，模型推理时有值） |
| data | JSONB NOT NULL | 标注数据，格式由标注版本的 annotation_type 决定（见下方说明） |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE annotations (
    id SERIAL PRIMARY KEY,
    image_id INT REFERENCES images(id) ON DELETE CASCADE,
    version_id INT REFERENCES annotation_versions(id) ON DELETE CASCADE,
    label_id INT REFERENCES labels(id),
    tag_ids INT[],
    confidence REAL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_anno_image ON annotations(image_id);
CREATE INDEX idx_anno_version ON annotations(version_id);
CREATE INDEX idx_anno_label ON annotations(label_id);
```

#### data 字段格式说明

`data` 的内容由所属 `annotation_versions.annotation_type` 决定：

所有坐标使用**归一化比例值**（0.0 ~ 1.0），不使用像素值。`x = 像素x / 图片宽度`，`y = 像素y / 图片高度`。这样标注数据与分辨率无关，图片缩放后标注仍然有效。

| annotation_type | data 格式 | 示例 |
|----------------|-----------|------|
| detection | `[x1, y1, x2, y2]` | `[0.104, 0.139, 0.167, 0.417]` |
| detection_rota | `[cx, cy, w, h, angle]` | `[0.135, 0.278, 0.063, 0.278, 15.5]` |
| segmentation | `[[x,y], ...]` | `[[0.109,0.139], [0.135,0.144], [0.161,0.185]]` |
| keypoint | `[[x,y,v], ...]` | `[[0.161,0.079,2], [0.159,0.072,2], [0.166,0.072,0]]` |

各类型详细说明：

- **detection** — `[x1, y1, x2, y2]`，左上角和右下角的归一化坐标
- **detection_rota** — `[cx, cy, w, h, angle]`，中心点归一化坐标、归一化宽高、旋转角度（度，角度不归一化）
- **segmentation** — `[[x1,y1], [x2,y2], ...]`，多边形顶点归一化坐标列表，按顺序连接闭合
- **keypoint** — `[[x1,y1,v1], [x2,y2,v2], ...]`，固定顺序的关键点列表，xy 为归一化坐标，v 表示可见性（0=未标注，1=遮挡，2=可见），顺序由 `labels.keypoint_names` 定义

转换公式：
- 存入：`x_norm = x_pixel / width`，`y_norm = y_pixel / height`
- 读取：`x_pixel = x_norm * width`，`y_pixel = y_norm * height`
- 图片宽高从 `images` 表的 `width`、`height` 字段获取

---

### 2.4 数据集与训练

#### datasets — 数据集表

对应原 `datasets/{dataset_name}/dataset_info.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 数据集 ID |
| project_id | INT REFERENCES projects(id) | 所属项目 |
| name | TEXT NOT NULL | 数据集名称（如"person_det_0"） |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### dataset_splits — 数据集划分表

对应原 dataset_info.json 中的 `splits` 字段（变长列表）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 划分 ID |
| dataset_id | INT REFERENCES datasets(id) | 所属数据集 |
| split | TEXT NOT NULL | 划分类型：train / val / test |
| data_clip_id | INT REFERENCES data_clips(id) | 引用的数据批次 |
| annotation_version_id | INT REFERENCES annotation_versions(id) | 引用的标注版本 |
| index_start | INT | 起始索引 |
| index_end | INT | 结束索引 |

```sql
CREATE TABLE dataset_splits (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE CASCADE,
    split TEXT NOT NULL,
    data_clip_id INT REFERENCES data_clips(id),
    annotation_version_id INT REFERENCES annotation_versions(id),
    index_start INT,
    index_end INT
);
```

#### training_runs — 训练任务表

对应原 `models/{model_name}/meta.json`，模型文件本身存对象存储。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 训练任务 ID |
| dataset_id | INT REFERENCES datasets(id) | 使用的数据集 |
| name | TEXT NOT NULL | 模型名称（如"person_det_yolo11n_0"） |
| code_config | TEXT | 代码配置 / commit ID |
| pretrained_model | TEXT | 预训练模型路径或来源 |
| training_config | JSONB | 训练配置（device、batch_size 等） |
| metrics | JSONB | 训练指标（precision、recall、train_time） |
| tags | TEXT[] | 模型标签 |
| status | TEXT DEFAULT 'queued' | 状态：queued / running / completed / failed |
| storage_prefix | TEXT | 对象存储中模型目录的路径前缀 |
| started_at | TIMESTAMP | 开始时间 |
| finished_at | TIMESTAMP | 结束时间 |
| created_at | TIMESTAMP DEFAULT NOW() | 创建时间 |

```sql
CREATE TABLE training_runs (
    id SERIAL PRIMARY KEY,
    dataset_id INT REFERENCES datasets(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    code_config TEXT,
    pretrained_model TEXT,
    training_config JSONB,
    metrics JSONB,
    tags TEXT[],
    status TEXT DEFAULT 'queued',
    storage_prefix TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 三、数据流

### 3.1 上传数据

```
用户上传视频/图片
    │
    ├──▶ MinIO: 存入 {workspace}/{project}/data_clip/{split}/video/ 或 images/
    │
    └──▶ PostgreSQL:
           ├── data_clips 表插入采集元信息
           └── images 表插入每张图片记录（path, 算法去重）
```

### 3.2 标注

```
创建标注版本
    └──▶ PostgreSQL: annotation_versions 表插入版本记录

逐张标注（Web 平台）
    └──▶ PostgreSQL: annotations 表插入/更新标注记录
         图片 URL 从 MinIO 读取展示

自动标注（模型推理）
    ├──▶ 读取 MinIO 图片
    └──▶ PostgreSQL: annotations 表批量插入
```

### 3.3 创建数据集

```
用户选择数据批次 + 标注版本 + train/val/test 划分
    └──▶ PostgreSQL:
           ├── datasets 表插入数据集记录
           └── dataset_splits 表插入划分记录（引用关系，不复制数据）
```

### 3.4 启动训练

```
训练前导出
    ├── 从 PostgreSQL 查 dataset_splits 获取引用关系
    ├── 从 PostgreSQL 查 annotations 获取标注
    ├── 组装成训练格式的cache文件 → 写入 MinIO exports/（可选）
    └── 或训练代码直接读数据库 + MinIO

训练过程
    └──▶ PostgreSQL: training_runs 表更新状态和指标

训练完成
    ├──▶ MinIO: 存入模型权重、配置快照、部署文件
    └──▶ PostgreSQL: training_runs 表更新 metrics、storage_prefix
```

### 3.5 模型推理

```
选择模型 + 目标数据
    ├── 从 MinIO 读取模型权重
    ├── 从 MinIO 读取图片/视频
    ├── 推理结果 → MinIO inference/ 目录（批量文件）
    └── 如果用推理结果作为新的标注版本 → 导入 PostgreSQL annotations 表
```

---

## 四、原有数据到新架构的映射

| 原文件系统 | 新存储位置 | 说明 |
|-----------|-----------|------|
| `projects_A/meta.json` | PostgreSQL `projects` 表 | 项目元信息 |
| `data_clip/{split}/meta.json` | PostgreSQL `data_clips` 表 | 采集元信息 |
| `data_clip/{split}/video/*.mp4` | MinIO `data_clip/{split}/video/` | 不变 |
| `data_clip/{split}/images/**/*.jpg` | MinIO `data_clip/{split}/images/` | 不变 |
| `annotations/{version}/meta.json` | PostgreSQL `annotation_versions` 表 | 标注版本元信息 |
| `annotations/{version}/labels/**/*.json` | PostgreSQL `annotations` 表 | 标注内容 |
| `datasets/{name}/dataset_info.json` | PostgreSQL `datasets` + `dataset_splits` 表 | 数据集定义 |
| `models/{name}/meta.json` | PostgreSQL `training_runs` 表 | 训练记录 |
| `models/{name}/weights/` | MinIO `models/{name}/weights/` | 不变 |
| `models/{name}/deployment/` | MinIO `models/{name}/deployment/` | 不变 |
| `models/{name}/config/` | MinIO `models/{name}/config/` | 不变 |
| `models/{name}/inference/` | MinIO `models/{name}/inference/` | 不变 |

---

## 五、版本链示意（数据库中）

```
annotation_versions 表:

id | data_clip_id | name          | parent_id | method | annotation_type
---|---------------|---------------|-----------|--------|----------------
 1 |             1 | det_sam3_0    |      NULL | sam3   | detection
 2 |             1 | det_manual_1  |         1 | manual | detection
 3 |             1 | det_manual_2  |         2 | manual | detection

版本链: det_sam3_0 → det_manual_1 → det_manual_2
通过 parent_id 追溯
```

---

## 六、权限判断逻辑

```
用户请求访问某个 project 时的权限判断：

1. 用户是否是该 workspace 的 owner？
   → 是：拥有全部权限

2. workspace_permissions 中是否有 project_id IS NULL 的记录？
   → 是：拥有该 workspace 下所有 project 的对应权限

3. workspace_permissions 中是否有匹配 project_id 的记录？
   → 是：拥有该 project 的对应权限

4. 以上都不满足
   → 无权限
```

```sql
-- 查询用户对某个 project 的权限
SELECT permission FROM workspace_permissions
WHERE user_id = :user_id
  AND workspace_id = :workspace_id
  AND (project_id = :project_id OR project_id IS NULL)
ORDER BY
  CASE WHEN project_id IS NOT NULL THEN 0 ELSE 1 END
LIMIT 1;
```

---

## 七、设计要点

| 要点 | 说明 |
|------|------|
| **标注存数据库** | 支持 Web 在线编辑、搜索、筛选、统计，训练前导出 |
| **文件存对象存储** | 图片/视频/模型权重存 MinIO，HTTP 接口访问，目录结构不变 |
| **标注版本链** | annotation_versions 通过 parent_id 形成版本链，可追溯 |
| **数据集是引用** | dataset_splits 只记录引用关系（数据批次 + 标注版本 + 索引范围），不复制数据 |
| **推理结果存文件** | 批量生成的推理结果存对象存储，需要作为标注时再导入数据库 |
| **权限按 project 粒度** | workspace owner 拥有全部权限，其他用户按 project 授权 |
| **三种标注类型统一存储** | annotations 表通过 box / polygon / keypoints 三个 JSONB 字段支持所有类型 |
