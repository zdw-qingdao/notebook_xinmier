# 全系列相机 AI 算法服务化与端侧推理 Block 重构实施说明

> 文档定位：AI 专项架构与分期实施设计<br>
> 当前状态：设计冻结，尚未声称源码重构已落地<br>
> 适用范围：AR 系列和 D 系列两套代码树的正式产品型号、共享 Web UI 及外部算法与相机管理平台<br>
> 首个实施样板：D950 `safety-double-rk3588/cam/aiobjdect/aiobjdect2.cpp`<br>
> 部署边界：C++ 算法管线仍同进程、静态链接，不使用动态 `.so` 插件，也不接受平台下发的任意 DAG；DE-2 起，获准的外部应用逻辑才允许以独立 Python 进程（`blockd`）运行在相机内，通过公开消息调用服务层，详见 [DeepEdge 渐进式 DAG 适配与三阶段实施说明](./全系列相机_DeepEdge渐进式DAG适配与三阶段实施说明.md)

配套文档：

- [全系列相机接口治理、用户组权限与平台化改造实施说明](./全系列相机_模块化重构方案审核与实施说明.md)
- [全系列相机功能模块定义与外部平台 Block 对接说明](./全系列相机_Block模块定义与划分说明.md)
- 全系列相机用户组、API Key 与安全规划（独立文档，当前工作区未提供，进入权限实施前需恢复或重新编制）
- [全系列相机 DeepEdge 渐进式 DAG 适配与三阶段实施说明](./全系列相机_DeepEdge渐进式DAG适配与三阶段实施说明.md)

---

## 1. 结论和不可破坏的边界

本次不是把 `aiobjdect2.cpp` 机械分成多个 `.cpp`，而是把当前同时存在的五种职责分成稳定契约：

1. **HAL / 驱动**：获取帧、图像加速、端侧推理、GPIO/PWM/MCU 和板级资源；Rockchip、NVIDIA、Qualcomm 等厂商 SDK 只能出现在各自 HAL 实现中。
2. **C++ 算法 Block**：预处理编排、推理阶段调用、模型解码、ROI 标注、跟踪、深度验证和结果组装；真正执行推理的厂商 backend 属于 HAL。
3. **AI 服务层**：管理管线会话、配置、资源、健康、结果总线和订阅背压。
4. **相机应用层**：多帧业务判断、禁止消失、报警分类、GPO/LED、录像、抓拍、Operator、客户日志和兼容输出。
5. **外部平台应用层**：Python Block、客户规则、状态机、跨设备编排和第三方集成。

目标调用方向只能向下：

```text
外部平台应用层
  Python Block / 业务规则 / 跨设备编排
                         │ Action / Event
                         ▼
协议与服务入口
  HTTPS / WSS / MQTT / Auth / PolicyGate / Audit
                         │
                         ▼
相机 AI 服务层
  Session / Config / Result Bus / Health / Resource
                         │
                         ▼
C++ 算法 Block 层
  Preprocess / Infer / Decode / ROI / Track / Depth / Assemble
                         │
                         ▼
HAL / 驱动层
  Frame / Image Accelerator / Inference Backend / Device SDK
```

图中的 `Infer` 是管线中的强类型调用阶段，不表示厂商推理实现属于 `blocks/`；实际执行由注入的 `hal/inference/api/IInferenceBackend` 完成。

禁止反向依赖：

- 算法 Block 不能 include HTTP、WSS、MQTT、UI、GPO、录像或抓拍实现。
- 推理 backend 不能接收 `SenderPtr`、`AiFinalResult`或项目业务任务。
- 相机应用、服务和算法语义 Block 不能直接调用 RKNN、TensorRT、QNN、RGA、CUDA 或其他芯片 SDK。
- 外部平台 Block 不能依赖相机内 major/minor、线程、寄存器、SoC 或驱动对象。
- 型号、SoC、端口和发行包名不能出现在 Block ID、Action ID 或 Event ID 中。

---

## 2. 现状盘点与根因

### 2.1 D950 `aiobjdect` 目录当前包含的模块

| 当前职责 | 主要文件 / 位置 | 目标归属 |
|---|---|---|
| AI 生命周期、线程、队列、整体编排 | `aiobjdect2.cpp` / `aiobjdect2.h` | AI 服务层 |
| 配置、任务、检测结果、最终结果 | `aiobjdectconfig.h` / `aiobjdectdef.h` / `detectorbase.h` | 分拆为领域类型和四类配置 |
| 帧拷贝、stride、padding、RGB/BGR、resize | `stepPre()` / `image_utils.c` | Preprocess Block + HAL Adapter |
| RKNN context 和请求调度 | `rknn_inspector.*` / `rknn_scheduler.*` | `hal/inference/rockchip` 实现 |
| YOLO/PP-YOLOE/Seg 后处理 | `postprocess.*` | 独立 Model Decoder Block |
| 检测坐标、类别、ROI 归一化 | `stepPost1GetResult()` | Normalize + ROI Block |
| 多帧阈值和最终布尔值 | `stepPost2Estimate()` | LocalAiApplication |
| 跟踪、Kalman、LAPJV、IOU/马氏距离 | `stepPost3MakeUiMsg()` / `STrack.*` / `kalmanFilter.*` / `lapjv.*` | Tracker Block |
| 深度估计和立体性复核 | `depth_inspector.*` 及 `aiobjdect2.cpp` 的验证函数 | Depth Backend + Depth Verifier Block |
| GPO、LED、failsafe、报警类别 | `stepPost3MakeGpoEvent()` | LocalAiApplication + Safety Service |
| 录像、抓拍、Operator Trigger | `stepPost3MakeInnerSignal()` | LocalAiApplication |
| ETH、SDK、SVAP/MQTT 报文 | `stepPost3MakeCommMsg()` | Transport Adapter / Legacy Adapter |
| UI 文字、框、ROI、Mask、马赛克 | `stepPost3MakeUiMsg()` 及 Manager 单例 | Diagnostic Overlay Sink |
| DeepEdge 低置信度和 regular 样本 | 异步存图函数 | Diagnostic Sample Store |
| PoseGuard / MonumentGuard | `siftWorker()` / `checkCam()` | 独立 Safety Service |

### 2.2 最主要的结构问题

1. `ObjectDectImpl` 同时拥有资源、线程、算法、配置、业务状态和协议输出，任何局部改动都可能改变整体生命周期。
2. `stepPost3MakeUiMsg()` 的名称是 UI 输出，实际却包含完整跟踪、匹配、深度状态和部分报警处理。
3. `AiFinalResult` 与 `AiOutputMessaage` 既是业务结果，又直接携带 GPO、Trigger、UI 和通信报文。
4. `DetectionOutput` 知道如何构造对外 JSON，导致算法领域类型依赖协议、固定帧尺寸和配置。
5. `detectorbase.h`、`aiobjdect2.h` 和 `rknn_scheduler.h` 存在双向 include，上下层边界已经失效。
6. `PostProcessor` 通过静态可变字段保存类别数、标签、anchor、阈值和模式，多模型实例会有相互覆盖风险。
7. `aiobjdectpolicy.cpp` 和 `ObjectDectImpl::stepPost*()` 保留两套近似策略，老新路径难以证明等价。
8. D950 和 AR 仓同名目录已明显漂移；简单复制新代码会继续放大差异。

