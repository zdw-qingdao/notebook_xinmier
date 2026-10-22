# 全系列相机功能模块定义与外部平台 Block 对接说明

> 文档定位：供两套相机项目、共享 Web UI 和外部“算法与相机管理平台”共同冻结业务模块、Action、事件和型号能力表达方式。<br>
> 正式范围：AR 系列项目的 AR950、AR940、AR760、AR765，以及 D 系列项目的 D940、D950、D955。<br>
> 当前代码证据以 AR950、D950 为代表样本；没有编译、部署或连接设备，不能由这两个样本推断其他五个型号已经通过。<br>
> Python Block 的编排在外部平台完成；DE-2 起，获准执行体才可下沉到相机内独立的 `blockd` 进程运行。相机提供稳定、可鉴权的服务能力，C++ 算法管线不动态加载外部代码。

AI 内部 C++ Block 与外部平台 Python Block 的边界、数据契约、“端侧AI推理”方案和 D950 首个迁移样板见 [全系列相机 AI 算法服务化与端侧推理 Block 重构实施说明](./全系列相机_AI算法服务化与端侧推理Block重构实施说明.md)。

与 DeepEdge 平台的最终逻辑 DAG、三种运行身份、三阶段任务和双负责人边界见 [DeepEdge 渐进式 DAG 适配与三阶段实施说明](./全系列相机_DeepEdge渐进式DAG适配与三阶段实施说明.md)。

## 1. 先冻结范围和分层

### 1.1 两套代码树不是两个型号

| 项目代码树 | 当前正式产品型号 | 硬件平台 / HAL 适配 |
|---|---|---|
| AR 系列项目 `camera2d-rk3588` | AR950、AR940、AR760、AR765 | AR950：RK3588；AR940：RK3576；AR760、AR765：RV1126B |
| D 系列项目 `safety-double-rk3588` | D940、D950、D955 | D940：RK3576；D950、D955：RK3588 平台族，D955 另有 MCU/PWM 等板级差异 |

以上产品清单以当前顶层构建和打包入口为准。EX950、AR750/AR750B、D850 等名称虽然出现在历史配置或共享前端特性中，但当前不作为一级正式构建目标；是否仍需交付由产品确认。若以后加入正式清单，只新增 ProductProfile、HAL 适配和能力记录，不复制一套 Module、Action、权限或平台 Block。

共享 Web UI 的品牌、语言和客户包属于发行变体，不是相机型号，也不是硬件平台。发行变体可以决定某项已经实现的产品能力是否展示，但不能产生另一套 `moduleId`、`actionId`、用户组或 API Key 体系。

### 1.2 三份目录必须分开

| 目录 | 负责什么 | 不放什么 |
|---|---|---|
| Module Catalog | 稳定业务模块：名称、说明、Action、事件、是否可委派 | 产品型号列、芯片、GPIO 数量、端口默认值 |
| Action / Event Catalog | “做什么”的稳定契约、输入输出、风险、幂等和旧入口映射 | `AR950`、`D950`、`RK3588` 等型号或平台前缀 |
| ProductProfile / HAL Capability Matrix | 产品是否支持、成熟度、硬件限制、发行变体开放情况和适配状态 | 用户组是否允许使用 |

最终判断为：

```text
允许调用 =
    当前固件注册了 Module / Action
    AND ProductProfile 声明产品支持所需 capability
    AND 对应硬件平台的 HAL 适配可用
    AND 身份有效
    AND（Administrator 或用户组启用了该 moduleId）
```

这里必须区分：

- 产品或 HAL 不支持：`NOT_SUPPORTED`，不是权限不足。
- 未登录或身份失效：`UNAUTHENTICATED`。
- 产品支持，但当前用户组关闭模块：`FORBIDDEN`。
- “后端存在，待产品化”：只供内部联调，不向正式平台模板默认开放。

### 1.3 ProductProfile 的最小结构

Module 和 Action 目录不枚举型号。产品能力使用独立、可追加数据行：

```json
{
  "productId": "D950",
  "projectTree": "safety-double-rk3588",
  "platformId": "rk3588",
  "releaseVariant": "simmir-zh",
  "capabilities": {
    "media.whep": {"supported": true, "maturity": "production"},
    "io.gpi": {"supported": true, "limits": {"channels": 2}},
    "vision.depth": {"supported": true, "maturity": "backend_only"},
    "device.pairing": {"supported": true, "limits": {"peerCount": 1}}
  }
}
```

建议 `system.diagnostics` 提供 `device.capabilities.get`。平台只能根据实机返回决定是否展示 Block，不能根据型号字符串、共享 UI 特性集名或某个源码文件存在来猜功能。

## 2. 网络协议和统一入口

Action 表示“做什么”，协议只表示“怎样传输”。现有 URL、WebSocket major/minor、TCP 命令和 MQTT topic 只是兼容入口，不是长期业务契约。

