# Workflow5 对外接口说明

本文以 `backend/workflow5` 当前实现为准，说明：

- workflow 定义格式；
- Engine 的初始化、单次执行和视频流执行方式；
- 执行状态、正式输出和 debug 输出的读取方式；
- 前端如何获取 block 元数据并生成节点和端口；
- 当前接口中需要服务层补充的部分。

## 1. Python 包入口

业务代码应优先从 `workflow5` 顶层包导入：

```python
from workflow5 import (
    BatchData,
    Classification,
    Detection,
    Engine,
    EngineStatus,
    FlowControl,
    FrameMeta,
    Image,
    ObjectDetection,
    StreamResult,
)
```

`workflow5.__init__` 当前公开以下对象：

| 对象 | 用途 |
| --- | --- |
| `Engine` | 编译和执行 workflow |
| `EngineStatus` | Engine 生命周期状态 |
| `StreamResult` | 视频流最近一次执行结果 |
| `Block` | 自定义 block 基类 |
| `BlockResult` | 单 sample block 输出，即 `dict[str, Any]` |
| `BatchBlockResult` | `BatchData` 的别名 |
| `BatchData` | batch 边界统一数据结构 |
| `Image` | BGR 图像及可选帧元数据 |
| `FrameMeta` | 视频源、帧号和时间戳信息 |
| `Detection` | 单个检测框 |
| `ObjectDetection` | 一张图像上的检测框集合 |
| `Classification` | 分类候选集合 |
| `FlowControl` | 固定命名控制出口的标记类型 |
| `DATA_TYPE` | workflow 类型名到 Python 类型的注册表 |

异常类位于 `workflow5.errors`。应用层通常捕获 `WorkflowError`，并读取：

```python
error.public_message
error.context
error.inner_error
```

`StepExecutionError` 还提供 `step_name` 和 `step_type`。

## 2. Workflow JSON

### 2.1 基本结构

```json
{
  "inputs": [
    {"name": "image", "type": "Image"},
    {"name": "threshold", "type": "float", "default_value": 0.5}
  ],
  "steps": [
    {
      "name": "resize",
      "type": "autopipe/image_resize@v1",
      "parameters": {"width": 640, "height": 640},
      "inputs": {"image": "$inputs.image"}
    }
  ],
  "outputs": [
    {"source": "$steps.resize.width"},
    {"source": "$steps.resize.height"}
  ]
}
```

支持三种 selector：

| 格式 | 用途 |
| --- | --- |
| `$inputs.<name>` | 引用 workflow 输入 |
| `$steps.<name>.<output>` | 引用普通 step 的具名输出 |
| `$steps.<name>` | FlowControl 的 `next_steps` 引用 child step |

正式结果 key 是 output selector 去掉 `$steps.` 后的值。例如
`$steps.resize.width` 对应 `resize.width`。

### 2.2 FlowControl

FlowControl block 的控制出口由 block 类型固定声明，workflow 不能临时增加出口：

```python
ContinueIfBlock.get_output()
# {"passed": "FlowControl", "failed": "FlowControl"}
```

workflow 使用 `next_steps` 将每个固定出口连接到下游：

```json
{
  "name": "gate",
  "type": "autopipe/continue_if@v1",
  "parameters": {"condition_statement": {}},
  "inputs": {
    "count": "$steps.detector.count",
    "min_count": "$inputs.min_count"
  },
  "next_steps": {
    "passed": ["$steps.accepted"],
    "failed": ["$steps.rejected"]
  }
}
```

`next_steps` 的 key 必须与 `get_output()` 声明的出口完全一致。一个出口可以连接零个、一个或
多个 child。普通 step 不能声明 `next_steps`。

### 2.3 Debug block

Debug block 是可选的叶节点：

- 不能作为普通业务 step 的上游；
- 不能连接正式 workflow output；
- 只有启用 debug 后才执行；
- 输出通过 `get_debug_outputs()` 获取。

## 3. Engine 初始化

```python
engine = Engine.init(
    workflow_definition=workflow,
    init_parameters={},
    deepstream_config={},
)
```

完整签名：