### 2.3 重构不得改变的现有行为

- 现有本地完整 AI 方案的配置、启停、报警、GPO、LED、录像、抓拍、UI 和旧协议语义保持不变。
- 现有“异步推流检测”方案及 SVAP 上报继续使用原有契约，本轮不强行并入新方案。
- 现有 `ObjectDect` 公共类作为兼容 façade 保留，`Project`、模型评估和回放路径不一次性改写。
- 回放 `generation`、`captureFrameId`、时间戳和迟到结果丢弃规则保留。
- 安全监测、看门狗、硬件互锁、启动/升级/恢复不依赖外部平台。

---

## 3. 目标模块和目录

### 3.1 第一阶段公共目录

D950 首先落地下列结构；通过阶段验收后，公共文件按相同相对路径镜像到 AR 仓：

```text
cam/ai/
├── core/
│   ├── block.h
│   ├── block_descriptor.h
│   └── component_health.h
├── domain/
│   ├── ai_error.h
│   ├── frame_view.h
│   ├── model_input.h
│   ├── tensor_bundle.h
│   ├── detection.h
│   ├── annotations.h
│   └── inference_result_event.h
├── blocks/
│   ├── block_registry.h/.cpp
│   ├── preprocess/
│   ├── decoders/
│   ├── roi/
│   ├── tracking/
│   ├── depth/
│   └── assemble/
├── hal/
│   ├── inference/
│   │   ├── api/
│   │   │   ├── inference_backend.h
│   │   │   ├── inference_capability.h
│   │   │   └── tensor_memory.h
│   │   ├── rockchip/
│   │   │   ├── rknn_backend.h/.cpp
│   │   │   └── rknn_context_pool.h/.cpp
│   │   ├── nvidia/
│   │   │   └── tensorrt_backend.h/.cpp
│   │   ├── qualcomm/
│   │   │   └── qnn_backend.h/.cpp
│   │   └── mock/
│   ├── image/
│   │   ├── api/
│   │   ├── rockchip/
│   │   ├── nvidia/
│   │   └── qualcomm/
│   └── frame/
│       ├── api/
│       ├── rockchip/
│       ├── nvidia/
│       └── qualcomm/
├── service/
│   ├── ai_inference_service.h/.cpp
│   ├── ai_pipeline_session.h/.cpp
│   ├── inference_result_bus.h/.cpp
│   ├── ai_resource_coordinator.h/.cpp
│   └── ai_health.h
├── application/
│   ├── local_ai_application.h/.cpp
│   ├── temporal_alarm_policy.h/.cpp
│   ├── disappearance_policy.h/.cpp
│   └── local_action_router.h/.cpp
├── adapters/
│   ├── frame_source/
│   ├── overlay/
│   ├── transport/
│   ├── legacy/
│   └── product/
└── tests/
```

`hal/inference/` 是端侧推理 HAL 的唯一落点，不能再把厂商推理代码放回 `blocks/`、`service/`、`adapters/product/` 或 `aiobjdect2.cpp`。其边界如下：

- `hal/inference/api/` 只定义芯片无关接口、能力、tensor 描述和所有权协议，不 include 任何厂商头文件。
- `rockchip/`、`nvidia/`、`qualcomm/` 分别封装 RKNN、TensorRT 和 QNN 等厂商运行时；具体采用哪个厂商 SDK 由对应产品实现和验收决定，公共契约不以 SDK 名命名。
- `mock/` 用保存的 tensor 和故障注入支持服务层、管线和合同测试，不要求开发机安装任何 NPU SDK。
- `hal/image/` 隔离 RGA、CUDA/NPP、Qualcomm 图像加速等预处理实现；`hal/frame/` 隔离厂商媒体缓冲、零拷贝句柄和同步原语。
- `blocks/` 只保存芯片无关的算法语义和固定管线阶段。decoder、ROI、Tracker 和 Result Assembler 不属于 HAL。
- `adapters/product/` 只负责 ProductProfile 到 HAL factory/capability 的装配，不实现推理，不包含厂商 context。

第一阶段仍是静态链接：每个产品构建只编入获准的 HAL 实现。运行时选择只能在编入固件且经 ProductProfile 公布的实现之间进行，不扫描目录、不加载动态 `.so`，也不允许配置传入任意实现类名。

### 3.2 HAL 推理接口与依赖规则

`IInferenceBackend` 的声明放在 `hal/inference/api/inference_backend.h`，厂商实现可继承 `core/block.h` 中的统一 `IBlock` 生命周期，但其源文件不因此进入算法 Block 目录。`core/` 只含生命周期和健康契约，不依赖 `blocks/` 或任一厂商 HAL，因此不会造成 HAL 对上层算法目录的反向依赖。接口至少覆盖：

```cpp
class IInferenceBackend : public IBlock {
public:
    // 返回芯片无关的模型格式、数据类型、并发和加速器能力。
    virtual const InferenceCapability& capability() const = 0;

    // 加载并验证模型；模型句柄和厂商 context 仅由 backend 持有。
    virtual AiResult<void> loadModel(const ModelArtifact& model) = 0;

    // 执行推理；输出所有权通过 TensorBundle 返回，不泄露厂商对象。
    virtual AiResult<TensorBundle> infer(const ModelInput& input) = 0;
};
```

必须满足以下依赖方向：

```text
Pipeline / Service → hal/inference/api ← Vendor HAL Implementation
Decoder            → domain tensor descriptors
Vendor HAL         → Vendor SDK
HAL / Blocks        → core lifecycle contracts
```

- `TensorBundle` 可以在内部持有类型擦除的释放器，但公共头文件不得出现 `rknn_context`、TensorRT/CUDA 对象、QNN handle 或厂商枚举。
- 坐标变换、模型类别、anchor、NMS、Mask 语义属于 Preprocess/Decoder，不得下沉到厂商推理 HAL。
- 通用排队、公平性、取消和会话配额属于 `AiResourceCoordinator`；只与 context 创建、厂商 stream 或 device memory 绑定的资源池留在具体 HAL。
- HAL 错误先映射为统一 `AiError`，同时保留仅用于诊断的 `vendor/domain/code`，上层不能依赖厂商错误码做业务分支。
- ProductProfile 用稳定能力选择 factory，例如模型格式、精度、零拷贝和最大并发；不得通过 `#ifdef RK3588` 在公共算法源码中选择实现。

### 3.3 模块所有权