| 通道 | 适合承载 | 不应承载 |
|---|---|---|
| HTTPS | 查询、短命令、配置读写、创建异步任务、能力发现 | 视频帧、高频连续事件 |
| WSS | 已认证事件订阅、状态变化、报警、异步任务进度 | 公开完整配置、继续新增页面专属命令分支 |
| MQTT over TLS | 相机主动连接平台、状态上报、事件通知、断线恢复 | 匿名 Broker 指令、绕过相机 PolicyGate 的旧 topic |
| RTSP / WHEP / WebRTC | 实时音视频数据面 | 用户、配置、权限和设备管理 |
| Artifact HTTPS | 模型、固件、图片、录像和日志等大文件 | 低时延控制 |
| 内部 IPC | 相机服务、HAL、驱动或受控本机进程之间通信 | 直接对外暴露 |
| Legacy HTTP / WS / TCP | 有期限的现有客户端兼容 | 新业务长期主契约 |

Transport/Auth 是服务层入口，不单独算第五个业务层。它只负责身份解析、Action 路由、权限、限流、审计和协议适配。

### 2.1 当前入口到语义模块的映射

端口级模块只控制兼容通道是否可用，不能一次放开通道承载的全部业务：

| 当前入口 | 首要检查 | 业务检查 |
|---|---|---|
| HTTP/HTTPS 80/443 | 身份和路由 Action | 目标 Action 所属业务模块 |
| WebSocket 1700 | 握手身份与订阅 Action | 每类事件所属业务模块 |
| RTSP 554、WHEP/WebRTC | 媒体会话身份 | `media.live` |
| JPEG 图像 TCP | `integration.image_tcp` | 预览检查 `media.live`；抓拍检查 `media.capture_record` |
| SDK TCP 9000 | `integration.sdk9000` | Video、AI、ROI、Snapshot 分别检查对应业务模块 |
| TCP 6002 | `integration.tcp6002` | 每条命令解析后再检查实际业务模块 |
| MQTT/SVAP | `integration.mqtt` | Topic 映射 Action 后检查实际业务模块 |
| UART/Modbus | `integration.protocols` | 入站业务指令映射 Action 后检查实际业务模块 |

用户组关闭模块只拒绝该身份的连接、请求、订阅或数据，不全局停止监听器。设备级“是否启动某服务”是 Administrator 管理的整机配置。

## 3. 芯片无关的 Module / Action Catalog

下表的 `requiredCapabilities` 是产品和 HAL 的前置条件，不是用户权限。`当前代码树证据` 只说明已在某代码树看到实现；`待逐型号验证` 是进入正式 ProductProfile 前必须完成的工作。

### 3.1 媒体与相机基础能力

| moduleId | 用途 | 建议 Action / 事件 | 协议 | requiredCapabilities | 当前代码树证据 | 待逐型号验证 |
|---|---|---|---|---|---|---|
| `media.live` | 实时预览和媒体会话 | `media.live.describe`、`media.live.status.get`；`media.live.state.changed` | HTTPS/WSS；RTSP/WHEP/WebRTC 数据面 | `media.capture`、至少一种实时编码/输出能力 | 两代码树均有实时媒体；AR950、D950 样本有 WHEP | 七型号实际流协议、编码、分辨率、帧率和鉴权 |
| `media.capture_record` | 抓拍、录像启停和录像参数 | `media.snapshot.create`、`media.recording.start/stop`、`media.recording.config.get/update`；`media.recording.state.changed` | HTTPS/WSS；Artifact HTTPS | `media.snapshot`、`media.recording` | 两代码树代表样本均有抓拍/录像 | 各 HAL 的编码器、存储路径、帧率限制和掉电行为 |
| `media.archive` | 查询、下载、删除图片和录像 | `media.artifact.list/get/delete`、`media.artifact.export.create`；`media.artifact.created` | HTTPS / Artifact HTTPS | `storage.local` | 两代码树共享网页有媒体档案入口 | 七型号存储布局、容量、清理与断点下载 |
| `camera.imaging` | 曝光、增益、白平衡、方向、参数与标定 | `camera.imaging.get/update`、`camera.calibration.get/update`；`camera.imaging.changed` | HTTPS/WSS | `camera.sensor`、`camera.isp` | AR950、D950 样本后端均有参数入口 | RK3588、RK3576、RV1126B HAL 字段映射；每个产品的传感器/IQ限制 |

### 3.2 方案、视觉和 AI 能力