```python
Engine.init(
    workflow_definition: dict,
    init_parameters: dict[str, Any] | None = None,
    max_concurrent_steps: int = 1,
    executor: Any = None,
    deepstream_manager_factory: type[DeepStreamManager] = DeepStreamManager,
    deepstream_config: dict[str, Any] | None = None,
) -> Engine
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `workflow_definition` | workflow JSON 反序列化后的字典 |
| `init_parameters` | block 参数的全局缺省值；step 自己的 `parameters` 优先 |
| `deepstream_config` | 视频流执行配置 |
| `deepstream_manager_factory` | DeepStreamManager 类型注入点，生产环境保持默认，测试可传 Fake Manager |
| `max_concurrent_steps` | 为兼容旧接口暂时保留；当前实现不并发调用同一个 block，参数不生效 |
| `executor` | 为兼容旧接口暂时保留；当前实现不使用 |

初始化阶段会完成：

1. 校验 workflow 结构、selector、FlowControl route 和 debug 约束；
2. 每个 step 实例化一个 block；
3. 调用 block 的 `init(parameters)`；
4. 构建执行层和 DeepStream 静态计划。

DeepStream source URI 此时尚未提供，所以 pipeline 在 `run_stream()` 中 build/start。

## 4. 调用方式

### 4.1 单张图像同步执行

```python
from workflow5 import Engine, Image

engine = Engine.init(workflow_definition=workflow)
result = engine.run(
    runtime_parameters={
        "image": Image(image_reference="/data/bus.jpg"),
        "threshold": 0.5,
    }
)

print(result["detector.predictions"])
engine.stop()
```

`run()`：

- 同步返回；
- 每次执行只有一个 sample，block 的 `run(..., index=0)` 中 index 始终为 0；
- 不创建 DeepStream pipeline；
- workflow 中所有未提供且没有 `default_value` 的输入都会报错；
- 同一个处于 `INITIALIZED` 状态的 Engine 可以串行调用多次 `run()`；
- 没有对外公开的 `Engine.run_batch()`，batch 执行属于视频流 worker 的内部能力。

Image 输入支持：

```python
{"image": Image(numpy_image=bgr_array)}
{"image": bgr_array}
{"image": "/data/bus.jpg"}
{"image": {"type": "file", "value": "/data/bus.jpg"}}
{"image": {"type": "base64", "value": jpeg_base64_without_data_url_prefix}}
{"image": {"type": "numpy", "value": bgr_array}}
```

当前 `{"type": "url"}` 最终也调用 OpenCV 本地文件读取，不是 HTTP 下载接口。

### 4.2 单次执行包含多个 Image 输入

`run()` 可以执行包含 front/rear 等多个 Image 输入的单个相机组：

```python
result = engine.run(
    {
        "front": "/data/front.jpg",
        "rear": "/data/rear.jpg",
        "threshold": 0.5,
    }
)
```

这里仍然只有一个 sample，index 为 0。

### 4.3 单个 Image 输入、多路视频

```python
engine = Engine.init(
    workflow_definition=workflow,
    deepstream_config={
        "gpu_id": 0,
        "workflow_interval_ms": 100,
        "max_frame_age_ms": 2000,
        "queue_policy": "drop_oldest",
    },
)

engine.run_stream(
    sources={
        "image": [
            "rtsp://camera-0/stream",
            "rtsp://camera-1/stream",
        ]
    },
    runtime_parameters={"threshold": 0.5},
)
```

列表位置就是稳定的 `batch_index/source_id`：

```text
image[0] -> batch_index 0
image[1] -> batch_index 1
```

`run_stream()` 启动 DeepStream pipeline 和后台 workflow worker，然后立即返回 Engine，本身不等待
视频结束。

### 4.4 多组 Image 输入、多路视频

```python
engine.run_stream(
    sources={
        "front": [
            "rtsp://front-0/stream",
            "rtsp://front-1/stream",
        ],
        "rear": [
            "rtsp://rear-0/stream",
            "rtsp://rear-1/stream",
        ],
    },
    runtime_parameters={"threshold": 0.5},
)
```

配对关系是列表位置，不是输入名称：

```text
batch_index 0 = {front: front[0], rear: rear[0]}
batch_index 1 = {front: front[1], rear: rear[1]}
```

约束和执行语义：

- `sources` 必须包含 workflow 声明的全部 Image 输入，不能包含未知名称；
- 每个值必须是非空 URI list；
- 所有 Image 输入的 URI list 长度必须相同；
- 一组内必须完整；某个 index 缺少任意 Image 输入时，该 index 本轮不执行；
- 同一 Image 输入路径上的 image/detection 等 DeepStream boundary 严格按同一帧对齐；
- front/rear 等不同 Image 输入之间采用各自最新可用帧，不要求 frame number 或 PTS 相同；
- 最新帧超过 `max_frame_age_ms` 后视为不可用；
- 本地视频路径可直接传入，Manager 会转换为 file URI。

### 4.5 Debug 开关

debug 默认关闭，可以在启动前或视频流运行期间切换：

```python
engine.enable_debug_blocks()
engine.run_stream(sources)