| 模块 | 不可变输入 | 输出 | 可持有状态 |
|---|---|---|---|
| FrameSourceAdapter | HAL 帧 | `FrameView` | 订阅句柄、丢帧计数 |
| Preprocessor | `FrameView` | `ModelInput` | 缓冲池、坐标变换配置 |
| InferenceBackend | `ModelInput` | `TensorBundle` | 模型上下文、加速器资源 |
| ModelDecoder | `TensorBundle` | `DetectionFrame` | 模型元数据、anchor、阈值、标签 |
| RoiAnnotator | `DetectionFrame` | ROI annotations | ROI 配置快照 |
| Tracker | `DetectionFrame` | tracking annotations | tracklet、Kalman、匹配参数 |
| DepthVerifier | detection + tracking + depth frame | depth annotations | 深度缓存和时效性 |
| ResultAssembler | 上述结果 | `InferenceResultEvent` | 会话 sequence |
| LocalAiApplication | `InferenceResultEvent` | 本地业务动作 | 多帧判断、报警边沿和去抖 |
| ExternalEventAdapter | `InferenceResultEvent` | WSS/MQTT Event | 订阅限频和丢弃计数 |

---

## 4. C++ Block 模型

### 4.1 Block 不是任意图节点

相机内 Block 是可独立配置、启停、测试和替换的强类型 C++ 算法阶段。它与平台 Python Block 共享“稳定契约和可组合”目标，但不共享运行时：

- 相机 C++ Block 在编译时强类型，由信任的固定管线模板组装。
- 平台 Python Block 在平台侧编排；DE-1 在平台运行，DE-2 起获准执行体才可下发到相机内独立的 `blockd` 进程。它通过公开消息消费结构化结果并调用服务层，不进入 C++ 管线，也不参与逐帧图像处理。
- 不允许方案 JSON 指定任意类名、库路径或未注册的 Block 连接。

AI 专项只维护私有 `AlgorithmBlockRegistry`。DeepEdge DE-3 使用的公开 `ApplicationNodeCatalog`、Graph Validator/Compiler/Executor、自动 IPC Bridge 和 Python 包均由通用模块化/DeepEdge 适配负责人维护；外部图把整个 AI 会话视为原子服务节点，不直接 include 或连接本节的内部 Block。

### 4.2 公共生命周期

```cpp
struct BlockDescriptor {
    std::string blockId;          // 稳定的芯片无关 ID。
    std::string implementationId; // 实现和平台适配标识。
    std::string version;
    std::vector<std::string> requiredCapabilities;
};

class IBlock {
public:
    virtual ~IBlock() = default;

    // 返回 Block 身份、实现版本和能力依赖。
    virtual const BlockDescriptor& descriptor() const = 0;

    // 在 STOPPED 状态下验证并应用配置，失败不得留下部分状态。
    virtual AiResult<void> configure(const Json::Value& config) = 0;

    // 申请资源并进入 RUNNING；重复启动返回 CONFLICT。
    virtual AiResult<void> start() = 0;

    // 停止接收新输入、有界等待在途任务并释放资源。
    virtual AiResult<void> stop() = 0;

    // 返回状态、错误、队列、延迟和丢弃计数，不执行昂贵操作。
    virtual BlockHealth health() const = 0;
};
```

`IBlock` 不提供无类型 `process(void*)`。各阶段通过派生接口提供强类型输入输出，例如：

```cpp
class IFramePreprocessor : public IBlock {
public:
    // 将不可变源帧转为模型输入，并保留逆坐标变换。
    virtual AiResult<ModelInput> process(const FrameView& frame) = 0;
};

class IModelDecoder : public IBlock {
public:
    // 将模型私有 tensor 转为统一的检测坐标和类别。
    virtual AiResult<DetectionFrame> decode(
        const TensorBundle& tensors,
        const CoordinateTransform& transform) = 0;
};
```

### 4.3 Block Registry 和固定管线

Registry 注册内容至少包含：

```text
blockId
implementationId
version
stageType
inputContract
outputContract
requiredCapabilities
supportedModelVersions
factory
```

首批只注册 `ObjectDetectionPipeline`：

```text
FrameSource
→ Preprocess
→ Inference Backend
→ Model Decoder
→ Detection Normalize
→ [ROI Annotator]
→ [Tracker]
→ [Depth Verifier]
→ Result Assembler
```

方案只能选择模板和模板已声明的可选 Block。启动顺序由下游到上游，确保首帧到来前消费者已就绪；失败时按已启动顺序的反序停止。

### 4.4 统一错误

```text
INVALID_CONFIG
NOT_SUPPORTED
RESOURCE_BUSY
MODEL_LOAD_FAILED
MODEL_CONTRACT_MISMATCH
PREPROCESS_FAILED
INFERENCE_FAILED
DECODE_FAILED
INPUT_STALE
CANCELLED
TIMEOUT
INTERNAL_ERROR
```

Block 错误可附带 `blockId/implementationId/sessionId/captureFrameId/retryable/detail`，但不对外泄露路径、凭据、驱动指针或未脱敏日志。

---

## 5. 公共数据契约和内存所有权

### 5.1 `FrameView`

`FrameView` 是只读视图，必须持有能保证帧内存生命周期的共享 owner，不允许像现有 `DetectorInData` 一样在领域对象析构时直接 `free()` 外部缓冲。

```text
owner
data / planeOffsets
dataLength
pixelFormat
width / height / strides
pts
monotonicTimeMs
captureFrameId
generation
sourceId
```

### 5.2 `ModelInput` 和坐标变换

`ModelInput` 记录：

- 模型输入格式、宽高、stride 和共享缓冲所有权。
- resize 比例、letterbox padding、crop 和源帧尺寸。
- 模型坐标返回源帧标准化坐标的唯一逆变换。

后处理、ROI、Mask、跟踪和对外契约不得各自重复假设 `640x640`、`1280x720` 或固定 padding。

### 5.3 `TensorBundle`

- 只能由创建它的 backend 释放。
- 保存 tensor name/index、dtype、layout、shape、quantization 和 buffer view。
- decoder 不得直接调用 `rknn_outputs_release`。
- 移动可用、禁止拷贝，避免同一输出被重复释放。

### 5.4 `DetectionFrame`

```text
modelIdentity
captureFrameId / generation
capturedAt / monotonicTime
sourceGeometry / modelGeometry
preprocessLatencyMs / inferenceLatencyMs / decodeLatencyMs
detections[]
```

每个 `Detection` 包含：

```text
detectionId
classId / className
confidence
bboxNormalized {left, top, width, height}
bboxPixels {left, top, width, height}
contourNormalized[]              # 可选简化轮廓
maskSummary {areaRatio, checksum} # 可选
```

`Detection` 不包含“安全/警告”、GPO 事件、录像动作或协议 JSON。

### 5.5 分析注解

分析 Block 不修改原始 Detection，通过索引或 `detectionId` 追加：

```text
RoiAnnotation       {detectionId, roiIds, strategy}
TrackingAnnotation  {detectionId, trackId, state, ageFrames, lostFrames}
DepthVerification   {detectionId, status, residual, dataAgeMs, fallbackUsed}
```

Depth `status` 表达算法证据，不表达最终报警：

```text
NOT_REQUESTED / PENDING / VERIFIED_3D / REJECTED_PLANE / STALE / UNAVAILABLE
```