| moduleId | 用途 | 建议 Action / 事件 | 协议 | requiredCapabilities | 当前代码树证据 | 待逐型号验证 |
|---|---|---|---|---|---|---|
| `solution.manage` | 方案模板、实例、导入导出 | `solution.list/get/create/update/delete`、`solution.import/export`；`solution.changed` | HTTPS / Artifact HTTPS | `solution.storage` | 两代码树有方案管理实现 | 七型号配置格式、迁移与持久化 |
| `solution.run` | 方案启停、状态与通用异步任务 | `solution.start/stop/status.get`、`solution.job.create/cancel`；`solution.state.changed`、`solution.job.progress` | HTTPS/WSS/MQTT | `solution.runtime` | 两代码树有方案运行入口 | 资源上限、互斥和重启恢复 |
| `solution.async_stream` | 异步推流检测方案 | `solution.async_stream.get/update`、`solution.async_stream.job.create/cancel`；`solution.async_stream.progress/result` | HTTPS/WSS/MQTT | `solution.async_stream` | AR950、D950 代表样本有对应入口/特性 | 七型号是否生产开放、输入格式和并发限制 |
| `solution.threshold` | 门限、tripwire、方向与结果 | `solution.threshold.get/update`；`solution.threshold.result/alarm` | HTTPS/WSS/MQTT | `solution.threshold` | AR 代表样本确认开放；D 代码树有共享方案代码 | 每个 ProductProfile 的开放状态和结果字段 |
| `solution.operator_debug` | 单算子配置、单次运行和项目输出 | `solution.operator.get/update`、`solution.operator.run_once`、`solution.operator.output.get`；`solution.operator.progress/completed/failed` | HTTPS / Artifact HTTPS / WSS | `solution.operator_debug` | AR950 代表样本代码存在 | AR940/760/765 是否支持；是否仅研发模式；D 系列逐型号确认 |
| `vision.roi` | ROI 图形和检测区域 | `vision.roi.get/update/clear`；`vision.roi.changed` | HTTPS/WSS | `vision.roi` | AR950 开放；D950 核心后端存在、部分发行变体开放 | 七型号坐标系、数量、形状和发行变体状态 |
| `vision.mosaic` | 马赛克区域绘制和应用 | `vision.mosaic.get/update/clear`；`vision.mosaic.changed` | HTTPS/WSS | `vision.mosaic` | AR950 开放；D950 后端存在、部分发行变体开放 | 七型号渲染路径、区域上限、量产开放状态 |
| `vision.mask` | 分割 Mask 与结果叠加 | `vision.mask.get/update/clear`、`vision.mask.display.update`；`vision.mask.changed` | HTTPS/WSS | `vision.segmentation_mask` | D950 后端存在，部分品牌发行变体开放 | 全系列逐型号核实；品牌开关不得充当硬件能力 |
| `ai.detection` | 通用目标检测和 ROI 计数 | `ai.detection.config.get/update`；`ai.detection.result`、`ai.detection.count.changed` | HTTPS/WSS/MQTT | `ai.inference`、`ai.object_detection` | 两代码树代表样本均有通用检测 | RKNN/模型适配、吞吐、结果字段与每型号上限 |
| `ai.disappearance` | 禁止消失区域和目标消失报警 | `ai.disappearance.config.get/update`；`ai.disappearance.alarm/cleared` | HTTPS/WSS/MQTT | `ai.object_detection`、`vision.roi` | AR950、D950 样本均有实现 | 七型号稳定性；V1 是否并入 `ai.detection` 用户开关由产品冻结 |
| `ai.depth` | 深度估计、深度检查与结果 | `ai.depth.config.get/update`；`ai.depth.result/alarm` | HTTPS/WSS/MQTT | `ai.depth_estimation` | D950 后端存在，UI 默认未开 | 七型号逐一声明；未完成产品化保持 `backend_only` |
| `ai.models` | 模型列表、上传、删除、校验和切换 | `ai.model.list/get/upload/delete/activate`；`ai.model.operation.progress`、`ai.model.activated` | HTTPS / Artifact HTTPS / WSS | `ai.model_management` | 两代码树代表样本有模型入口 | 各平台模型格式、签名、空间和回滚 |
| `ai.simulation` | 文件模拟推理和播放控制 | `ai.simulation.job.create/status.get/cancel`、`ai.simulation.playback.control`；`ai.simulation.progress/completed/failed` | HTTPS / Artifact HTTPS / WSS | `ai.simulation`；播放细控另需 `ai.simulation_playback_control` | AR950 有模拟推理/监控；D950 有播放细控差异 | 七型号分别声明基础模拟与播放细控 capability |
| `ai.evidence` | AI 证据数据管理 | `ai.evidence.list/get/import/export/delete/promote`；`ai.evidence.changed/import.progress` | HTTPS / Artifact HTTPS / WSS | `ai.evidence_management` | D950 代表样本有独立服务和 HTTP 路由 | D940/D955 与 AR 系列逐型号确认；数据生命周期验收 |
| `ai.evaluation` | 真值标注、模型评估任务和结果 | `ai.evaluation.job.create/status.get/cancel`、`ai.evaluation.ground_truth.get/update`；`ai.evaluation.progress/completed/failed` | HTTPS / Artifact HTTPS / WSS | `ai.model_evaluation` | D950 代表样本有独立服务和 HTTP 路由 | D940/D955 与 AR 系列逐型号确认；资源限制和取消语义 |
| `ai.target_tracking` | 目标跟踪和轨迹事件 | `ai.tracking.config.get/update`；`ai.tracking.result` | HTTPS/WSS/MQTT | `ai.target_tracking` | AR950 代表样本开放；D950 发行配置未开 | 其余六型号 ProductProfile 逐一确认 |
| `safety.pose_guard` | 旋转、姿态、遮挡等本机安全监测 | `safety.pose_guard.config.get/update`、`safety.pose_guard.baseline.capture`；`safety.pose_guard.alarm/cleared` | HTTPS/WSS/MQTT；内部 IPC | `sensor.pose` 或等价视觉监测能力 | 两代码树代表样本有守卫实现；D950 有姿态/遮挡扩展 | 七型号传感器、标定、失效安全和断网验收 |