debug_outputs = engine.get_debug_outputs()

engine.disable_debug_blocks()
```

单次 `run()` 也使用同一个开关：

```python
engine.enable_debug_blocks()
result = engine.run({"image": "/data/bus.jpg"})
debug_outputs = engine.get_debug_outputs()
```

## 5. 视频流结果和生命周期

### 5.1 获取最近结果

```python
latest = engine.get_latest_output()

if latest is not None:
    print(latest.execution_batch_id)
    print(latest.updated_at)
    print(latest.outputs)
```

返回值为 `StreamResult | None`：

```python
@dataclass(frozen=True)
class StreamResult:
    execution_batch_id: int
    updated_at: float
    outputs: dict[str, list[Any]]
```

- 尚未成功执行过一轮时返回 `None`；
- 只保留最新快照，不保存历史队列；
- `sequence` 和 `batch_id` 是 `execution_batch_id` 的兼容别名；
- `outputs` 每个字段的 list 顺序与本轮参与执行的升序 batch index 一致；
- FlowControl 终止某个正式输出的路径时，该 index 对应位置为 `None`。

例如：

```python
StreamResult(
    execution_batch_id=12,
    updated_at=...,
    outputs={
        "detector.count": [2, 1],
        "csv.csv": ["...", None],
    },
)
```

注意：当前 `StreamResult` 没有公开本轮实际的 batch index 列表。当本轮完整组是稀疏集合（例如只有
index 1 可用）时，调用者只能拿到一个紧凑 list，不能从返回值中严格恢复它原来是 index 1。这是
当前公开接口的缺口；若前端需要将结果可靠地回填到具体相机组，建议后续给 `StreamResult` 增加
`indices: tuple[int, ...]`，不要直接把 list 下标当作 source_id。

### 5.2 获取 debug 输出

```python
debug = engine.get_debug_outputs()
# dict[debug_step_name, BatchData]

visualised = debug["visualise"]
item_0 = visualised.get_by_index(0)
image = item_0["image"]
```

debug 输出和正式输出分别保存。关闭 debug 后，相关 step 不再执行。

### 5.3 状态、失败和停止

```python
status = engine.status
failure = engine.failure
engine.stop(timeout=10.0)
```

状态：

```text
INITIALIZED
  -> STREAM_STARTING
  -> STREAM_RUNNING
  -> STOPPING
  -> STOPPED

启动或后台执行异常 -> FAILED
```

- `stop()` 会停止 worker、DeepStream pipeline 并调用所有 block 的 `close()`；
- `stop()` 可以重复调用；
- `STOPPED` 或 `FAILED` 的 Engine 不支持重新启动，需要重新 `Engine.init()`；
- stream 后台异常不会从已经返回的 `run_stream()` 再次抛给调用线程，应检查
  `engine.status` 和 `engine.failure`。

## 6. DeepStream 配置

当前代码实际读取的主要配置：

| 字段 | 默认值 | 说明 |
| --- | ---: | --- |
| `gpu_id` | `0` | 对当前进程可见 GPU 中的设备编号 |
| `mux_width` | `1920` | nvstreammux 输出宽度 |
| `mux_height` | `1080` | nvstreammux 输出高度 |
| `workflow_interval_ms` | `0` | 两轮 workflow 的最小间隔 |
| `max_frame_age_ms` | `2000` | 最新帧允许复用的最大时间 |
| `drop_frame_interval` | `0` | source 解码丢帧间隔 |
| `num_extra_surfaces` | `1` | decoder 额外 surface 数量 |
| `queue_policy` | 自动 | `block` 或 `drop_oldest`；RTSP 默认 drop_oldest，本地文件默认 block |
| `nvbuf_memory_type` | `3` | DeepStream buffer memory type |

在容器外通过 `CUDA_VISIBLE_DEVICES=7` 只暴露物理 GPU7 时，容器/进程内部通常仍使用
`gpu_id=0`。

## 7. 前端获取 block 信息

### 7.1 当前现状

workflow5 的 block 注册入口是：

```python
from workflow5.block_library.loader import load_blocks