---

## 6. AI 服务层

### 6.1 会话接口

```cpp
class IAiInferenceService {
public:
    virtual ~IAiInferenceService() = default;

    // 验证管线模板、ProductProfile、capability 和资源后创建 STOPPED 会话。
    virtual AiResult<AiPipelineSessionPtr> createSession(
        const PipelineSpec& specification) = 0;

    // 仅在安全点交换模型或分析配置，失败保留原会话。
    virtual AiResult<void> reconfigureSession(
        const std::string& sessionId,
        const PipelineSpec& specification) = 0;

    // 查询会话、Block、队列、NPU 和延迟健康快照。
    virtual AiResult<AiServiceHealth> health() const = 0;
};

class AiPipelineSession {
public:
    // 注册完结果消费者后启动下游 Block 和帧源。
    virtual AiResult<void> start() = 0;

    // 停止新帧、取消或有界排空在途任务，然后释放资源。
    virtual AiResult<void> stop() = 0;

    // 返回会话 ID、runId、状态、配置版本和运行计数。
    virtual AiPipelineStatus status() const = 0;
};
```

会话状态机：

```text
CREATED → STARTING → RUNNING → STOPPING → STOPPED
                    └──→ FAILED
```

- `STARTING` 中任一 Block 失败，必须反向回滚并进入 `FAILED`。
- `RUNNING` 时非可恢复 backend 错误使会话进入 `FAILED`，不在工作线程内无限重试。
- `stop()` 必须幂等；已停止会话再次停止返回成功并标识 `alreadyStopped`。

### 6.2 结果总线

```cpp
class IInferenceResultSubscriber {
public:
    virtual ~IInferenceResultSubscriber() = default;

    // 消费不可变结果；实现不得阻塞推理发布线程。
    virtual void onInferenceResult(
        std::shared_ptr<const InferenceResultEvent> event) = 0;

    // 消费会话启停、降级、错误和恢复状态。
    virtual void onInferenceState(const InferenceStateEvent& event) = 0;
};
```

每个订阅者拥有自己的有界队列、限频和计数，不共享一个网络发送队列。默认策略：

| 消费者 | 默认队列 | 满队列策略 | 是否反压推理 |
|---|---:|---|---|
| LocalAiApplication | 2 | 丢旧保新，记录连续性中断 | 否 |
| DiagnosticOverlay | 1 | 仅保留最新 | 否 |
| WSS subscriber | 2 | 丢旧保新 | 否 |
| MQTT bridge | 2 | 丢旧保新 | 否 |
| Evaluation observer | 可配置，默认 1 | 评测模式由帧源串行控制 | 仅评测会话 |

本地多帧策略若收到 sequence 间隔，不得把丢失帧当成 false 帧；应重置需要连续帧的去抖计数，并增加 continuity reset 指标。

### 6.3 安全重配

会话重配采用“新配置预验证 → 资源预检 → 停止旧帧源 → 交换 runId → 启动新管线”：

- 预验证失败不停止旧管线。
- 开始交换后不再向旧管线提交帧。
- 旧 runId/generation 的迟到结果丢弃并计数。
- 新管线启动失败时，只在旧资源仍完整可恢复时回滚；否则进入 FAILED 并报明确错误。

---

## 7. 算法 Block 与推理 HAL 详细边界

### 7.1 Preprocess Block

职责：

- 验证像素格式、尺寸、stride 和 buffer 长度。
- 执行 crop、resize、letterbox、通道转换和必要的量化输入准备。
- 生成唯一 `CoordinateTransform`。
- 可以选择 CPU 或 HAL 加速实现，但对上层契约相同。

不负责：ROI、跟踪、报警、保存图片或协议发送。

### 7.2 Inference HAL Backend

职责：

- 加载并验证模型 I/O contract。
- 按 `AiResourceCoordinator` 分配的设备、核心和并发限额创建厂商 context。
- 执行输入提交、推理、输出获取和 RAII 归还。
- 报告队列、推理延迟、统一错误和加速器资源信息。

不负责：根据模型版本输出 bbox、构造业务任务或回写 Messaging Sender。

首个 D950 实现是 `hal/inference/rockchip/rknn_backend.*`。以后新增 NVIDIA 或 Qualcomm 产品时，应实现同一 `hal/inference/api`，不能复制或派生一套 TensorRT/QNN 专用的 Service、Pipeline、Decoder 或 Event Schema。模型格式不兼容时由 `ModelArtifact`、capability 和 ProductProfile 在创建会话前返回 `NOT_SUPPORTED` 或 `MODEL_CONTRACT_MISMATCH`。

芯片无关的 InferenceScheduler 位于 Service/ResourceCoordinator 一侧，只做：

- 在多个 context 中选择队列最短且可用的实例。
- 实施每会话和全局最大在途数。
- 取消尚未开始的任务。
- 在 stop 期间拒绝新请求并有界等待在途任务。

厂商 HAL 内的 context pool 只管理本厂商 context、stream、device memory 和核心绑定，不自行实现跨会话优先级或业务调度。

### 7.3 Model Decoder Block

每个 decoder 是一个持有自身不可变配置的实例：

```text
yolov5.decoder
yolov7.decoder
yolov8.decoder
yolov8_seg.decoder
yolov10.decoder
yolov11.decoder
ppyoloe.decoder
```

类别数、label、anchor、NMS、置信度、分割阈值和 transpose 模式不得使用跨实例静态可变状态。Registry 只根据已验证的模型 meta `version/type/output contract` 选择 decoder，未知组合返回 `MODEL_CONTRACT_MISMATCH`。

### 7.4 ROI Block

ROI 是算法分析，不是最终业务报警。Block 输出目标所在 ROI 和使用的判定策略：

```text
CENTER
BOTTOM_CENTER
BOTTOM_EDGE
BBOX_OVERLAP
SEGMENTATION_OVERLAP
```

ROI 配置更新使用不可变快照；单帧处理期间不读取正在修改的 UI JSON。

### 7.5 Tracker Block

Tracker 统一拥有：

- track 状态机、Kalman 状态、LAPJV 匹配和去重。
- IOU、马氏距离、几何距离和可选 MobileNet 特征。
- 性能等级和降级恢复状态。
- 连续性中断、generation 变化和配置更新时的明确 reset。

Tracker 输出 track 注解和健康数据，不生成 UI JSON，不改变 GPO 计数，不决定“禁止消失报警”。禁止消失是 LocalAiApplication 中消费 track/ROI 状态的业务策略。

### 7.6 Depth Verifier Block

Depth backend 和 verifier 分开：

- Depth backend 产生带时间戳和源帧对齐信息的深度图。
- Verifier 对符合跟踪稳定性和最小 bbox 的目标计算残差。
- 过期、尚未产生、不可用和已验证是不同状态。
- 跟踪 fallback 是显式注解 `fallbackUsed=true`，不伪装成深度验证通过。

最终“是否报警”由本地或外部应用根据该证据决定。

---

## 8. 相机应用层

### 8.1 `LocalAiApplication`