### 3.3 IO、通信和外部系统集成

| moduleId | 用途 | 建议 Action / 事件 | 协议 | requiredCapabilities | 当前代码树证据 | 待逐型号验证 |
|---|---|---|---|---|---|---|
| `io.gpio` | GPI 状态、GPO 输出和输入事件 | `io.gpi.state.get`、`io.gpo.set/pulse`；`io.gpi.changed`、`io.gpo.changed` | HTTPS/WSS/MQTT；HAL 本机调用 | `io.gpi`、`io.gpo` | 两代码树有 GPIO；D950 样本为 2 GPI/3 GPO | 七型号通道数、极性、PWM/MCU 后端和安全默认态 |
| `integration.protocols` | TCP Client/Server、UDP、Modbus TCP/RTU、HTTP、UART Raw 端点 | `integration.endpoint.list/get/create/update/delete/test`；`integration.endpoint.state.changed` | HTTPS 配置；各协议数据面 | 对应 `transport.*` 和 `hal.uart/rs485` | 两代码树有通用协议实现 | 各平台设备节点、协议组合和入站身份方式 |
| `integration.mqtt` | MQTT Broker、Topic、上报和指令 | `integration.mqtt.config.get/update/test`；`integration.mqtt.state.changed` | HTTPS；MQTT over TLS | `transport.mqtt` | 两代码树有 MQTT/SVAP 路由 | 七型号 TLS、Broker 身份、Topic ACL 和离线队列 |
| `integration.tcp6002` | 现有 TCP 6002 兼容通道管理 | `integration.tcp6002.config.get/update`、`integration.tcp6002.status.get` | HTTPS；Legacy TCP | `legacy.tcp6002` | AR950 默认开；D950 代码存在但部分发行版关 | 七型号端口、默认状态、客户端依赖和认证方案 |
| `integration.sdk9000` | SDK TCP 9000 兼容通道 | `integration.sdk9000.config.get/update`、`integration.sdk9000.session.list/close` | HTTPS；Legacy TCP | `legacy.sdk9000` | AR950、D950 代表样本均有服务 | 七型号订阅类型、默认订阅、认证与背压 |
| `integration.image_tcp` | 预览/抓拍 JPEG 兼容通道 | `integration.image_tcp.config.get/update`、`integration.image_tcp.session.list/close` | HTTPS；Legacy TCP | `legacy.image_tcp`、对应媒体 capability | AR950 样本为 5566/5588；D950 样本端口组合不同 | 端口不能写进业务契约；七型号返回实际端点和用途 |
| `integration.fixed_report` | 固定格式二进制上报 | `integration.fixed_report.config.get/update`、`integration.fixed_report.status.get`；`integration.fixed_report.state.changed` | HTTPS；TCP 二进制数据面 | `integration.fixed_binary_report` | D950 代表样本存在；AR950 未见对应服务 | 七型号逐一确认，不能把“D950 特有”编码进 ID |
| `storage.ftp` | FTP 配置、测试、队列和上传状态 | `storage.ftp.config.get/update/test`、`storage.ftp.queue.list/retry`；`storage.ftp.transfer.changed` | HTTPS；FTP/FTPS/SFTP | `transport.ftp` 或后续安全替代能力 | 两代码树共享 UI 有 FTP 管理 | 七型号安全协议、缓存路径、重试和凭据保护 |
| `device.pair` | 多节点产品的配对关系、对端状态和受控配置同步 | `device.pair.status.get`、`device.pair.project.sync`；`device.pair.state.changed`、`device.pair.sync.completed/failed` | HTTPS/WSS；设备间认证通道 | `device.pairing`、`project.config_sync` | D950 代表样本有 1.202/1.203 和项目配置同步 | D940/D950/D955 逐型号确认是否开放；AR 系列通常为不支持；节点数和角色进入 capability limits |

### 3.4 系统、诊断和管理能力

| moduleId | 用途 | 建议 Action / 事件 | 协议 | requiredCapabilities | 当前代码树证据 | 待逐型号验证 |
|---|---|---|---|---|---|---|
| `system.settings` | 设备名称、时间、网络等全局参数 | `system.settings.get/update`、`system.network.get/update`、`system.time.get/update`；`system.settings.changed` | HTTPS/WSS | `system.settings` | 两代码树代表样本有设置入口 | 七型号字段、网络后端和持久化路径 |
| `system.diagnostics` | 设备信息、能力发现、健康、日志和审计导出 | `device.info.get`、`device.capabilities.get`、`system.health.get`、`system.log.list/export`、`audit.list/export`；`system.health.changed` | HTTPS / Artifact HTTPS / WSS | `system.diagnostics` | 两代码树有日志/状态基础 | 七型号指标可用性、日志路径和隐私过滤 |
| `system.maintenance` | 重启、固件/Web UI 更新和 HTTPS 传输证书维护 | `system.reboot`、`system.firmware.upload/install`、`system.webui.install`、`system.https_certificate.update`；`system.operation.progress/completed/failed` | HTTPS / Artifact HTTPS / WSS | 对应 `system.*` 维护 capability | 两代码树有维护入口；D950 样本有 HTTPS 证书上传特性 | 七型号升级格式、签名、恢复、分区和回滚 |