block_classes = load_blocks()
```

每个类通过以下接口提供静态信息：

```python
block_class.type
block_class.get_input()
block_class.get_parameter()
block_class.get_output()
block_class.controls_flow()
block_class.accepts_empty_values()
block_class.is_deepstream_supported()
```

以下能力当前是实例方法：

```python
block.is_batch_supported()
block.is_debug()
```

前端不应直接加载 Python 类，应由后端把注册表序列化为 JSON。

项目已有：

```http
GET /api/workflow-blocks
```

但 `backend/routers/workflows.py` 当前导入的是
`workflow2.block_library.loader.load_blocks`，因此这个接口返回的是 workflow2 block，而不是
workflow5 block。`POST /api/workflows/run` 当前也由 workflow2 的 preview service 执行。

所以，**workflow5 Python Engine 已实现，但 workflow5 的前端 HTTP 接入尚未完成**。前端不能把
当前 `/api/workflow-blocks` 的返回值当作 workflow5 能力描述。

### 7.2 建议的 workflow5 block 元数据响应

服务层应从 workflow5 的 `load_blocks()` 构造以下结构：

```json
{
  "type": "autopipe/yolo_detection@v1",
  "category": "models",
  "inputs": {"image": "Image"},
  "parameters": {
    "model_path": "string",
    "engine_path": "string",
    "labels_path": "string",
    "imgsz": "int",
    "confidence": "float",
    "iou": "float",
    "device": "any",
    "max_batch_size": "int"
  },
  "outputs": {"predictions": "ObjectDetection"},
  "controls_flow": false,
  "accepts_empty": false,
  "supports_batch": true,
  "supports_deepstream": true,
  "is_debug": false,
  "dynamic_inputs": false
}
```

后端序列化逻辑可以是：

```python
from workflow5.block_library.loader import load_blocks


def workflow5_block_specs() -> list[dict]:
    specs = []
    for cls in load_blocks():
        instance = cls()  # 只读取能力，不调用 init()
        parts = cls.__module__.split(".")
        specs.append(
            {
                "type": cls.type,
                "category": parts[-2] if len(parts) >= 2 else "misc",
                "inputs": cls.get_input(),
                "parameters": cls.get_parameter(),
                "outputs": cls.get_output(),
                "controls_flow": cls.controls_flow(),
                "accepts_empty": cls.accepts_empty_values(),
                "supports_batch": instance.is_batch_supported(),
                "supports_deepstream": cls.is_deepstream_supported(),
                "is_debug": instance.is_debug(),
                "dynamic_inputs": cls.type in {
                    "autopipe/expression@v1",
                    "autopipe/continue_if@v1",
                },
            }
        )
    return specs