现有完整方案使用一个本地应用消费者：

```text
InferenceResultEvent
→ Temporal Evaluator
→ Optional Disappearance Policy
→ Optional Depth Alarm Policy
→ Alarm Decision
→ Local Action Router
   ├─ GPO / LED
   ├─ Record / Snapshot / Operator
   ├─ Customer Alarm Log
   ├─ Legacy ETH / SDK / SVAP output
   └─ UI business text
```

统一业务结果必须使用枚举，不再用裸 `alarmType=0/1/2/3/4`：

```text
NONE
OBJECT_DETECTED
FORBIDDEN_AREA_MISSING
DEPTH_VERIFIED_OBJECT
COMBINED_REGION
```

Legacy Adapter 负责在与旧 `TriggerWithMeta` 交互的最后边界做枚举与整数的映射，新领域代码不传播整数报警类别。

### 8.2 安全服务

PoseGuard、MonumentGuard、failsafe 和看门狗不属于 `LocalAiApplication`，也不是“端侧AI推理”的可选业务动作。

```text
SafetyFrameConsumer
├─ PoseGuardService
├─ MonumentGuardService
├─ FailsafeCoordinator
└─ SafetyOutputController
```

安全服务可与目标检测共享只读帧源或预处理缓存，但拥有独立生命周期、状态、配置和输出权。目标检测方案停止、平台断网或外部订阅者慢不得使其停止。

### 8.3 非业务消费者

下列消费者允许在“端侧AI推理”方案中继续使用：

- `DiagnosticOverlaySink`：预览上的 ROI、bbox、Mask、trackId 和深度验证标记。
- `AiHealthReporter`：Block、会话、队列、延迟、丢弃和资源指标。
- `DiagnosticSampleStore`：经明确配置的低置信度和 regular 样本，使用有界队列和容量限制。
- `EvaluationSubscriber`：模型评测专用，必须抑制一切本地业务副作用。

---

## 9. “端侧AI推理”方案

### 9.1 方案身份

```text
solutionTypeId: edge_ai_inference
displayName.zh-CN: 端侧AI推理
requiredModules: [solution.run, ai.detection]
requiredCapabilities: [solution.runtime, ai.inference, ai.object_detection]
```

内部判断必须使用 `solutionTypeId`，不使用中文名称、项目名或型号字符串。ProductProfile 只在实现和验收所需 capability 后才对某型号公布该方案。

### 9.2 允许和禁止行为

| 行为 | 端侧AI推理 |
|---|---|
| 帧获取、预处理、推理、decoder | 允许 |
| ROI、跟踪、深度证据注解 | 按 capability 和配置允许 |
| WSS/MQTT 结构化结果 | 允许 |
| 预览框、ROI、Mask、trackId | 仅诊断展示，允许 |
| 健康、性能和诊断日志 | 允许 |
| 多帧最终报警真假判断 | 禁止 |
| 禁止消失报警 | 禁止，只可输出 track/ROI 事实 |
| AI 驱动 GPO/LED | 禁止 |
| AI 驱动录像/抓拍/Operator | 禁止 |
| AI 业务报警客户日志 | 禁止 |
| Pose/Monument/failsafe 安全闭环 | 独立本地运行，不受该方案限制 |

新方案不接受 `LocalPolicyConfig`。如果 Legacy 项目 JSON 包含录像、抓拍、GPO 或报警规则字段，创建/更新方案时返回 `INVALID_ARGUMENT`，不能静默接受后忽略。

### 9.3 与“异步推流检测”的关系

- “端侧AI推理”使用新 Action/Event 契约和新配置分层。
- “异步推流检测”继续按现有 SVAP topic、GPO 门控和录像语义运行。
- 两者可在内部共用 `AiInferenceService`，但必须使用不同应用/协议消费者。
- 本轮不把旧 SVAP 报文直接别名为新 Event，不改变旧客户契约。

### 9.4 断网行为

外部平台断开时：

1. 不启动本地 AI 业务兜底，避免同一方案在网络波动时突然改变 GPO/录像语义。
2. 推理管线按配置继续运行，WSS/MQTT 队列只保留有界的最新结果。
3. 重连后从当前最新 sequence 继续，不补发历史逐帧结果。
4. 平台通过 `droppedSincePrevious`、sequence 间隔和健康事件判断数据连续性。
5. PoseGuard、MonumentGuard、failsafe、看门狗和硬件安全默认态继续工作。

---

## 10. 配置分层与兼容迁移

### 10.1 四类配置

```text
InferenceConfig
├─ modelId / modelPath / modelHash
├─ inputWidth / inputHeight / pixelFormat
├─ confidenceThreshold / nmsThreshold / segmentationThreshold
└─ backend / maxConcurrency / resourceClass

AnalysisConfig
├─ roi.enabled / strategy / geometry
├─ tracking.enabled / parameters / featureExtractor
├─ depth.enabled / model / thresholds / freshness
└─ resultExtensions

LocalPolicyConfig
├─ temporalWindow / estimateThreshold / reverse
├─ disappearancePolicy / depthAlarmPolicy
├─ recording / snapshot / operator
├─ gpo / led / customerLog
└─ legacyReports

DeliveryConfig
├─ wss.enabled / maxHz / include
├─ mqtt.enabled / maxHz / topicProfile
├─ mask.inlineSummary / artifactEnabled
└─ diagnosticOverlay / sampleStore
```

### 10.2 配置归属规则

- 本地完整方案：四类配置均可存在。
- 端侧AI推理：只允许 Inference、Analysis 和 Delivery。
- 模型评估：使用 Inference + Analysis，由 EvaluationSubscriber 消费，强制禁用所有业务副作用。
- 安全服务配置不进入上述四类，保留独立配置、权限和生命周期。

### 10.3 `LegacyAiConfigAdapter`

迁移期间不立即改写旧项目 JSON。AI 负责人维护的 `LegacyAiConfigAdapter` 负责：

1. 从 `ObjDectConfig` 读取旧字段。
2. 产生四份强类型内部配置。
3. 对限幅、缺失和弃用字段产生明确 warning。
4. 保留旧方案的默认值、阈值、ROI、类别映射和输出语义。
5. 只在所有正式方案通过升级/降级测试后，才考虑将存储格式迁移为新 schema。

不允许旧字段同时被多个新模块独立解析；Adapter 是唯一转换入口。

对外冻结的 `AiSessionSpec V1` 引用 InferenceConfig 和 AnalysisConfig 的 Schema；`LocalPolicySpec V1` 引用 LocalPolicyConfig 的 Schema。通用模块化负责人维护的 `LegacyProjectAdapter` 只负责 Project 文件、方案生命周期、快照和回滚，不能再次解释这些 AI 字段；`LegacyAiConfigAdapter` 也不能写 Project 文件或控制方案启停。

---

## 11. Action、Event 和外部平台契约

### 11.1 Action / Event Catalog

复用全系列稳定 ID：

```text
solution.start
solution.stop
solution.status.get
ai.detection.config.get
ai.detection.config.update
ai.detection.result
ai.tracking.result
ai.depth.result
ai.inference.state.changed
ai.inference.health.changed
```