以上共 33 个候选目录项。`solution.operator_debug` 是否进入正式客户目录、`ai.disappearance` 是否与 `ai.detection` 共用一个 V1 用户开关，需要产品冻结。Module 的数量不等于网页一级菜单数量，也不等于平台 Python Block 数量。

`access.manage` 是保留的根管理域，不放入普通角色的功能模块选择框，也不作为平台业务能力展示。用户/组/API Key、身份信任、安全/审计策略、恢复出厂、维护 Shell 和危险清理等可提权或绕过策略的 Action 固定归此域，只允许完整 Administrator 操作。

## 4. ProductProfile / HAL Capability Matrix

### 4.1 七个正式型号的最小基线

下表只冻结平台和验收维度，不提前宣称全部模块已支持。所有“待盘点”都必须通过构建配置、静态代码、最终固件和真机补证。

| productId | projectTree | platformId / HAL | 当前代表性结论 | 必须补齐的验证 |
|---|---|---|---|---|
| AR950 | AR 系列 | RK3588 | 本轮主要 AR 代码样本；WHEP、ROI、马赛克、跟踪、模拟推理、6002/9000/图像 TCP 等已有入口 | 全量 Action 映射、鉴权、端口和实机合同测试 |
| AR940 | AR 系列 | RK3576 | 正式构建目标，复用共享业务代码 | 产品能力全盘点；RK3576 媒体/ISP/GPIO/存储真机回归 |
| AR760 | AR 系列 | RV1126B | 正式构建目标，存在板级和路径差异 | RV1126B 媒体、AI、GPIO 极性、持久化和协议真机回归 |
| AR765 | AR 系列 | RV1126B | 正式构建目标，与 AR760 同平台但板级能力不能假定相同 | 单独验证传感器、分辨率、GPIO、ISP、前端能力和持久化 |
| D940 | D 系列 | RK3576 | 正式构建目标，业务代码与 D 系列共享 | 产品能力全盘点；构建入口、RK3576 HAL 和双节点能力真机确认 |
| D950 | D 系列 | RK3588 | 本轮主要 D 代码样本；证据/评估、深度、Mask、固定上报、pair 等有后端证据 | 区分 `production`、发行变体开放和 `backend_only`；两节点验收 |
| D955 | D 系列 | RK3588 + MCU/PWM 板级差异 | 正式构建目标，不能视为 D950 别名 | MCU/PWM、GPIO、恢复、资源服务、前端能力和 pair 开放状态 |

### 4.2 三类 HAL 的真机回归

| HAL 平台 | 首批真机覆盖 | 必测差异 |
|---|---|---|
| RK3588 | 至少 AR950、D950，并单独覆盖 D955 板级差异 | ISP/编码/RKNN、GPIO/PWM/MCU、升级恢复、存储、媒体端口 |
| RK3576 | AR940、D940 | ISP/编码、GPIO/UART、文件路径、启动与打包集成 |
| RV1126B | AR760、AR765 均需覆盖 | 传感器/IQ、分辨率、媒体管线、GPIO 极性、存储路径 |

同平台不等于同产品。七个正式型号都必须运行共享 Action/权限合同测试；HAL 真机矩阵用于补充硬件和板级差异，不能用一个 RK3588 样机替代所有 RK3588 产品验收。

### 4.3 发行变体规则

- 品牌、语言、客户 UI 包记录在 `releaseVariant`，不进入 `productId`。
- 发行变体只能在产品已实现的能力范围内决定是否开放；不能伪造 HAL 不支持的能力。
- Web UI 最终读取相机返回的“产品支持模块 + 当前身份允许模块”，不以共享前端特性集名代替实机能力。
- 后端存在但 UI 未开放的能力使用 `maturity=backend_only`；完成稳定接口、权限、UI 和验收后才能转 `production`。

## 5. AR950 / D950 代表样本证据

本节仅保留当前审查的可追溯证据，用来启动全型号盘点；它不表示另外五个型号继承相同产品能力。

路径缩写：

- `AR_ROOT=/home/watermirror/camera2d-rk3588`
- `D_ROOT=/home/watermirror/safety-double-rk3588`
- `UI_ROOT=/home/watermirror/xme-app-event-cam-2d-self-setup-web-ui-201x`