```

`dynamic_inputs` 当前不是 Block 基类方法，只能由服务层补充或以后增加正式类方法。
`get_input() == {}` 在现有 block 中表示动态命名输入，但单凭空字典无法区分“动态输入”和“无输入
block”，因此建议响应显式提供这个字段。

### 7.3 前端如何使用元数据

前端节点编辑器按以下规则使用响应：

1. `type` 保存到 workflow step 的 `type`。
2. `category` 用于 block 组件库分组。
3. `inputs` 生成左侧数据输入端口，并按类型限制可连接输出。
4. `parameters` 生成基础参数表单；复杂参数如 `condition_statement` 仍需要专用编辑器。
5. 普通 `outputs` 生成右侧数据输出端口。
6. `controls_flow=true` 时，类型为 `FlowControl` 的每个 output 是一个固定命名控制端口。
7. 控制端口连接关系写入该 step 的 `next_steps[route_name]`，不写入 child 的 `inputs`。
8. `is_debug=true` 的节点只能作为叶节点，不能连接业务下游或正式 output。
9. `supports_deepstream` 和 `supports_batch` 用于能力提示，不用于前端自行决定执行计划；最终计划由
   Engine 根据整张图计算。

ContinueIf 的前端表示：

```text
ContinueIf
├─ passed  -> next_steps.passed
└─ failed  -> next_steps.failed
```

对应 JSON：

```json
{
  "name": "gate",
  "type": "autopipe/continue_if@v1",
  "inputs": {
    "count": "$steps.detector.count"
  },
  "parameters": {
    "condition_statement": {}
  },
  "next_steps": {
    "passed": ["$steps.branch_a"],
    "failed": ["$steps.branch_b"]
  }
}
```

### 7.4 当前注册 block

| type | 分类 | 输入 | 输出 | Batch | DeepStream | Debug |
| --- | --- | --- | --- | --- | --- | --- |
| `autopipe/image_crop@v1` | transformations | `image` | `crop` | 否 | 是 | 否 |
| `autopipe/image_resize@v1` | transformations | `image` | `resized,width,height` | 否 | 是 | 否 |
| `autopipe/image_properties@v1` | classical_cv | `image` | `width,height,brightness,properties` | 否 | 否 | 否 |
| `autopipe/color_threshold_detector@v1` | classical_cv | `image` | `predictions,count` | 否 | 否 | 否 |
| `autopipe/brightness_classifier@v1` | models | `image` | `top,confidence,predictions` | 否 | 否 | 否 |
| `autopipe/yolo_detection@v1` | models | `image` | `predictions` | 是 | 是 | 否 |
| `autopipe/detections_filter@v1` | fusion | `predictions` | `predictions,count` | 否 | 否 | 否 |
| `autopipe/exclusive_merge@v1` | fusion | `a,b` | `value` | 否 | 否 | 否 |
| `autopipe/detections_count@v1` | analytics | `predictions` | `count,count_by_class,total_area` | 否 | 否 | 否 |
| `autopipe/expression@v1` | math | 动态 | `result` | 否 | 否 | 否 |
| `autopipe/property_definition@v1` | formatters | `data` | `output` | 否 | 否 | 否 |
| `autopipe/csv_formatter@v1` | formatters | `rows` | `csv,row_count` | 否 | 否 | 否 |
| `autopipe/continue_if@v1` | flow_control | 动态 | `passed,failed` | 是 | 否 | 否 |
| `autopipe/detection_vis@v1` | debug | `image,predictions` | `image` | 否 | 否 | 是 |

## 8. 前端/HTTP 层的数据序列化

Engine 返回的是 Python 领域对象，不保证可以直接交给 FastAPI JSON encoder：

- `ObjectDetection`：调用 `to_dicts()`，必要时另外返回 image size、model name 和 frame meta；
- `Detection`：调用 `to_dict()`；
- `Classification`：序列化其 `items`；
- `Image`：按接口需求编码为 JPEG/base64 或保存文件后返回 URL；
- `BatchData`：先调用 `to_dict()`，再递归序列化其中的领域对象；
- `EngineStatus`：使用 `.value`；
- `WorkflowError`：输出 `public_message/context/step_name/step_type` 等公开字段。

不要把 numpy 数组、PyServiceMaker Buffer、TensorRT 对象或 block 实例直接返回给前端。

## 9. 建议补充的服务接口

为了让前端完整使用 workflow5，建议服务层后续提供：

```text
GET    /api/workflow5/blocks
POST   /api/workflow5/run
POST   /api/workflow5/streams
GET    /api/workflow5/streams/{id}
GET    /api/workflow5/streams/{id}/debug
POST   /api/workflow5/streams/{id}/debug/enable
POST   /api/workflow5/streams/{id}/debug/disable
DELETE /api/workflow5/streams/{id}
```

其中 stream Engine 必须由服务端按 id 持有，停止时调用 `engine.stop()`。这些 HTTP 路由当前尚未在
workflow5 中实现；本节是对现有 Python API 的服务化映射建议，不代表现有可调用接口。