Action 不返回高频检测结果；查询返回当前配置、会话状态和健康快照，高频结果通过已认证的 WSS/MQTT 事件通道发布。

### 11.2 `ai.detection.result` V1

```json
{
  "eventId": "01J...",
  "eventType": "ai.detection.result",
  "contractVersion": "1.0",
  "deviceId": "device-stable-id",
  "solutionId": "project-instance-id",
  "sessionId": "ai-session-id",
  "runId": "run-id-after-each-start-or-reconfigure",
  "sequence": 1024,
  "captureFrameId": 9981,
  "generation": 3,
  "capturedAt": "2026-08-19T12:34:56.123Z",
  "monotonicTimeMs": 123456789,
  "model": {
    "id": "helmet-detector",
    "version": "2026.08",
    "hash": "sha256:...",
    "input": {"width": 640, "height": 640}
  },
  "source": {
    "width": 1280,
    "height": 720,
    "coordinateSpace": "normalized_source_frame"
  },
  "latencyMs": {
    "preprocess": 1.2,
    "inference": 12.8,
    "decode": 1.4,
    "endToEnd": 17.1
  },
  "detections": [
    {
      "detectionId": 1,
      "classId": 2,
      "className": "person",
      "confidence": 0.93,
      "bbox": {"left": 0.10, "top": 0.20, "width": 0.30, "height": 0.40},
      "roiIds": ["roi-1"],
      "tracking": {"trackId": "42", "state": "TRACKED", "ageFrames": 18},
      "depth": {"status": "VERIFIED_3D", "residual": 0.041, "dataAgeMs": 83},
      "mask": {
        "areaRatio": 0.12,
        "checksum": "sha256:...",
        "contour": [[0.1, 0.2], [0.3, 0.2], [0.3, 0.5]],
        "artifactId": "optional-artifact-id"
      }
    }
  ],
  "delivery": {
    "droppedSincePrevious": 2,
    "publisherQueueDepth": 0
  }
}
```

强制规则：

- bbox 坐标基于源帧左上原点、`[0,1]` 标准化范围，不是模型 letterbox 坐标。
- 可选结构在未启用对应 Block 时省略，不使用伪造默认值。
- 事件不得出现 `alarmType`、`estimateBool`、`doRecordVideo`、`doSnap`、GPO 或 Operator 动作。
- `sequence` 在同一 `sessionId + runId` 内单调递增；重新启动或成功重配使用新 runId。
- `eventId` 全局唯一；`captureFrameId` 用于与媒体/证据帧关联。
- 不提供完整 tensor、原始帧或内联全尺寸 Mask。

### 11.3 Mask 契约

- 高频事件只携带简化轮廓、面积比和 checksum。
- 轮廓简化必须有顶点上限，超限继续简化而不扩大消息。
- 完整 Mask 仅在 ProductProfile 声明 Artifact 能力且 DeliveryConfig 启用时生成。
- `artifactId` 通过已认证 Artifact HTTPS 查询；事件中不放本地文件路径。
- Artifact 生成和下载不得阻塞推理线程，必须有独立容量和生命周期管理。

### 11.4 WSS 投递

- 握手解析 Principal，订阅时检查 module 和 capability。
- 每个订阅者设置 `maxHz`，不得超过设备公布的 limit。
- 订阅者队列默认 2，满时丢弃最旧检测结果。
- 状态、错误和健康事件与高频结果分队列，不被检测结果覆盖。
- 权限改变或 API Key 撤销后，按统一 PolicyGate 长连接策略终止订阅。

### 11.5 MQTT 桥接

- MQTT 使用与 WSS 完全相同的 Event payload，不维护第二份字段语义。
- `ai.detection.result`、`ai.tracking.result`、`ai.depth.result` 使用 QoS 0 和 latest-first 队列。
- `ai.inference.state.changed`、`ai.inference.health.changed` 使用 QoS 1。
- Broker 断开时不在相机内积压逐帧检测结果；只保留最新状态快照供重连后上报。
- 旧 SVAP topic 和 payload 不在本轮改写。

### 11.6 Python SDK 接口

本文档冻结 SDK 能力，SDK 实现作为后续独立交付：

```python
class CameraClient:
    def get_capabilities(self) -> DeviceCapabilities: ...
    def list_solutions(self) -> list[Solution]: ...
    def start_solution(self, solution_id: str) -> OperationResult: ...
    def stop_solution(self, solution_id: str) -> OperationResult: ...
    def get_ai_status(self, solution_id: str) -> AiStatus: ...
    def update_ai_config(self, solution_id: str, config: AiConfig) -> OperationResult: ...
    def subscribe_ai_results(
        self,
        solution_id: str,
        *,
        max_hz: float,
        include: set[str],
        on_gap: Callable[[SequenceGap], None] | None = None,
    ) -> AsyncIterator[InferenceResult]: ...
```

SDK 负责认证、重连、ActionResult/错误映射、Schema 验证和 sequence gap 回调，不在 SDK 中复制相机算法或报警业务。

---

## 12. ProductProfile 和全系列策略

### 12.1 公共契约和实现

- Module、Action、Event、领域类型、Block 接口和服务接口在两仓保持一致。
- 第一阶段不建新公共仓库，D950 验收后将公共文件按相同相对路径镜像到 AR 仓。
- CI 对镜像文件做内容 hash 或受控 diff，差异必须记录为平台 adapter，不允许静默漂移。
- 公共源码不允许 `AR950/D950/RK3588/RK3576/RV1126B` 条件宏或型号字符串。
- `hal/inference/api` 是跨芯片公共接口；`hal/inference/<vendor>` 是明确允许不同的厂商实现，不要求不同厂商源码内容一致。
- 新增芯片平台时优先增加 Vendor HAL 和 ProductProfile，不新建平行的 AI Service、应用策略或协议目录。

### 12.2 capability

首批 AI capability：

```text
ai.inference
ai.object_detection
ai.target_tracking
ai.depth_estimation
vision.roi
vision.segmentation_mask
ai.mask_artifact
ai.model_evaluation
```

ProductProfile 需要声明 `supported/maturity/limits`，例如模型输入尺寸、最大并发、最大订阅 Hz、ROI 上限和是否支持深度。代码存在但未完成契约、权限、UI 和实机验收的能力标记 `backend_only`。

推理 HAL 还必须声明 `vendor/backendId/modelFormats/precisions/zeroCopy/maxContexts/deviceMemory` 等芯片能力。上层只按稳定 capability 匹配，不判断 `RK/NVIDIA/Qualcomm` 字符串；Event 可报告诊断用 backend 信息，但事件语义和字段不随芯片变化。

### 12.3 全系列迁移顺序

1. D950：首个源码拆分、两种运行模式和对外契约样板。
2. AR950：验证公共源码镜像、单目 RK3588 adapter 和现有跟踪差异。
3. AR940 / D940：验证 RK3576 FrameSource、预处理和 Rockchip 推理 HAL。
4. AR760 / AR765：验证 RV1126B 模型、媒体帧和板级差异。
5. D955：在 D950 契约上单独验证 MCU/PWM、安全输出和恢复。