1. AR 项目正式构建目标定义在 `AR_ROOT/CMakeLists.txt:4-37`，包含 AR950、AR940、AR760、AR765。
2. D 项目正式打包型号定义在 `D_ROOT/xbuild.sh:359-367`、`:470-494`，包含 D940、D950、D955。
3. D950 当前权限类型只有 Public、Authenticated、Admin：`D_ROOT/tools/auth/auth_types.h:12`；API Key 记录没有模块集合：`D_ROOT/tools/auth/api_key_store.h:8`。AR 项目对应文件仍需纳入全型号对照。
4. 共享 UI 当前角色常量仍是固定角色：`UI_ROOT/src/global/app-constants/_user-roles.js:7`。
5. D950 HTTP 鉴权编译选项默认关闭：`D_ROOT/CMakeLists.txt:92`；路由位于 `D_ROOT/tools/auth/http_auth_routes.cpp:10`。两代码树及七型号最终构建参数都要验证，不能只据 D950 推断。
6. D950 WS 匿名白名单和粗角色处理位于 `D_ROOT/tools/auth/auth_gateway.cpp:12`；现有审计 Action 映射起点位于 `D_ROOT/tools/auth/auth_audit.cpp:133`。
7. D950 WHEP 路由位于 `D_ROOT/tools/auth/http_auth_routes.cpp:64` 和 `D_ROOT/cam/httpserver/httpserver.cpp:3711`；RTSP 样本存在未启用认证的路径：`D_ROOT/cam/rtspserver/camrtsp.cpp:135`。
8. TCP 6002 样本位于 `D_ROOT/cam/communication/communication.cpp:55`、`:295`；AR950 默认开关样本位于 `AR_ROOT/package/www/www-simmir/json/ui.json:32`。
9. SDK 9000 命令和默认订阅样本位于 `D_ROOT/cam/communication/SdkTcpServer.h:4`、`D_ROOT/cam/communication/SdkTcpServer.cpp:170`、`:291`。
10. AR950 预览图 5566、抓拍图 5588 和 SDK 9000 的创建位于 `AR_ROOT/cam/communication/communication.cpp:304`；D950 图像 TCP 创建从 `D_ROOT/cam/communication/communication.cpp:173` 开始，说明端口属于 ProductProfile/兼容入口，而不是业务 Action。
11. D950 MQTT/SVAP 路由位于 `D_ROOT/cam/communication/communication.cpp:518`；通用协议枚举位于 `D_ROOT/tools/ethclass/ethdefinition.h:25`。
12. D950 固定格式上报位于 `D_ROOT/cam/communication/FixedReportServer.h:18` 和 `D_ROOT/cam/communication/communication.cpp:72`、`:228`。
13. D950 配对命令 1.202/1.203 位于 `D_ROOT/cam/setting/jsoncmddef.h:143`，处理位于 `D_ROOT/cam/handlecmd/camerabase_handlecmd.cpp:3137`；当前项目配置同步位于 `D_ROOT/cam/configsync/configsync.h:37`、`D_ROOT/cam/configsync/configsync.cpp:125`。
14. D950 Mask 位于 `D_ROOT/cam/camera/mask_overlay_renderer.h:4`、`D_ROOT/cam/aiobjdect/aiobjdect2.cpp:2071`；深度位于 `D_ROOT/cam/aiobjdect/depth_inspector.h:28`、`D_ROOT/cam/aiobjdect/aiobjdect2.cpp:1381`。
15. D950 AI 证据和评估服务位于 `D_ROOT/cam/airaw/ai_evidence_service.h:4`、`D_ROOT/cam/model_evaluation/model_evaluation_service.h:26`，HTTP 路由位于 `D_ROOT/cam/httpserver/ai_simulation_http.cpp:1838`。
16. AR950、D950 共享 UI 产品特性样本位于 `UI_ROOT/专用于研发阶段的工具集/javascript-本项目专用工具集/公共类型定义集-与-公共常量集/_2-诸发行版之系统特性集.ts:205`、`:279`。这只是迁移证据，不能充当全系列 ProductProfile。

## 6. 平台 Python Block 与相机能力的关系

本节的 Python Block 由外部平台编排；DE-1 在平台运行，DE-2 起获准执行体才可下沉到相机内独立的 `blockd` 进程。相机内部将预处理、推理、decoder、ROI、跟踪和深度验证实现为强类型 C++ Block，第一阶段只允许经验证的固定管线模板，不由外部 Block manifest 动态加载代码进入 C++ 管线或组装任意管线；Python Block 只通过公开消息消费结构化结果并调用服务层。端侧推理的芯片实现统一隔离在 `cam/ai/hal/inference/<vendor>/`，上层 Block、Service 和 Event 契约不区分 Rockchip、NVIDIA 或 Qualcomm。

必须维护两个互不混用的注册表：AI 负责人维护私有 `AlgorithmBlockRegistry`，通用模块化/DeepEdge 负责人维护公开 `ApplicationNodeCatalog`。DeepEdge 最终只自由连接后者；整个 AI 会话在外部图中是原子服务节点，内部 Preprocess、Inference Backend、Decoder、ROI、Tracker、Depth 和厂商 HAL 不因 C++ Block 化而自动开放。

### 6.1 四层边界

```text
外部平台应用层
  Python Block、业务规则、状态机、任务调度、客户工作流
                       │ 调用 Action / 订阅事件
                       ▼
相机服务入口（Transport/Auth，属于服务层边界）
  HTTPS / WSS / MQTT / 媒体会话 / 兼容 TCP
  身份、Action 路由、权限、限流、审计、协议适配
                       │
                       ▼
相机服务层
  媒体、方案、AI、ROI、GPIO、通信、配置、诊断等芯片无关服务
                       │
                       ▼
HAL 层
  统一相机、ISP、UART、GPIO、存储等接口，屏蔽平台和板级差异
                       │
                       ▼
驱动层
  SoC、MCU、传感器、执行器、通信芯片和寄存器操作
```

