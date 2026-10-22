# 全系列相机 DeepEdge 渐进式 DAG 适配与三阶段实施说明

> 文档定位：DeepEdge 与相机应用编排专项的最终架构裁决和研发拆分依据<br>
> 当前状态：设计冻结，尚未声称源码、固件或设备验收已经完成<br>
> 适用范围：AR、D 两套相机代码树及 DeepEdge 平台<br>
> 近期样板：AR950、D950；其余型号通过 ProductProfile 和 capability 逐步接入<br>
> 编号规则：阶段号使用 `DE-1/DE-2/DE-3`，任务号使用 `DE1-*`、`DE2-*`、`DE3-*`；不替代通用模块化重构或 AI 专项自己的阶段编号

配套文档：

- [全系列相机接口治理、用户组权限与平台化改造实施说明](./全系列相机_模块化重构方案审核与实施说明.md)
- [全系列相机功能模块定义与外部平台 Block 对接说明](./全系列相机_Block模块定义与划分说明.md)
- [全系列相机 AI 算法服务化与端侧推理 Block 重构实施说明](./全系列相机_AI算法服务化与端侧推理Block重构实施说明.md)
- [算法平台与相机交互最终形态讨论](../算法平台与相机交互最终形态讨论.md)
- [相机 DAG 适配改造清单](../相机DAG适配改造清单.md)

最后两份文档是调研记录和问题清单，可能包含阶段性结论；出现冲突时，以本文的架构裁决、契约和阶段门禁为准。

---

## 1. 最终结论

DeepEdge 最终采用“**一个逻辑应用 DAG、平台与相机两个执行域、三种受控运行形态**”，但不向平台开放相机内部 AI 算法流水线。

```text
DeepEdge 全局应用 DAG
  业务规则 / Python / 状态机 / 跨设备编排 / 第三方集成
                         │ 编译、分区
             ┌───────────┴───────────┐
             ▼                       ▼
       PlatformPlan              DevicePlan
       DeepEdge 执行             相机受控执行
             │                       │
             └──── BridgeContract ───┘
                    Action / Event
```

必须同时冻结以下结论：

1. DeepEdge 可以自由组合的是**公开、白名单、强类型的应用节点**，不是 RKNN/TensorRT/QNN、预处理、Decoder 或内部 Tracker。
2. AI 内部 `Preprocess → Inference → Decoder → ROI → Tracker → Depth → Assemble` 仍由 AI 专项负责人维护为私有固定管线；对 DeepEdge 暴露为一个或少数稳定 AI 服务节点。
3. MQTT、WSS、HTTPS、UDS 只是同一 Action/Event 的传输适配器，不是四套业务接口；AI 源码不得直接拼 topic、URL 或 major/minor。
4. `default.json`、中文方案类型和现有 major/minor 只允许留在 `LegacyProjectAdapter` 内，不成为 DeepEdge 公共合同。
5. 第一阶段先交付“平台远程编排”和“相机本地模板”两条短期闭环；第二阶段再引入受控的相机内 Python；第三阶段才实现受限应用 DAG。
6. 相机内 Python 属于 DeepEdge 应用层的一个部署位置，不属于 AI 服务层，也不进入 `camera` 进程或 C++ 算法管线。
7. PoseGuard、MonumentGuard、failsafe、看门狗、硬件默认态和安全闭环始终固定在相机受信 C++ 服务中，平台断开或 Python 崩溃不能使其停止。
8. 第一、二阶段只允许一个活动 AI 业务方案；多方案并行必须等 ResourceCoordinator 和 DE-3 资源校验具备后另行开放。

这不是照搬某一家产品的运行时。可借鉴 Luxonis DepthAI V3 的三个原则：节点端口是有类型的、Host/Device 节点可以处于同一逻辑管线、跨执行域桥接由框架处理；其官方文档同时说明输入队列需要明确阻塞与长度，阻塞队列可能冻结上游，非阻塞队列会淘汰旧消息。本文只采用这些架构原则，不引入 DepthAI 依赖，也不复制其 API：