不能由 D950 和 AR950 代码存在直接宣称另外五个型号支持新方案。

未来 NVIDIA、Qualcomm 或其他端侧芯片型号按同一准入流程增加：实现 `hal/frame`、`hal/image`、`hal/inference`，声明 ProductProfile，运行统一 golden/合同/性能/安全测试。芯片接入不改变上层目录、Action/Event 或本地应用边界。

---

## 13. D950 分期实施任务

每一阶段都必须可独立合并、可回滚，并在通过阶段门禁后才进入下一阶段。

### P0：行为基线和台账

**任务**

- 为检测解码、类别映射、ROI、多帧评估、跟踪、深度、报警类别和各类输出建立 characterization/golden tests。
- 保存代表性图片、tensor 或检测中间结果，测试数据不包含客户隐私。
- 固定同一模型和输入下的 FPS、P50/P95 延迟、RSS、NPU 核心和队列数据。
- 列出 `aiobjdectpolicy`、旧存图、Hungarian/Kalman、测试入口等候选遗留，不直接删除。

**门禁**

- 基线数据可重复，每个业务输出都有至少一个回归样本。
- 当前未覆盖行为明确登记，不以“应该一样”替代证据。

### P1：领域类型和依赖解环

**任务**

- 引入 `FrameView/ModelInput/TensorBundle/DetectionFrame/InferenceResultEvent`。
- 将原始指针所有权改为 RAII 类型，保留现有零拷贝或缓冲复用能力。
- 解除 `detectorbase.h`、`aiobjdect2.h`、`rknn_scheduler.h` 循环 include。
- 保留 `ObjectDect` 方法和返回语义，内部使用 adapter 转换新旧类型。

**门禁**

- 纯领域头文件不 include UI、GPO、Trigger、HTTP/MQTT、RKNN 或型号头文件。
- ASAN/所有权专项用例不出现重复释放、悬挂指针和迟到回调访问已销毁会话。

### P2：算法 Block 化

**任务**

- 抽出 Preprocess、通用 `IInferenceBackend`、Rockchip RKNN HAL 和各 Model Decoder。
- 建立 `hal/inference/api` 与 `hal/inference/rockchip`，确保 RKNN 头文件和 context 不越过 HAL 边界。
- 将 `PostProcessor` 静态可变配置改为 decoder 实例配置。
- 抽出 ROI、Tracker、MobileNet Feature Extractor 和 Depth Verifier。
- 将跟踪从 `stepPost3MakeUiMsg()` 完整移出，UI/Overlay 只读不可变结果。

**门禁**

- 新旧管线对同一输入的 bbox、class、confidence、ROI、track 和 depth 结果在规定浮点容差内一致。
- 同时创建两个不同模型 decoder 不会相互覆盖 label、anchor 或阈值。
- 算法 Block 没有协议和本地业务副作用。
- 使用 Mock backend 可以在无 RKNN SDK 的环境运行管线合同测试；公共头文件不包含厂商 SDK 类型。

### P3：AI 服务层和本地应用分离

**任务**

- 引入 `AiInferenceService`、`AiPipelineSession`、`InferenceResultBus` 和资源协调器。
- 将多帧评估、禁止消失、深度报警、GPO/LED、录像/抓拍/Operator、客户日志和旧通信移入 `LocalAiApplication`。
- 将 Pose/Monument/failsafe 生命周期从 `ObjectDectImpl` 抽为独立 Safety Service。
- `ObjectDect` façade 内部组装新服务和本地应用，现有 `Project` 继续消费兼容结果。

**门禁**

- 现有完整方案的配置、报警边沿、GPO、录像、抓拍、UI 和协议 golden tests 全部通过。
- 停止或重配 AI 会话不停止 Safety Service。
- 每个消费者慢或异常不能阻塞推理线程。

### P4：端侧AI推理方案和外部契约

**任务**

- 注册 `edge_ai_inference` 方案类型和 capability 过滤。
- 接入 Action Catalog、WSS Event Adapter、MQTT Bridge 和权限判断。
- 实现 per-subscriber `maxHz`、latest-first 队列、sequence gap 和状态事件。
- 保留 Diagnostic Overlay 和可选 Sample Store，不注册 LocalAiApplication。
- 为平台发布 JSON Schema、Mock 和 Python SDK 接口说明。

**门禁**

- 新方案运行时没有 AI 驱动的 GPO、LED、录像、抓拍、Operator 或业务报警日志。
- WSS 慢消费者、MQTT 断网和平台重连不使队列或 RSS 无界增长。
- WSS 和 MQTT 对同一结果的 payload 在传输层字段外完全一致。
- 旧“异步推流检测”和 SVAP 回归通过。

### P5：D950 完整验收

**任务**

- 在同模型、分辨率、输入和运行时长下对比重构前后 FPS、P95 延迟、RSS 和 NPU 使用。
- 验证模型切换、方案启停、快速重连、慢订阅、断网、回放 seek/generation 和异常停止。
- 独立验证 PoseGuard、MonumentGuard、failsafe 和硬件安全默认态。

**门禁**

- 同配置推理 FPS 和 P95 延迟相对基线回退均不超过 5%。
- 峰值 RSS 增量不超过基线 10%，长时间慢消费/断网不出现持续增长。
- 所有新旧行为对照、契约、安全和恢复用例通过。

### P6：AR 迁移和全系列 ProductProfile

**任务**

- 将已通过 D950 验收的公共源码镜像到 AR 仓。
- 先接入 AR950，核对其现有跟踪、客流统计和 RV1126B 兼容边界，不直接覆盖差异。
- 按 RK3588、RK3576、RV1126B 实现 `hal/frame`、`hal/image`、`hal/inference/rockchip` 适配，按七个正式 productId 声明 capability/maturity/limits。
- 建立公共源码 diff 和 Action/Event 合同测试。

**门禁**

- 七个 productId 均执行同一套契约测试；不支持项返回 `NOT_SUPPORTED`。
- 公共文件内容一致；平台和产品差异只存在适配器、ProductProfile 和 capability 数据。
- Vendor HAL 目录之外不存在 RKNN 类型或厂商 SDK include，并预留 NVIDIA、Qualcomm backend 的同接口接入位置。

### P7：遗留路径退役

仅在 P0–P6 的覆盖和回滚路径均存在时执行：

- 确认并删除不再可达的 `aiobjdectpolicy` 双轨实现。
- 删除旧存图实现和编入正式目标的纯测试入口。
- 在证明无调用后合并或删除重复 Hungarian/LAPJV、Kalman 和 JSON 头文件。
- 移除 `ObjectDect` 兼容 façade 前，必须证明 `Project`、评测、回放、HTTP 和测试入口已全部迁移。

---

## 14. 测试和验收矩阵

### 14.1 单元和 golden tests