平台 Block 不直接调用 HAL/驱动，也不依赖某型号的 WS major/minor、端口或线程对象。

### 6.2 平台 Block 最小契约

```yaml
blockType: camera.gpo.pulse
displayName: GPO 脉冲输出
version: 1.0.0
inputSchema:
  trigger: boolean
configSchema:
  channelId: string  # 例如 business_alarm_1；不是物理 GPO index
  durationMs: integer
outputSchema:
  accepted: boolean
requiredModules:
  - io.gpio
requiredCapabilities:
  - io.gpo
actions:
  - io.gpo.pulse
events: []
```

- DE-1/DE-2 的 `blockType` 由平台保持稳定；DE-3 提升为公开 `nodeType` 后，其版本、端口和配置 Schema 属于平台与相机共同的应用节点合同。
- `requiredModules` 用于当前身份权限检查。
- `requiredCapabilities` 用于产品和 HAL 支持检查。
- `actions/events` 只写稳定业务契约，不写原始 URL、命令号或产品型号。

### 6.3 首批平台 Block 候选

| blockType | 类型与用途 | requiredModules | requiredCapabilities |
|---|---|---|---|
| `camera.event.detection` | 事件：目标检测结果 | `ai.detection` | `ai.object_detection` |
| `camera.event.disappearance` | 事件：目标消失报警 | `ai.disappearance` | `ai.object_detection`、`vision.roi` |
| `camera.event.pose_guard` | 事件：姿态/遮挡报警 | `safety.pose_guard` | `sensor.pose` 或等价视觉能力 |
| `camera.event.gpi` | 事件：GPI 状态变化 | `io.gpio` | `io.gpi` |
| `camera.event.solution_state` | 事件：方案状态 | `solution.run` | `solution.runtime` |
| `logic.condition` | 纯逻辑：条件分支 | 无 | 无 |
| `logic.boolean` | 纯逻辑：与/或/非 | 无 | 无 |
| `logic.threshold` | 纯逻辑：数值门限 | 无 | 无 |
| `logic.debounce` | 纯逻辑：去抖/连续次数 | 无 | 无 |
| `logic.delay_timer` | 纯逻辑：延迟/超时/定时 | 无 | 无 |
| `logic.state_machine` | 纯逻辑：有限状态机 | 无 | 无 |
| `camera.action.snapshot` | 动作：抓拍 | `media.capture_record` | `media.snapshot` |
| `camera.action.recording` | 动作：录像启停 | `media.capture_record` | `media.recording` |
| `camera.action.gpo` | 动作：GPO 设置/脉冲 | `io.gpio` | `io.gpo` |
| `camera.action.solution_switch` | 动作：方案启停 | `solution.run` | `solution.runtime` |
| `camera.action.async_stream` | 动作：异步推流任务 | `solution.async_stream` | `solution.async_stream` |
| `camera.event.threshold` | 事件：门限结果/报警 | `solution.threshold` | `solution.threshold` |
| `camera.action.roi_update` | 动作：更新 ROI | `vision.roi` | `vision.roi` |
| `camera.action.pair_sync` | 动作：触发受控项目配置同步 | `device.pair` | `device.pairing`、`project.config_sync` |
| `integration.action.notify` | 动作：平台通知第三方系统 | 无 | 平台连接器能力 |

这 20 个候选足够打通首批流程。平台在展示和运行前同时检查 `requiredModules` 与 `requiredCapabilities`，不得将“产品不支持”显示成“用户无权限”。

### 6.4 必须留在相机本机的逻辑

以下逻辑不能依赖外部平台在线：

1. 视频采集、编码、实时推理、ROI/Mask 帧内处理和媒体会话。
2. 姿态、旋转、遮挡等安全监测，以及确定响应时间的 GPO 联动。
3. 看门狗、过温/存储故障保护、升级恢复、关键配置落盘和启动自检。
4. 网络中断仍必须执行的检测、报警和本地缓存。
5. 对声明 `device.pairing` 的多节点产品，设备间健康检查和本地配置同步最小闭环。

平台可以配置、观察和编排这些能力，但不应成为逐帧处理或安全动作的必经路径。

相机内 `blockd` 进程承载平台下发的自定义逻辑时，必须满足以下隔离约束：

1. 独立进程，崩溃、死循环或 OOM 只影响自身；采集、编码、推理、安全监测和看门狗不受影响。
2. 只能发送和接收消息，不允许访问 `/dev`、NPU SDK、寄存器或相机内部对象。
3. 有 CPU 份额、内存上限和单次处理超时；超限即终止并按退避重启。
4. 不消费原始图像帧；需要图像时只拿抓拍文件路径。
5. GPO 控制粒度是逻辑通道号、电平和保持时间，引脚映射、极性和失效安全默认态仍由 C++ 侧统一掌管。
6. 卡死判定基于“有待处理输入且节点长时间无进展”，不能只看进程是否存活。失效动作由方案配置声明为保持最后状态或主动置报警态。