- [DepthAI V3 Porting Guide](https://docs.luxonis.com/software-v3/depthai/tutorials/v2-vs-v3/)
- [DepthAI Device Nodes](https://docs.luxonis.com/software-v3/depthai/depthai-components/nodes/)
- [DepthAI Host Nodes](https://docs.luxonis.com/software-v3/depthai/depthai-components/host_nodes/)

---

## 2. 为什么不能把原三种设想做成三套独立系统

原三种设想都有实际价值，但如果分别落成 MQTT 程序、配置下发程序和 Python 旁路程序，会形成三套配置、三套状态、三套错误和三套回滚路径。

| 原设想 | 保留的产品价值 | 必须纠正的实现方式 |
|---|---|---|
| 相机只推理，DeepEdge 判断并用 MQTT 控制录像/抓拍/GPO | 平台快速更新业务、跨设备组合 | 使用稳定 Event/Action；MQTT 只是适配器，不能让 Python 硬编码现有 topic |
| DeepEdge 画节点后下发相机已有 `default.json` | 近期最快复用完整本地方案 | 平台下发版本化 `FixedSolutionSpec`；整文件替换只封装在 Legacy Adapter 中 |
| 下发配置和 Python，在相机启动 Python 进程 | 断网运行、低延迟、客户定制 | 放到 DE-2 的独立 `blockd`；使用结构化消息和本地 Action Client，不访问 HAL、原始内部对象或回环 MQTT |
| 最终 DAG | 可视化组合和节点复用 | 只开放受限应用 DAG；AI 算法 Block Registry 保持私有 |

因此，原三种设想在本文中被收敛为三个稳定运行形态，而不是三条长期平行技术栈。

---

## 3. 当前基础和不能误判的证据

当前工程已经具备部分“可接入基础”，但还没有形成目标服务合同：

- `cam/setting/svapprotocol.h` 已集中定义“异步推流检测”、推理结果、录像、抓拍和 GPO/GPI 事件相关 MQTT 常量，说明现有 SVAP 路径可以作为兼容适配器。
- `tools/mqttclient/` 已使用 Paho MQTT 异步客户端，具备连接、订阅和发布基础；它仍是通用传输实现，不应继续承载方案业务判断。
- 当前默认 SVAP MQTT 入站只覆盖录像、手动录像和抓拍，没有可直接复用的 GPO 控制主题；现有 HTTP GPIO 入口还能接受物理 index/edge，也不适合作为 Block 合同。因此 DE-1 的 `io.gpo.*` 必须是新增的逻辑 Action，再由协议适配器映射。
- `Project::readConfigFile()` 在方案运行时会拒绝读取配置；现有部署路径必须考虑停机、预验证、激活失败和恢复旧方案。
- `Project::doJsonCommand()` 的整方案更新直接写入并调用 `updateConfig()`，尚不能等同于具备 `validate → stage → activate → rollback` 的事务部署服务。
- 当前 AI 后处理仍直接生成 MQTT JSON，并同时触达 GPO、LED、录像、抓拍和 Operator；仅凭“异步推流检测”抑制部分 GPO 事件，不能证明端侧推理模式已经无本地业务副作用。
- AR、D 的 MQTT 回调、项目切换、GPO payload 和 generation 处理已有差异，公共契约必须用同一组 Mock/合同测试重新收口，不能选择其中一仓的现状作为标准。
- 调研文档中已有整配置替换和 Python 旁路的 PoC/设备记录；这些记录只能证明路径可能可通，不能证明鉴权、事务、资源隔离、升级兼容和全型号产品化已经完成。

代表性差异和处理方式如下：

| 现状 | 工程证据 | DE 处理 |
|---|---|---|
| 两仓都有录像/手动录像/抓拍 MQTT 控制，当前没有入站 GPO 控制 topic | `setup/*/config/global/config.json`、`cam/camera/camerabase.cpp` | 复用媒体执行器；新建逻辑 `io.gpo.*` Action，不承诺“现有 MQTT 已支持 GPO 控制” |
| 当前 AI 直接生成旧 MQTT JSON，且缺少统一连续性头 | 两仓 `cam/aiobjdect/aiobjdect2.cpp` | 旧 JSON 进入 Legacy Adapter；新事件由 Result Bus 生成 |
| D 已有 generation 迟到结果处理，AR/D 语义尚未统一 | D `cam/aiobjdect/aiobjdect2.cpp` | 提炼成公共合同和 golden tests，不直接复制某仓状态字段 |
| D 的 MQTT 回调/连接线程比 AR 多一部分安全收口 | 两仓 `tools/mqttclient/mqttclient.cpp` | 先对齐 transport 基线，再做同 Schema 发布器 |
| 两仓现有 GPO payload 和项目切换流程存在差异 | `cam/camera/camerabase.cpp`、`cam/handlecmd/camerabase_handlecmd.cpp` | 公共 Action/operation 隐藏差异，Adapter 分仓实现 |
| D 的 `cam/blockexp` 只是未进入正式主链的旁路实验 | D `cam/blockexp/block_exp_*` | 只借鉴 wire、有界队列和逻辑 GPO 白名单，不认定 `blockd` 已产品化 |

所以 DE-1 可以复用现有方案、MQTT 和 Project 能力，但必须先在外面增加稳定 façade，不能让 DeepEdge 直接绑定内部实现。

---

## 4. 目标边界：两个 Registry，不是一张内部大图

### 4.1 AI 私有算法 Registry

由 AI 专项负责人维护：

```text
AlgorithmBlockRegistry（私有）
  FrameSource
  Preprocess
  InferenceBackend
  ModelDecoder
  DetectionNormalize
  RoiAnnotator
  Tracker
  DepthVerifier
  ResultAssembler
```

特性：

- 强类型 C++、静态链接、固定管线模板。
- 推理 HAL 只位于 `cam/ai/hal/inference/{api,<vendor>,mock}/`；厂商实现只能进入对应 `<vendor>/`。
- 不接受 DeepEdge 下发 C++ 类名、厂商 SDK 名、任意边或动态 `.so`。
- 对外只输出不可变 `InferenceResultEvent` 和 AI 会话服务接口。

### 4.2 DeepEdge 公开应用 Node Catalog

由通用模块化/DeepEdge 适配负责人维护：

```text
ApplicationNodeCatalog（公开）
  camera.ai.detections
  camera.ai.tracks
  camera.ai.depth
  logic.threshold
  logic.temporal
  logic.state_machine
  app.python
  camera.action.gpo
  camera.action.record
  camera.action.snapshot
  integration.notify
```

特性：

- 节点有稳定 nodeType、版本、输入/输出端口、配置 Schema、资源和 capability 声明。
- 节点只依赖公开服务和消息，不 include AI 私有头文件。
- 节点实际执行位置由 Catalog 和相机能力决定，用户图不能直接填写 `runOn` 或进程名。
- 编译结果可以回显 `resolvedPlacement`，便于诊断，但不能用回显值绕过重新校验。

### 4.3 公开 AI 节点是原子服务

DE-1 和 DE-2 中，DeepEdge 看到的 AI 节点至少包含：

```text
camera.ai.object_detection@1
  input:  AiSessionConfig
  output: DetectionEventV1
  optional output: TrackingEventV1 / DepthEventV1
  actions: start / stop / reconfigure / status
```

是否启用 ROI、Tracker、Depth 由配置和 capability 决定，但 DeepEdge 不连接它们的内部 C++ 端口。只有当未来存在明确的产品需求、稳定契约和独立资源模型时，才可以把某个分析能力提升为额外公开服务节点；不能因为内部已拆成 Block 就自动对外开放。

---

## 5. 三种稳定运行形态

### 5.1 `managed_local_ai`：相机本地完整方案

适用于断网仍需完整业务闭环、已有方案已经稳定、需要最短交付周期的场景。

```text
DeepEdge FixedSolutionSpec
          │ deploy
          ▼
相机 AI Service → LocalAiApplication
                     ├─ 多帧/禁止消失/报警分类
                     ├─ GPO/LED
                     ├─ 录像/抓拍
                     └─ 旧协议/客户日志
```

DeepEdge 提供可视化配置体验，但不执行逐帧业务逻辑。第一阶段由 `LegacyProjectAdapter` 把 `FixedSolutionSpec` 转换为现有配置并原子应用；后续内部实现可以换成新服务，平台合同不变。

### 5.2 `edge_ai_inference`：端侧推理、平台编排

适用于平台在线、业务变化快、需要跨设备或第三方系统组合的场景。

```text
相机 AI Service ── Detection/Tracking/Depth Event ──> DeepEdge
相机 Media/GPO  <── record/snapshot/gpo Action ────── DeepEdge
```

该形态只产生事实型结构化结果和诊断信息，不装配本地 AI 业务消费者，不产生 AI 驱动的 GPO、LED、录像、抓拍、Operator 或业务报警日志。平台断开后推理可以继续，发布队列有界丢旧；不得自动切换为本地业务判断。

### 5.3 `deepedge_custom_application`：相机内受控 Python 应用

DE-2 才引入，适用于需要断网运行、低延迟自定义业务或客户专属逻辑的场景。

```text
AI 结构化结果 → UDS Bridge → blockd / Python Application
                                      │ Local Action Client
                                      ├─ 逻辑业务 GPO
                                      ├─ 录像/抓拍
                                      └─ 日志/外部事件
```

Python 不进入 `camera` 进程，不接收 Tensor、厂商 handle 或默认的原始帧，不访问 `/dev`，也不直接持有物理 GPO 引脚。它只能通过公开消息和本地 Action Gateway 工作。

### 5.4 运行形态对比

| 项目 | `managed_local_ai` | `edge_ai_inference` | `deepedge_custom_application` |
|---|---|---|---|
| 业务判断位置 | 相机 C++ 本地应用 | DeepEdge | 相机 `blockd` 中 Python |
| AI 推理位置 | 相机 AI Service | 相机 AI Service | 相机 AI Service |
| 断网后的业务闭环 | 保持 | 不保持，且不自动切本地 | 已激活应用可保持 |
| AI 驱动本地副作用 | 按方案允许 | 全部禁止 | 仅通过受控 Action 允许 |
| 首次交付阶段 | DE-1 | DE-1 | DE-2 |
| 是否为任意 DAG | 否 | 平台侧可编排，相机侧否 | 否，固定拓扑 |

三个身份必须可观测且互斥；不能因平台掉线、Python 崩溃或重启而静默换成另一个身份。

---

## 6. 统一合同：协议只是适配器

### 6.1 Action/Event 主链

```text
MQTT / WSS / HTTPS / 本地 UDS
             │ Transport Adapter
             ▼
    Principal + PolicyGate + Audit
             │
             ▼
      Action Dispatcher / Event Bus
             │
             ▼
 AI / Solution / Media / GPIO Service
```

DE-1 即使暂时把 DeepEdge 视为受信主体，也必须在合同中保留 principal、moduleId、capability 和审计字段；后续接入用户组/API Key 时只替换身份实现，不重写 AI 或 DeepEdge SDK。

### 6.2 首批稳定 Action

| 领域 | Action |
|---|---|
| 方案 | `solution.validate`、`solution.deploy`、`solution.start`、`solution.stop`、`solution.status.get`、`solution.rollback` |
| AI | `ai.detection.config.get`、`ai.detection.config.update`；按 capability 开放 `ai.tracking.config.get`、`ai.tracking.config.update`、`ai.depth.config.get`、`ai.depth.config.update` |
| 媒体 | `media.recording.start/stop`、`media.snapshot.create`、`artifact.get` |
| IO | `io.gpo.set/pulse`、`io.gpo.lease.acquire/renew/release` |
| 应用（DE-2 起） | `application.install/activate/stop/status.get/rollback` |
| DAG（DE-3） | `graph.validate/deploy/start/stop/status.get/rollback` |

现有 `camera/<id>/cmd/...`、推理 topic 和 major/minor 由 Transport/Legacy Adapter 映射到这些语义 Action；新平台 SDK 不直接公开旧字面量。

`IAiInferenceService::create/start/stop/status/reconfigure/subscribe` 是相机内部 C++ façade，由 Solution Service 和兼容 façade 调用，不再额外暴露成一套外部 session Action。这样外部合同继续沿用 `solution.*` 和 `ai.*.config.*`，不会出现平台同时维护“方案生命周期”和“AI session 生命周期”两套入口。

### 6.3 首批稳定 Event

| Event | 语义 |
|---|---|
| `ai.detection.result` | 一帧事实型检测结果 |
| `ai.tracking.result` | 可选跟踪事实 |
| `ai.depth.result` | 可选深度验证事实 |
| `ai.inference.state.changed` | 会话生命周期 |
| `ai.inference.health.changed` | 健康、队列和资源变化 |
| `solution.state.changed` | 方案部署和运行状态 |
| `media.recording.state.changed` | 录像动作状态 |
| `media.snapshot.created` | 抓拍 Artifact 已生成 |
| `io.gpo.state.changed` | 逻辑通道状态 |
| `application.state.changed`（DE-2 起） | Python 应用生命周期 |

AI 事件不得携带 `alarmType`、`doRecordVideo`、`doSnap`、GPO 或最终业务真假值。

### 6.4 三类消息必须使用不同队列语义

| messageClass | 场景 | 队列 | 满载行为 | 必须字段 |
|---|---|---|---|---|
| `FACT_LATEST` | 检测、跟踪、深度事实 | 小型有界队列 | 丢旧保新 | runId、sequence、generation、droppedSincePrevious |
| `STATE_COALESCED` | 健康、当前状态 | 按 key 合并 | 保留每个 key 最新状态 | stateVersion、changedAt |
| `COMMAND_ORDERED_ACK` | GPO、录像、抓拍、部署 | 有界有序队列 | 明确拒绝，不静默丢弃 | correlationId、idempotencyKey、deadline、ack/error |

不能把所有边统一成 latest-first。事实流允许跳帧；动作必须可确认、可幂等、可超时并可审计。

### 6.5 连续性和迟到结果

所有 AI 事实事件至少携带：

- `contractVersion`、`eventId`、`deviceId`、`solutionId`、`runId`。
- `sequence`、`captureFrameId`、`generation`。
- `capturedAt`、`monotonicTime`、端到端延迟。
- 模型 ID、版本、hash 和输入尺寸。
- `droppedSincePrevious` 和发布器健康摘要。

方案重启、回放 seek 或安全重配必须生成新的 runId 或 generation。订阅者不得把旧 generation 的迟到结果应用到新方案。

---

## 7. 配置、部署和回滚

### 7.1 DE-1 使用 `FixedSolutionSpec V1`

平台只提交语义配置，不提交相机内部文件：

```json
{
  "contractVersion": "1.0",
  "solutionId": "customer-line-a",
  "profile": "edge_ai_inference",
  "aiSession": {
    "modelRef": {"id": "ppe-yolo", "version": "3.2.0", "hash": "..."},
    "inference": {},
    "analysis": {}
  },
  "localPolicy": null,
  "delivery": {}
}
```

- `managed_local_ai` 允许受 Schema 约束的 `localPolicy`。
- `edge_ai_inference` 必须拒绝 `localPolicy`，而不是接收后忽略。
- 平台不得传本地绝对路径、中文方案类型、C++ 类名、厂商 backend 名或物理引脚。

其中 `aiSession` 使用双方冻结的 `AiSessionSpec V1`；`localPolicy` 引用 AI 负责人维护语义、通用部署层只做引用和版本校验的 `LocalPolicySpec V1`。通用部署层校验方案 envelope、版本和引用，AI Service 校验模型、Inference/Analysis/LocalPolicy 的领域约束；通用负责人不能依据旧 Project 字段自行复制一套 AI 配置模型。

### 7.2 原子部署状态机

```text
RECEIVED
   │ schema/capability/resource validate
   ▼
VALIDATED ── stage artifact/config ──> STAGED
   │                                  │
   └──────── reject, no side effect   │ activate
                                      ▼
                                ACTIVATING
                                  │      │
                            success      failure
                                  ▼      ▼
                               ACTIVE  ROLLING_BACK
                                           │
                                           ▼
                                      PREVIOUS_ACTIVE
```

必须先在不停止当前方案的情况下完成 Schema、capability、模型 hash、资源和安全校验。只有进入 `ACTIVATING` 才允许短暂停止旧方案。DE-1 可以在 Legacy Adapter 内使用“停—写—启”，但必须保留旧配置快照、激活超时和自动恢复；平台只看到标准 operation 状态。

### 7.3 `default.json` 的最终位置

`default.json` 是旧实现的持久化格式，不是 API：

```text
FixedSolutionSpec
       │
       ▼
SolutionDeploymentService
       │
       ▼
LegacyProjectAdapter ──> 旧配置 / 旧命令 / Project
```

未来 Project 内部重构时只替换最下层 Adapter，不改变 DeepEdge 画布、SDK 和合同测试。

### 7.4 DE-2 的应用包

`ApplicationBundleDescriptor` 只允许声明：

- bundleId、version、entrypoint、Python ABI。
- 输入/输出消息类型和版本。
- 所需公开 Actions/capabilities。
- CPU、内存、队列、处理超时和失败策略。
- 文件 hash、签名、发布者和兼容固件范围。

它不得声明 C++ 类、动态库、HAL、设备文件、物理 GPIO、任意 DAG 连线或 root 权限。最低产品要求采用签名校验；hash 只用于内容完整性，不能代替发布者信任。

### 7.5 `CustomApplicationSpec V1` 联合部署

DE-2 的“基础 AI 配置 + Python 包”必须作为一个方案原子部署，不能让 AI 会话已切换而 Python 仍是旧版本：

```text
CustomApplicationSpec
  solutionId / version
  aiSession: AiSessionSpec
  applicationBundle: bundleId / version / hash
  grantedActions / actionPolicy / requiredCapabilities
  resourceBudget / failurePolicy
```

`actionPolicy` 只引用逻辑 GPO 通道、录像 profile、抓拍/Artifact 约束和默认超时，不包含物理引脚。部署服务必须先同时验证模型、AI 配置、Bundle 签名、Action 权限和资源，再一起 stage；激活任一环节失败时，AI 会话、应用包和 lease 一起恢复到上一活动版本。

### 7.6 DE-3 的图部署

第一版 `GraphSpec` 采用整图替换：先离线校验和编译新图，再停止旧图并原子切换；不做逐节点热更新。失败时旧图保持或恢复运行。局部热更新只有在状态迁移协议、资源一致性和全量回滚有明确测试后才可立项。

---

## 8. 安全、GPO 和资源边界

### 8.1 安全 GPO 与业务 GPO 分开

| 类型 | 所有者 | Python/平台权限 |
|---|---|---|
| 安全 GPO、failsafe、心跳、硬件默认态及 PoseGuard/MonumentGuard/看门狗闭环 | 相机受信 C++ Safety Service | 只能观察或配置获准参数，不能成为闭环必经路径 |
| 业务 GPO，如提示灯、普通继电器联动 | IO Service | 通过逻辑通道 lease 和带 ACK 的 Action 使用 |

如果某个 GPO 最终控制机械停机、人员安全回路或要求确定性最坏时延，它必须被归入安全 GPO；Python 可以提供检测事实或业务请求，但不能拥有最终安全闭环。

### 8.2 逻辑通道 lease

平台或 Python 申请的是 `business_alarm_1` 等逻辑通道，不是 GPO2/高电平：

- ProductProfile 把逻辑通道映射为实际引脚、极性和默认态。
- lease 有 owner、TTL、renew、冲突规则和失效回落状态。
- 同一通道的并发写入必须明确拒绝或按预先冻结的优先级仲裁。
- `blockd` 崩溃、超时或被杀死后，由 C++ IO/Safety Service 执行回落。

### 8.3 Python 隔离

DE-2 至少要求：

- `blockd` 与 `camera` 独立进程、独立用户和最小文件权限。
- CPU、RSS、进程数、文件大小、日志量和消息队列均有硬上限。
- 禁止访问 `/dev`、厂商 SDK、相机内部共享对象和任意网络监听端口。
- 本机服务调用走 UDS Action Client，不通过回环 MQTT/HTTP。
- 卡死判断以“有输入但无进展”为基础；只看 PID 存活不算健康。
- 崩溃退避、最大重启次数、隔离状态和人工恢复均可观测。

### 8.4 图资源约束

DE-3 每个 NodeDescriptor 声明 CPU、内存、NPU 会话、队列、媒体编码器、Artifact 和逻辑 GPO lease。Graph Validator 必须在切换前完成资源总量、互斥、生命周期和 ProductProfile capability 校验；不允许节点在 `start()` 后再无上限抢资源。

---

## 9. 目录与负责人边界

建议的目标目录按“公开合同、通用服务、DeepEdge 运行时、AI 私有实现”分开：

```text
cam/
├── contracts/                         # 小型、版本化、跨组冻结
│   ├── action/
│   ├── event/
│   ├── solution/
│   ├── application/
│   └── graph/
├── services/                          # 通用模块化负责人
│   ├── action_gateway/
│   ├── solution_deployment/
│   ├── media/
│   ├── io/
│   └── artifact/
├── integration/deepedge/              # 协议和平台适配
│   ├── mqtt_adapter/
│   ├── wss_adapter/
│   ├── capability_adapter/
│   └── legacy_project_adapter/
├── application_runtime/               # DE-2/DE-3，通用负责人
│   ├── blockd/
│   ├── bundle_manager/
│   ├── ipc_bridge/
│   └── dag/
│       ├── application_node_catalog/
│       ├── graph_validator/
│       ├── graph_compiler/
│       └── graph_executor/
└── ai/                                # AI 专项负责人
    ├── domain/
    ├── blocks/                        # 私有 AlgorithmBlockRegistry
    ├── hal/inference/{api,<vendor>,mock}/
    ├── service/
    ├── application/
    └── adapters/
```

这是目标边界，不要求 DE-1 一次搬完全部现有源码。两仓第一阶段仍采用同相对目录、同接口、同公共源码镜像；不引入公共子仓库、动态插件系统或新的跨仓发布基础设施。

### 9.1 通用模块化 / DeepEdge 适配负责人

负责：

- Action Gateway、Event Adapter、权限、审计和统一错误。
- SolutionDeployment、Media、IO/GPO、Artifact 等稳定服务 façade。
- MQTT/WSS/HTTPS/UDS 适配和旧 Project/SVAP 兼容。
- `blockd`、应用包、IPC、ApplicationNodeCatalog 和 DAG 运行时。
- `LegacyProjectAdapter` 只管理旧 Project 文件、生命周期和回滚，不解释 AI 算法字段。

不得：

- include AI Decoder、Tracker、RKNN/TensorRT/QNN 或厂商 tensor 头文件。
- 读取 `aiobjdect2.cpp` 内部状态来决定业务协议。
- 在 DAG 运行时复制一套 AI 后处理。

### 9.2 AI 专项负责人

负责：

- `ai/domain`、AI Service、Result Bus、私有算法 Block、厂商 HAL。
- `InferenceResultEvent` 的事实语义和连续性。
- `LocalAiApplication`、现有完整方案兼容和 AI 安全消费者拆分。
- 一个可被通用层替换的 `MockActionSink`。
- `LegacyAiConfigAdapter` 负责旧 AI 字段到 `AiSessionSpec`/`LocalPolicySpec` 的强类型转换，不写 Project 文件。

不得：

- include MQTT、HTTP、Python Runtime、DAG JSON、GPO Driver 或 DeepEdge SDK。
- 在 AI 线程中直接发网络、录像、抓拍或业务 GPO。
- 为某个 DeepEdge 画布节点增加厂商或型号分支。

### 9.3 DeepEdge 平台负责人

负责：

- 画布、PlatformPlan、Graph Partitioner/Compiler、平台 Python Runtime。
- capability 驱动的节点展示和配置生成。
- SDK、自动重连、sequence gap 回调、operation 状态和统一错误。
- DE-2 受限应用包生成、签名和发布。

不得：

- 硬编码 major/minor、旧 topic、中文方案类型、本地路径或物理引脚。
- 假设所有型号支持 Tracker、Depth、Mask 或相机内 Python。
- 在图中指定未经 Catalog 允许的实际执行进程。

### 9.4 两位相机负责人只共同冻结八项

1. `InferenceResultEvent V1` 及 Detection/Tracking/Depth 扩展。
2. AI 会话 façade：create/start/stop/status/reconfigure/subscribe。
3. Action Sink：录像、抓拍、逻辑 GPO 请求和结果。
4. capability、统一错误和 `NOT_SUPPORTED` 语义。
5. runId、sequence、generation、取消和迟到结果规则。
6. 三种 messageClass 和队列语义。
7. Safety/Resource 声明和逻辑通道回落规则。
8. `AiSessionSpec V1`、`LocalPolicySpec V1` 的 Schema 引用、版本和所有权；不把旧 Project 字段作为共享合同。

不共同冻结 AI 内部目录、Decoder 接口、厂商 HAL、Python 实现、MQTT topic、`default.json` 字段或 DAG 调度器内部类。

并行开发时，通用负责人使用 `MockAiService`，AI 负责人使用 `MockActionSink`；双方通过 Schema、少量 contract header、Mock 和合同测试同步，不互相等待大规模源码搬迁。

---

## 10. DE-1：固定模板与两条近期闭环

### 10.1 阶段目标

在不建设相机内 Python 和任意 DAG 的前提下，同时交付：

1. `managed_local_ai`：DeepEdge 可视化配置后，相机运行现有完整本地方案。
2. `edge_ai_inference`：相机只发布 AI 事实，DeepEdge 判断后调用录像、抓拍和业务 GPO Action。

相机部署载荷在本阶段只有 `FixedSolutionSpec`，不发送 `nodes/links`；DeepEdge 平台侧仍可使用现有 PlatformFlow/Python/逻辑节点消费 AI Event 并调用 Action。也就是说，本阶段禁止的是“向相机下发 Device DAG”，不是禁止平台自己的业务流编排。

### 10.2 任务包

| ID | 负责人 | 任务 | 产物 | 前置依赖 |
|---|---|---|---|---|
| DE1-C01 | 三方合同小组 | 冻结 Action/Event/Error/capability/operation V1 | Schema、示例、Mock、版本规则 | 无 |
| DE1-C02 | 通用负责人 | 建立 Capability Discovery | 型号能力、限制、Node/Action 支持状态 | DE1-C01 |
| DE1-C03 | 通用负责人 | 实现 `FixedSolutionSpec` 校验与部署 façade | validate/stage/activate/rollback/status | DE1-C01 |
| DE1-C04 | 通用负责人 | 封装 `LegacyProjectAdapter` | Project 文件/生命周期、快照、停写启、失败恢复 | DE1-C03 |
| DE1-C05 | 通用负责人 | 建立媒体和逻辑 GPO Action façade | 幂等、ACK、权限、审计 | DE1-C01 |
| DE1-C06 | 通用负责人 | 建立 MQTT/WSS Action + Event Adapter | 出站同 Schema；入站录像/抓拍/逻辑 GPO 映射、ACK、幂等；独立有界队列 | DE1-C01/C05 |
| DE1-A01 | AI 负责人 | 从兼容 façade 发布 `InferenceResultEvent V1` | 事实事件和连续性字段 | DE1-C01 |
| DE1-A02 | AI 负责人 | 保持完整本地方案行为 | characterization/golden tests | 无 |
| DE1-A03 | AI 负责人 | 注册 `edge_ai_inference` 无副作用装配 | 不创建 LocalAiApplication | DE1-A01 |
| DE1-A04 | AI 负责人 | 实现 `LegacyAiConfigAdapter` | 旧 AI 字段转 `AiSessionSpec`/`LocalPolicySpec`，不管理 Project 文件 | DE1-C01 |
| DE1-P01 | DeepEdge | capability 驱动的固定模板画布 | `FixedSolutionSpec` 生成器 | DE1-C01/C02 |
| DE1-P02 | DeepEdge | 部署、状态、订阅和 Action SDK | 不含旧 topic/major/minor | DE1-C03/C05/C06 |
| DE1-P03 | DeepEdge | 注册 DE-1 平台业务节点 | AI Event、录像/抓拍/逻辑 GPO Action 接入现有 PlatformFlow/Python 运行时 | DE1-C01/DE1-P02 |
| DE1-Q01 | QA/集成 | AR950、D950 共用合同和故障测试 | 自动报告和差异清单 | 上述任务 |

### 10.3 可并行关系

```text
                 DE1-C01 合同冻结
                 /       |       \
        通用服务/Mock   AI/Mock   DeepEdge/Mock Server
                 \       |       /
                    DE1-Q01 集成
```

合同冻结后，AI 拆分不需要等待 MQTT、权限或部署服务完成；通用负责人也不需要等待 `aiobjdect2.cpp` 全量重构完成。

### 10.4 阶段门禁

- AR950、D950 运行同一套 Schema、Action/Event/Error 合同测试。
- 非法配置在停止当前方案前被拒绝；激活失败自动恢复旧方案。
- `managed_local_ai` 的检测、报警、GPO、录像、抓拍、UI 和旧协议与基线一致。
- `edge_ai_inference` 的本地 AI 驱动 GPO、LED、录像、抓拍、Operator 和业务报警日志计数全部为零。
- MQTT/WSS 慢消费者、断线和重连不阻塞采集或推理，内存和队列有界。
- sequence gap、runId/generation 切换和丢弃计数正确。
- DeepEdge 代码中不存在旧命令号、中文方案类型、旧 topic 和相机本地模型绝对路径。
- 平台侧至少一条“AI 事实 → 业务判断 → 录像/抓拍/逻辑 GPO Action”流程通过故障和幂等测试。
- 未通过门禁前不删除“异步推流检测”、旧配置和 `ObjectDect` façade。

---

## 11. DE-2：相机内受控 Python 应用

### 11.1 阶段目标

新增 `deepedge_custom_application`，通过 `CustomApplicationSpec` 将基础 AI 配置和签名 Python 包原子部署，固定拓扑为“AI 事实 → 一个受控 Python 应用 → 本地 Action Gateway”。本阶段解决部署、隔离、离线运行和低延迟自定义逻辑，仍不实现用户任意连线的 Device DAG。

### 11.2 任务包

| ID | 负责人 | 任务 | 产物 | 前置依赖 |
|---|---|---|---|---|
| DE2-C01 | 通用负责人 | `blockd` Supervisor 与独立权限 | 启停、健康、退避、资源上限 | DE-1 |
| DE2-C02 | 通用负责人 | UDS typed IPC 和自动 Bridge | 三类队列、版本握手、gap/ACK | DE1-C01 |
| DE2-C03 | 通用负责人 | Bundle Manager | 签名验证、staging、激活、回滚、重启恢复 | DE2-C01 |
| DE2-C04 | 通用负责人 | 本地 Action Client | 不走回环 MQTT/HTTP | DE1-C05/DE2-C02 |
| DE2-C05 | 通用负责人 | 业务 GPO lease | 逻辑通道、TTL、冲突和回落 | DE1-C05 |
| DE2-C06 | 通用负责人 | `CustomApplicationSpec` 联合事务部署 | AI 配置、Bundle、Action 授权/默认策略和 lease 一起 stage/activate/rollback | DE2-C03/C04/C05 |
| DE2-A01 | AI 负责人 | 稳定 Detection/Tracking/Depth 输出 | 与 Python 无关的消息源 | DE1-A01 |
| DE2-A02 | AI 负责人 | 用 `MockSlowSubscriber` 验证结果总线门禁 | 任意慢订阅者不反压推理 | DE1-A01/共享背压合同 |
| DE2-P01 | DeepEdge | Python SDK 与应用模板 | typed handler、Action、health | DE2-C02/C04 |
| DE2-P02 | DeepEdge | Bundle 构建、签名和发布 | 可重复制品与兼容声明 | DE2-C03 |
| DE2-P03 | DeepEdge | 生成 `CustomApplicationSpec` | 基础 AI 配置、bundleRef、Action 权限/默认策略、资源和失败策略 | DE2-C06/DE2-P02 |
| DE2-Q01 | QA/安全 | crash/hang/OOM/断电/回滚测试 | 隔离与恢复报告 | 上述任务 |

### 11.3 数据限制

- 默认只传 Detection、Tracking、有限 Depth 事实和状态事件。
- 完整 Mask 走 Artifact；原始帧走媒体/抓拍服务；Tensor 永不进入 Python。
- 若业务需要平面拟合，必须在 DE-2 开始前单独冻结有界 `DepthPointSet` 或 `DepthFrameRef` 的尺寸、同步、频率、所有权和 capability。未冻结则该功能延期，不能临时把完整深度图塞进通用事件。

### 11.4 阶段门禁

- Bundle 安装、验证、激活、重启恢复和回滚可重复，失败不破坏旧应用。
- AI 配置、应用包、Action 授权和 GPO lease 联合激活；任一失败均恢复上一完整方案，不出现跨版本组合。
- Python 崩溃、死循环、OOM、日志爆量不影响 `camera`、AI 推理和 Safety Service。
- 平台断开后，已激活的本机应用按声明继续运行；未激活包不会自行启动。
- Python 只使用逻辑 GPO 通道，不知道引脚、极性或厂商对象。
- 动作都有 ACK/错误/幂等键；事实流 gap 可观察。
- 真机记录 Python 路径的 P50/P95/P99、队列、RSS、CPU、超时和回落结果。
- 不支持 `application.python` capability 的型号返回 `NOT_SUPPORTED`，不复制另一套降级实现。

---

## 12. DE-3：受限应用 DAG

### 12.1 阶段目标

DeepEdge 用户可以连接相机公开的白名单应用节点；全局图由 DeepEdge 编译和分区，相机只接收经过签名、版本化、可验证的 DevicePlan。固定方案和单 Python 应用逐步编译到同一运行时，避免长期双轨。

### 12.2 GraphSpec 最小模型

```text
GraphSpec
  graphId / version / contractVersion
  nodes[]: nodeId / nodeType / nodeVersion / config
  links[]: from(node,port) / to(node,port) / messageClass
  failurePolicy / resourceBudget / requiredCapabilities
```

平台图不提供 `runOn`。`ApplicationNodeCatalog` 决定允许的执行域，Graph Compiler 自动生成：

- `PlatformPlan`：平台 Python、跨设备状态和第三方集成。
- `DevicePlan`：相机服务节点、受控逻辑和获准 `blockd` 节点。
- `BridgeContract`：跨域 typed port、序列、队列、ACK 和重连语义。

### 12.3 任务包

| ID | 负责人 | 任务 | 产物 | 前置依赖 |
|---|---|---|---|---|
| DE3-C01 | 三方合同小组 | 冻结 NodeDescriptor/Port/GraphSpec V1 | Schema、类型兼容规则 | DE-2 |
| DE3-C02 | 通用负责人 | ApplicationNodeCatalog 及公开 AI 节点注册 | 白名单、版本、placement、capability；把稳定 AI façade 适配为应用节点 | DE3-C01/DE3-A01 |
| DE3-C03 | 通用负责人 | Graph Validator | 无环、端口、cardinality、config、安全、资源校验 | DE3-C01/C02 |
| DE3-C04 | 通用负责人 | Device Graph Compiler | DevicePlan、自动 IPC Bridge | DE3-C03 |
| DE3-C05 | 通用负责人 | Graph Executor | 有界调度、资源 lease、反向回滚、健康 | DE3-C04 |
| DE3-C06 | 通用负责人 | 整图原子部署 | stage/activate/rollback/重启恢复 | DE3-C05 |
| DE3-A01 | AI 负责人 | 提供原子 AI Service façade 描述 | 稳定端口、版本和 capability，不操作公开 Catalog | DE3-C01 |
| DE3-A02 | AI 负责人 | 提供资源/健康描述 | 会话配额、NPU 需求、状态 | DE3-C01 |
| DE3-P01 | DeepEdge | 全局 Graph Compiler/Partitioner | PlatformPlan/DevicePlan/BridgeContract | DE3-C01/C02 |
| DE3-P02 | DeepEdge | DAG 画布校验和诊断 | capability 过滤、编译错误定位 | DE3-P01 |
| DE3-M01 | 通用负责人 | DE-1/DE-2 兼容编译器 | 旧形态转标准 GraphSpec/DevicePlan | DE3-C05 |
| DE3-Q01 | QA/集成 | 图、资源、故障和等价测试 | 全系列合同矩阵 | 上述任务 |

### 12.4 调度和生命周期

- 首版只支持有向无环图；有状态反馈通过受控 `state_machine` 节点表达，不开放任意环。
- 启动按依赖从下游接收端准备到上游生产端，失败按已启动顺序反向停止。
- 每条边必须声明 messageClass、queueSize、deadline 和失败策略；禁止无界队列。
- 新图先完整校验和预申请资源；校验失败不影响当前运行图。
- 首版整图替换，不做局部节点热更新和运行时 C++ 插件。

### 12.5 阶段门禁

- 未知节点、类型不匹配、有环、端口数量错误、安全边违规和资源冲突在切换前拒绝。
- 新图失败时当前图不受影响或可恢复，不能留下半张活动图。
- AR/D 对同一 GraphSpec 生成语义一致的执行计划；硬件差异只体现为 capability 和资源值。
- 事实慢消费可按策略丢旧，Action 不得静默丢失。
- Python 节点异常只隔离节点或按声明停止业务图，不影响 Safety Service。
- DE-1、DE-2 的标准场景经新图运行时得到等价结果后，才允许退役相应旧编排路径。
- 仍禁止动态 `.so`、HAL 节点、厂商 tensor 和未经 capability 批准的原始帧输入。

---

## 13. 三阶段交付关系

| 能力 | DE-1 | DE-2 | DE-3 |
|---|---|---|---|
| 本地完整方案可视化配置 | 交付 | 保持 | 编译为标准图 |
| 端侧推理、平台业务判断 | 交付 | 保持 | 作为跨域图运行 |
| 相机内 Python | 不做 | 固定拓扑交付 | 成为白名单节点 |
| 任意应用节点连线 | 不做 | 不做 | 受限开放 |
| AI 内部算法 DAG 外放 | 不做 | 不做 | 仍不做 |
| `default.json`/旧命令 | Legacy Adapter | Legacy Adapter | 逐步退役 |
| 部署粒度 | `FixedSolutionSpec` | `CustomApplicationSpec`（AI 配置 + 单应用包原子部署） | 整图 |
| 多活动 AI 业务图 | 不做 | 不做 | ResourceCoordinator 验收后另开 |

禁止为了展示 DE-3 效果跳过 DE-1 的合同和 DE-2 的隔离。否则 DAG 只会把当前耦合放大到更多节点。

---

## 14. 跨仓和全型号策略

1. AR、D 两仓的 contracts、Mock、Schema 和合同测试保持相同相对路径与内容；第一阶段仍采用源码镜像，不引入公共子仓库。
2. 代表样板先做 AR950、D950；随后按 ProductProfile 验证 AR940、AR760、AR765、D940、D955。
3. 不支持的能力统一返回 `NOT_SUPPORTED`；平台按 capability 隐藏或禁用节点，不按型号名称硬编码。
4. Rockchip、NVIDIA、Qualcomm 的差异只进入 AI HAL、媒体 HAL、ProductProfile 和资源描述；Action/Event/GraphSpec 不出现 SoC 名称。
5. 两仓内容一致性检查只针对明确列入共享清单的文件；板级配置、打包、设备节点和厂商实现不做机械一致。

---

## 15. 统一验收矩阵

| 类别 | 必测内容 |
|---|---|
| 合同 | Schema 兼容、必填字段、未知字段、错误码、capability、版本协商 |
| 部署 | 预验证、staging、激活、超时、断电、回滚、重启恢复、幂等重试 |
| AI 连续性 | runId、sequence、generation、seek、迟到结果、drop count |
| 副作用 | `edge_ai_inference` 下 GPO/LED/录像/抓拍/Operator/业务日志全部为零 |
| 背压 | MQTT/WSS/UDS 慢消费者、断线、重连、队列满、平台进程停止 |
| 动作 | 有序、ACK、幂等、deadline、重复命令、拒绝时不部分执行 |
| Python | crash、hang、OOM、CPU 爆量、日志爆量、非法文件/设备访问、签名错误 |
| DAG | 有环、类型错、未知节点、资源冲突、非法 placement、安全边、半启动回滚 |
| 安全 | 平台、网络、Python、业务图全部失效时 Safety Service 和硬件默认态持续工作 |
| 性能 | FPS、P95/P99、RSS、CPU/NPU、队列深度相对各阶段基线 |
| 全系列 | 同一合同测试；差异只由 capability 表达；AR/D 共享文件内容一致 |

DE-1 延续 AI 专项性能门禁：同配置推理 FPS 和 P95 延迟相对基线回退不超过 5%，峰值 RSS 增量不超过 10%。DE-2、DE-3 需要分别建立 Python/IPC 和 DAG 调度基线，不能用功能可用替代性能验收。

---

## 16. 兼容、发布和退役规则

- 现有“异步推流检测”和 SVAP 暂时保持，统一放在 Legacy/Transport Adapter 后面；不与 `edge_ai_inference` 强行合并。
- 每个阶段保留方案级回滚开关：`legacy`、`service_fixed`、`blockd_fixed`、`restricted_dag`。
- 同一时刻只允许一个实现拥有某个业务动作，禁止新旧路径同时驱动 GPO 或录像。
- 没有 characterization、合同、故障和性能证据，不删除旧路径。
- 旧配置迁移必须可重复；同一输入多次转换得到相同语义结果。
- 新平台不得再生成旧命令和旧文件；兼容只在相机 Adapter 内收口，避免兼容债务反向扩散。

---

## 17. 本版默认裁决和进入研发前的产品确认

为使任务可以立即拆分，本文按以下默认值冻结；如产品决定不同，必须在对应阶段启动前修改合同和验收，不允许开发中口头变更：

1. **机械停机等安全输出**：归相机 C++ 安全闭环；Python 只允许普通业务 GPO。
2. **深度平面拟合**：DE-2 默认不承诺完整深度图；先单独定义有界 `DepthPointSet`/`DepthFrameRef`。
3. **DE-1 切换**：允许 Legacy Adapter 短时“停—写—启”，但必须预验证和失败回滚；允许中断时长由产品在实机基线后填写。
4. **并发**：DE-1/DE-2 单设备单活动 AI 业务方案。
5. **传输**：Schema 同时覆盖 WSS/MQTT；项目可排定先接其中一个 Adapter，但正式 DE-1 门禁要求两者语义一致。
6. **Python 包信任**：正式交付必须签名；仅 hash 的包只允许研发环境。

如果以上任一项被否决，受影响最大的是 DE-2 的安全/IPC 设计或 DE-1 的部署事务，应先修改本文再分派对应任务；AI 内部 Block/HAL 拆分仍可独立推进。

---

## 18. 完成定义

本专项不是以“画布上能连线”或“MQTT 能收到一条结果”为完成，而是满足以下结果：

1. DE-1 的两条近期闭环可独立部署、回滚、观察和验收。
2. DE-2 的 Python 自定义逻辑在相机内可控、可恢复、不可越权，故障不影响相机核心与安全服务。
3. DE-3 的用户自由度被限制在公开应用节点，AI 内部算法和厂商 HAL 不泄漏。
4. 三阶段使用同一 Action/Event、capability、错误和 operation 语义，不形成三套平台 SDK。
5. 通用模块化负责人和 AI 专项负责人能通过 Mock 并行开发，除七项冻结合同外不互相依赖内部实现。
6. AR、D 两仓和后续 NVIDIA、Qualcomm 设备继续使用相同的上层合同，芯片差异只扩展 HAL 与 ProductProfile。