| 模块 | 必测项 |
|---|---|
| Preprocess | stride、crop、letterbox、RGB/BGR、640/1280、非法 buffer |
| Decoder | 每个支持模型版本、量化/浮点、NMS、空结果、多类别、Seg |
| ROI | 五种策略、边界点、多 ROI、polygon、Mask overlap |
| Tracker | 创建、确认、丢失、重激活、generation reset、降级/恢复 |
| Depth | 新帧、复用、过期、平面拒绝、立体通过、fallback |
| Local policy | 窗口阈值、反转、禁止消失、报警边缘、动作去抖 |
| Delivery | 限频、丢旧保新、sequence gap、WSS/MQTT Schema 一致 |

### 14.2 兼容对照

- 旧方案配置通过 Adapter 转换后，模型、阈值、ROI、类别、多帧和输出与原实现一致。
- 同一输入分别运行旧路径和新路径，保存逐帧 diff，超出浮点容差即失败。
- 完整方案对每种报警模式核对 GPO、LED、录像、抓拍、Operator、客户日志和旧协议。
- 端侧AI推理使用副作用探针，任一业务动作计数非零即失败。

### 14.3 线程、故障和背压

- Block 启动中途失败反向回滚，无遗留线程、NPU context 或帧订阅。
- 快速 start/stop/reconfigure 循环不死锁、不重复释放、不处理旧 runId 结果。
- WSS 消费者停止读取、MQTT Broker 离线和 DNS 失败时，推理 FPS 不被网络线程反压。
- 丢帧、跳 sequence、回放 seek 和系统时间回跳分别使用 captureFrameId、generation 和 monotonic time 处理。
- 消费者抛异常仅隔离该消费者，不终止结果总线。

### 14.4 性能门禁

在同一模型、帧源、输入尺寸、Block 配置和运行时长下：

- 推理 FPS 回退不超过 5%。
- 端到端 P95 延迟回退不超过 5%。
- 峰值 RSS 增量不超过 10%。
- 30 分钟慢订阅和 MQTT 断网测试中 RSS 无单调增长，队列深度不超过配置上限。
- 诊断 Overlay 开/关不改变检测结果和业务动作。

### 14.5 安全验收

- 平台、WSS 和 MQTT 全部断开后，PoseGuard、MonumentGuard、failsafe 和看门狗持续工作。
- 端侧AI推理方案无权的身份无法启停、更新或订阅结果。
- 产品不支持返回 `NOT_SUPPORTED`，身份无权返回 `FORBIDDEN`，资源被占用返回 `TEMPORARILY_UNAVAILABLE/RESOURCE_BUSY`。
- 事件、日志和健康数据不暴露本地路径、认证凭据、原始指针或未授权原始画面。

### 14.6 全型号验收

| 代码树 | 产品 | 公共合同 | 专项验收 |
|---|---|---|---|
| AR | AR950 | 全量 | RK3588、单目、跟踪/客流差异 |
| AR | AR940 | 全量 | RK3576 帧源和推理 adapter |
| AR | AR760 | 全量 | RV1126B 媒体、模型和 IO |
| AR | AR765 | 全量 | RV1126B 板级和传感器差异 |
| D | D940 | 全量 | RK3576 及双节点 capability 判定 |
| D | D950 | 全量 | 首个样板、深度、Mask、评测、pair |
| D | D955 | 全量 | MCU/PWM、安全默认态和恢复 |

“全量”表示运行同一套 Action/Event/Error/Auth 合同测试，不表示所有型号都必须支持深度、Mask 或端侧AI推理。

---

## 15. 发布、回滚和观测

### 15.1 兼容开关

迁移期每个旧完整方案可按方案或内部调试配置选择 `legacy` 或 `block_pipeline`，默认保持已验收路径。端侧AI推理只允许新管线，因为旧路径无法证明没有本地业务副作用。

回滚只切换管线选择和消费者组装，不自动重写已存旧项目 JSON。

### 15.2 观测指标

```text
ai_session_state
ai_frames_received_total
ai_frames_dropped_total{reason}
ai_block_latency_ms{blockId,quantile}
ai_block_errors_total{blockId,errorCode}
ai_inference_inflight
ai_result_subscriber_queue_depth{subscriberType}
ai_result_delivery_dropped_total{subscriberType}
ai_continuity_resets_total{consumer}
ai_model_identity
```

以上指标通过内部健康和受权的 `system.diagnostics` 导出，不在默认客户日志中逐帧打印。

### 15.3 停止条件

出现下列任一情况时暂停下一阶段，先修复当前阶段：

- 旧完整方案出现未解释的行为差异。
- 端侧AI推理产生本地业务副作用。
- 安全服务因 AI 会话启停、网络或慢消费者停止。
- 跨模型 decoder 配置污染、无界队列、循环 include 回归或新的型号宏泄漏。
- 性能超出本文门禁且未定位原因。

---

## 16. 代码评审检查表

每个 AI 重构 PR 至少回答：

- 本 PR 修改的是 HAL、Block、Service、Application 还是 Transport？
- 厂商推理、图像或帧处理代码是否只落在对应 `hal/` 子目录，公共头文件是否泄露厂商类型？
- 是否引入了反向依赖或新的型号/SoC 分支？
- 新类型的内存、线程和回调所有权是否明确？
- 队列是否有上限，满时策略是什么？
- 新旧管线行为对照和回滚开关是否存在？
- 端侧AI推理模式下是否可能产生任何业务副作用？
- Safety Service 是否仍可独立启停和恢复？
- Action/Event Schema、moduleId、capability 和权限是否同步？
- D950 变更是否已评估 AR 对应实现，公共文件是否保持一致？
- 本 PR 的阶段门禁、性能证据和未验收项是否明确？

---

## 17. 本文档的明确假设

1. AI 重构第一阶段和 DeepEdge DE-1 不引入独立 AI 进程、相机内 Python、动态库热替换或任意 DAG。DeepEdge DE-2 才允许独立 `blockd` 承载签名的自定义应用逻辑；它不加载进 C++ 管线、不默认处理原始帧，崩溃或卡死时由通用运行时隔离，安全回落由 C++ 服务执行。
2. “模块可独立更新”在本阶段表示源码目录、契约、测试、版本和部署包可独立演进，实际仍随相机应用/固件发布。
3. D950 是首个实施样板，不代表其他型号自动具备深度、Mask、跟踪、Artifact 或端侧AI推理能力。
4. 完整 Mask、原始帧和 tensor 不进入高频 Event；原始帧继续使用媒体或证据/Artifact 契约。
5. 新 Action/Event 依赖全系列接口治理的 Catalog、PolicyGate 和认证主链；在该主链未落地前可先完成内部 Block/Service 拆分和 Mock 合同，不新增绕过治理的裸端口。
6. 编译、打包、部署和实机验收属于后续实施阶段，不由本设计文档声称已完成。
7. NVIDIA、Qualcomm 目录是稳定扩展点和依赖边界，不代表当前固件已经引入相应 SDK、模型转换链或产品 capability；具体 backend 在对应芯片型号立项时单独实施和验收。