## 7. Action、模块权限和能力的最小关系

用户组和 API Key 属于独立安全规划；对应文档当前工作区未提供，进入权限实施前需恢复或重新编制。本文只冻结 Module/Action/capability 与其对接边界。

Action 定义不保存 `models` 或 `supportedModels`：

```json
{
  "actionId": "media.snapshot.create",
  "moduleIds": ["media.capture_record"],
  "requiredCapabilities": ["media.snapshot"],
  "risk": "write",
  "legacyMappings": ["POST /legacy/snapshot", "WS 1.xxx"]
}
```

产品支持情况由 ProductProfile 独立回答；用户组只回答是否允许模块。兼容通道也不能例外：SDK 9000、TCP 6002、图像 TCP 或 MQTT 命令均先映射 Action，再检查通道模块、业务模块和 capability。未知或没有映射的命令在强制鉴权后默认拒绝并审计。

## 8. 多人可并行的近期任务

### 8.1 公共目录与接口映射

负责人建议：公共 API/后端 1 名，两套代码树各 1 名盘点负责人，产品/HAL 1 名协调人。

- 冻结芯片无关的 Module、Action、Event 和 capability 命名规则。
- 从两代码树导出全部 HTTP、WS、TCP、MQTT、RTSP/WHEP、文件和设备间入口。
- 每个入口填写 `actionId`、`moduleId`、`requiredCapabilities`、项目代码树、产品 Profile、平台适配、当前鉴权和替代接口。
- 首批用 AR950、D950 代表样本补齐细节，同时并行盘点另外五个正式型号，不能把样本结论直接复制。
- 未映射 Action 默认拒绝并审计；不先重写算法或媒体实现。

交付物：公共 Catalog、Legacy 映射表、七型号 ProductProfile、HAL capability matrix、缺口清单。

### 8.2 Web UI 与权限联动

- 页面只读取“产品支持模块 + 当前身份允许模块”。
- 品牌和语言发行变体只影响资源与明确的产品开放状态，不形成新 moduleId。
- 后端所有协议入口执行同一 Action 校验；网页隐藏不能替代后端拒绝。
- 新建用户组默认全选当前产品支持的可委派业务模块；高风险可委派模块标风险并二次确认，不擅自默认关闭。

### 8.3 平台 SDK 与首批 Block

- 先用 Mock 实现能力发现、Action 调用、事件订阅、统一错误和重连。
- 先打通检测事件、条件/去抖、抓拍、录像、GPO、方案切换和外部通知。
- 平台按 capability 和 maturity 过滤 Block；`backend_only` 不默认面向客户。
- 媒体数据继续走 RTSP/WHEP/WebRTC，不搬入业务事件通道。

## 9. 验收标准和风险

### 9.1 合同测试

- 七个正式产品 ID 都能返回正确的 `productId`、`platformId`、`releaseVariant` 和 capability。
- 七型号运行同一套 Action、401/403、用户组、API Key、事件过滤和旧入口合同测试。
- RK3588、RK3576、RV1126B 三类 HAL 均完成真机回归；AR760/AR765、D950/D955 的板级差异分别验证。
- 新增型号只允许新增 ProductProfile、HAL 适配和 capability 数据，不修改共享 Action 权限语义。
- 不支持能力返回 `NOT_SUPPORTED`；用户无权返回 `FORBIDDEN`。
- 同一 Action 从不同协议进入时，身份、权限、错误和审计一致。
- 多节点产品被识别为多个设备节点和一个拓扑关系；部分同步失败不会覆盖身份或密钥数据。
- 断开平台后，本机安全、媒体和已配置的关键联动仍工作。

### 9.2 主要风险

| 风险 | 控制 |
|---|---|
| 把代码树名或首批样本当成产品范围 | 产品清单和 ProductProfile 独立维护；所有正式型号进入合同测试 |
| 把型号、SoC 或端口写进业务 ID | CI 校验 ID 命名；差异放 capability、ProductProfile、HAL 或 legacyMappings |
| 同一硬件平台被误认为同一产品 | 同平台型号分别验收板级、传感器、GPIO、存储和发行能力 |
| 共享 UI 特性集或品牌包充当能力源 | 实机 capability 为准；UI 构建期开关只作迁移证据 |
| 代码存在即对外承诺 | 使用 `backend_only`；完成接口、权限、UI 和验收后才转 `production` |
| Legacy 入口绕过模块权限 | 所有入口进入同一 Action 网关；未知映射默认拒绝 |
| 平台承担帧级或安全闭环 | 确定性执行留在相机；平台负责配置、观察和非关键编排 |
| 一次重写全部接口 | 先 Catalog 和三个纵向样板，再按模块迁移并保留回滚 |

这套分离方式使 Module/Action 契约可以服务两套代码树和后续型号，同时把真正的芯片、传感器、板级和发行差异限制在 ProductProfile、HAL capability 和适配层中。
