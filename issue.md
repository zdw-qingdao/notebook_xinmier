
### YOLO 的 GPU 高级设置

- `device` 默认为 `auto`，也可以保存多个 `机器地址/GPU UUID` 作为候选列表。每个 YOLO 只从候选范围分配一张卡；同一 workflow 必须有共同允许的机器。旧单卡配置读取时会规范为候选列表。
- `num_gpus` 默认为 `auto`，手动份额范围为 `0.0001～1`。auto 当前沿用 `workflow_inference` 资源预设，保存配置时不将 auto 固化为数值。
- DeepStream 的合批身份不包含份额；同模型、兼容配置且候选卡交集非空的输入合批，合批设备范围取交集，每个实际 batch 取其中最大申请量。每路原始申请保留在已有 `input_list` 中，拆批或停止后重建时重新计算。
- Python YOLO 各自申请份额，解码沿用 `video_decode` 预设；任务把这些申请安排到同一机器的具体卡。模型使用对应卡的进程内编号，解码卡放在可见设备列表首位。
- Head 与 Worker 通过 `task_manager_3/gpu_resources.py` 启动 Ray，登记每卡自定义资源，原生 GPU 资源数量设为 0，避免两套分配同时记账。Task 表原有 `num_gpus` 仍表示申请总额；逐节点申请及本次分配保存于 `task_config`，无数据库结构变化。
- 普通 GPU 任务也复用同一按卡分配入口；资源不足时沿用现有队列等待、超时与清理机制。已有 batch 不因修改节点配置自动重启。
- 启用启动配置需要在维护窗口停止现有推理部署并重启 Ray、调度器及 API；仅同步源码不代表现有 Ray 任务已加载新实现。

## 19. 当前按卡 GPU 实现审查

本节记录当前工作区全部按卡 GPU 改动的实现链路、已知问题和替代方案。这里描述的是当前实现状态，不代表推荐长期保留该架构。

### 19.1 实现链路

当前方案没有使用 Ray 原生 `GPU` 资源表示显卡，而是在应用层重新实现了一套按卡资源系统：

1. `docker/supervisord.conf` 和 `docker/deploy_worker.sh` 不再直接执行 `ray start`，改由 `task_manager_3/gpu_resources.py` 包装启动。
2. 启动包装器通过 `nvidia-smi` 读取 GPU index、UUID 和名称，为每张卡注册一个容量为 `1.0` 的 `autopipe_gpu/<index>/<uuid>/<model>` 自定义资源，并强制传入 `--num-gpus=0`，关闭 Ray 原生 GPU 账本。
3. `RayClient.gpu_devices()` 从 Ray 节点自定义资源反向解析设备目录；Workflow API 将 `节点地址/GPU UUID` 暴露给前端。
4. YOLO 节点新增 `device` 和 `num_gpus` 高级参数。前端允许选择候选卡和 GPU 份额，后端负责格式校验。
5. `WorkflowManager` 在部署时选择一台机器，重写 YOLO inference 分组，并生成 `_gpu_node`、`_gpu_requests`。
6. Scheduler 读取自定义资源的可用快照，由 `allocate_gpus()` 在应用层执行逐卡、逐份额分配，并把结果写入任务的 `_gpu_allocation`。
7. `RayClient.create_runtime()` 使用所选自定义资源创建 placement group；Actor 自身声明 `num_gpus=0`，再手动设置 `CUDA_VISIBLE_DEVICES=<UUID 列表>` 和 `AUTOPIPE_GPU_ASSIGNMENTS`。
8. Python YOLO 通过 `model_device()` 将 UUID 映射为进程内 CUDA ordinal；DeepStream 固定使用进程内 `gpu-id=0`。
9. 资源监控、节点总量和 Task 表中的 `num_gpus` 再把各卡自定义资源汇总成一个兼容用的 GPU 总量。

因此，当前方案的正确性依赖下面这个全局约束：**所有 GPU 任务都必须经过 TaskManager 的自定义分配入口，且不能再直接使用 Ray 原生 `num_gpus` 调度。** 只要存在绕过该入口的 Ray Job、Task、Actor 或第三方组件，两套资源视图就可能不一致。

### 19.2 问题汇总

| 级别 | 问题 | 影响 |
| --- | --- | --- |
| 高 | 关闭了整个节点的 Ray 原生 `GPU` 资源 | 原生 `@ray.remote(num_gpus=...)`、Ray Train、Tune、Serve 以及依赖 `ray.get_gpu_ids()` 的代码无法正常获得 GPU；Ray Dashboard 和 autoscaler 也看不到真实 GPU 容量。 |
| 高 | 自定义资源与物理设备的关联只存在于应用代码中 | Ray 只预留字符串资源，不负责验证 `CUDA_VISIBLE_DEVICES` 是否与其对应；环境变量、资源 key 或分配结果任一处出错都可能使用错误显卡。 |
| 高 | 自动选卡在 Workflow 准备阶段提前固定机器 | `auto` 当前倾向于选择设备目录中的第一台机器，而不是任务真正开始时负载最低、资源可用的机器；该机器繁忙时，任务会等待，即使其他节点有空闲 GPU。 |
| 高 | 对全部 YOLO 强制使用同一台机器 | 当前在 `WorkflowManager._prepare_instances()` 中把 Python Workflow Actor 内的 YOLO、解码，以及已经拆成独立任务的 DeepStream YOLO 一起计算共同机器。实际上只有同一个 Python Workflow Actor 内的模型与解码必须同机；不同 DeepStream batch 可以独立调度。该约束会拒绝本可运行的跨机器候选配置，也会使不同 batch 无法根据实时容量选择各自的节点。 |
| 高 | 节点资源启动后是静态的 | Ray 不支持运行中修改节点资源容量。GPU 故障、维护或临时禁用后，自定义卡仍会留在 Ray 资源表中；真正移除仍需重启对应 Ray 节点。 |
| 高 | 设备身份包含易变的节点地址 | Workflow 保存的是 `<NodeManagerAddress>/<GPU UUID>`。IP 变化、节点重建或地址复用后，已有配置会过期；当前只校验字符串格式，没有在部署时明确报告“设备已不存在”。 |
| 高 | `auto` 份额按 API/调度进程本机的 GPU 型号解析 | `gpu_amount()` 复用 `get_gpu_device_name()` 的本机缓存，而不是最终目标卡型号；异构集群可能使用错误的资源预设。 |
| 高 | 应用层分配与 Ray 资源预留不是一个原子操作 | Scheduler 先读取可用快照并保存 `_gpu_allocation`，之后才创建 placement group。外部任务、并发 Scheduler 或状态变化可能使快照失效，造成长时间 pending、重试或队首阻塞。Ray 最终会阻止超卖，但应用层选择不一定仍然有效。 |
| 高 | CPU-only Head 存在启动回归 | Head 启动命令没有传 `--num-gpus=0` 时，包装器会无条件执行 `nvidia-smi`；没有 NVIDIA 驱动或设备的 Head 会直接启动失败。 |
| 中 | 普通多卡任务失去 Ray 原生语义 | fallback 会把 `num_gpus > 1` 拆成多个自定义卡并暴露 UUID 列表，但 Actor 对 Ray 声明的仍是 `num_gpus=0`，所以 `ray.get_gpu_ids()`、Ray Train device 初始化及第三方 Ray 集成得到的结果不正确。 |
| 中 | 同一 Actor 内只做“可见性”，没有组件级隔离 | Actor 能看到该任务分配到的全部显卡。某个模型或库如果默认使用首卡、初始化所有可见卡或忽略映射，会干扰同 Actor 内其他模型；每个节点的 `_device` 映射不是强隔离。 |
| 中 | 逐卡分配器是贪心算法 | `allocate_gpus()` 按候选数量和份额排序后选择第一张可用卡，不做完整的装箱或回溯；复杂候选范围下可能在存在可行解时仍返回不可分配。 |
| 中 | GPU 份额同时承担多种含义 | 同一个 `num_gpus` 同时用于调度容量、任务类型限额、监控和计费，但它既不限制显存，也不限制算力。两个 `0.5` 任务是否能安全共享一张卡取决于模型和显存，而不是资源值本身。 |
| 中 | Workflow 的其他资源没有按模型聚合 | 多个 Python YOLO 的 GPU 份额会求和，但 CPU 和内存仍来自单个任务默认值或 `video_decode` 预设，可能低估整个 Workflow Actor 的 CPU/内存需求。 |
| 中 | inference batch 使用最大份额而不是按实际负载建模 | 合批后只取各输入申请的最大值。它适合表达“共享一个模型实例”，但无法体现 stream 数、batch size 和吞吐增加带来的显存、算力变化。 |
| 中 | 混合版本/滚动升级不安全 | 集群中只要出现任意 `autopipe_gpu/` 资源，兼容汇总就会优先使用自定义资源并忽略原生 GPU 总量；未升级节点可能被遗漏，旧任务和新监控的口径也不同。 |
| 中 | 使用 Ray 私有或实验接口 | `ray._private.accelerators...` 和 `RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES` 不属于稳定公共契约，升级 Ray 时存在失效风险。 |
| 中 | NVIDIA 和完整 GPU UUID 被写死在协议中 | 设备发现依赖 `nvidia-smi`，校验要求 `/GPU-`，没有覆盖 AMD、Intel、MIG 标识、UUID 前缀、容器重编号和 `CUDA_VISIBLE_DEVICES` 特殊值。 |
| 中 | GPU 目录 API 暴露整个集群拓扑 | 任意有 Workspace 访问权的用户都能读取全部节点主机名、GPU index、型号和 UUID；当前没有 Workspace 级设备池或资源授权边界。 |
| 低 | 前端、业务编排和底层调度强耦合 | `device` 同时参与前端 widget、Workflow 校验、inference 合组、批次复用、Scheduler 分配和 CUDA 映射；以后扩展到其他模型或调度策略需要同时修改多层。 |
| 低 | 监控是兼容汇总而非 Ray 原生事实 | `RayClient` 合成 `GPU` 字段，State API 监控再解析自定义资源；混用原生和自定义资源时可能漏算或重复计算，其他直接读取 Ray 状态的工具不会得到相同结果。 |

### 19.3 当前实现缺少的关键验证

现有单元测试覆盖了候选卡、份额、分组和 UUID 到局部编号的纯逻辑，但以下场景仍需要真实环境测试：

- CPU-only Head 能否启动和加入集群；
- Head、Worker 混合升级或某个 Worker 未使用启动包装器；
- 真实多 GPU 节点上的 placement group、自定义资源和 UUID 形式 `CUDA_VISIBLE_DEVICES`；
- PyTorch、Ultralytics、DeepStream 是否都按预期使用进程内 ordinal；
- 一个 Actor 同时包含解码和多个 Python 模型、且分配到不同 GPU；
- 普通 `num_gpus=2` 任务及依赖 `ray.get_gpu_ids()` 的任务；
- GPU Worker 重启、IP 变化、设备消失、MIG 重配和 GPU 故障；
- 两个调度进程、外部 Ray Job 或其他 namespace 同时申请资源；
- fractional GPU 总份额合法但显存不足，以及复杂候选集合存在可行解时的分配结果；
- 动态禁用一张卡后，排队任务、运行任务、设备目录和监控的行为。

在这些测试完成前，这套方案只能视为受控部署下的专项实现，不能视为通用 Ray GPU 调度层。

### 19.4 可选实现方式

#### 方案 A：只使用 Ray 原生 GPU 调度

任务只声明 `num_gpus` 和可选 accelerator type，由 Ray 选择具体卡；任务启动后读取 Ray 分配的 ID、GPU UUID 和名称用于审计。

- 优点：资源预留、placement group、Dashboard、autoscaler、Ray Train/Tune 和多卡任务保持原生兼容，代码最少。
- 缺点：不能在同一多卡 Ray 节点上提前指定物理 GPU 3，也不能在节点启动后单独下线一张卡。
- 适用：产品只要求“获得足够 GPU”，固定卡只是观察或调试需求。

#### 方案 B：一张 GPU 一个 Ray Worker/容器

每个 Worker 在启动前只暴露一个 GPU UUID，并注册原生 `GPU=1`；再使用稳定节点标签或自定义标签选择 Worker。由于节点内只有一张可见卡，节点选择与物理卡选择天然一致。

- 优点：Ray 仍正确预留原生 GPU；指定卡、下线卡和故障隔离都转换为节点级操作；业务层不需要维护 UUID 到 CUDA ordinal 的映射。
- 缺点：需要容器或 Kubernetes Pod 具备独立网络身份；单任务多卡需要额外的多 GPU Worker 池，不能直接跨若干单卡 Actor 拼成一个普通多 GPU Actor。
- 适用：必须精确选卡，且基础设施允许按卡拆分 Worker。当前需求下优先推荐该方案。

#### 方案 C：原生 GPU 常驻 Executor Actor

按节点创建与 GPU 数量相同的常驻 Actor，每个 Actor 原生申请 `num_gpus=1`。Actor 启动后上报自己获得的 UUID，应用维护 `UUID -> Actor` 路由，并把推理调用提交给对应 Actor。需要临时屏蔽某张卡时，保留一个占卡 Actor但停止向其路由。

- 优点：Ray 的原生预留与实际设备一致；无需预先指定 Ray 应该分配哪个 index；很适合长期驻留的模型服务。
- 缺点：业务必须改成向 Executor 调用，不能继续为每个任务创建独立 GPU Actor；Actor 生命周期、模型缓存、失败恢复和多 GPU 协同需要单独设计。
- 适用：固定卡主要用于长期推理服务，而不是任意类型的短任务。

#### 方案 D：继续当前自定义按卡资源方案

只有在“静态 NVIDIA 集群、所有 GPU 工作负载都强制经过 TaskManager、无需 Ray Train/Tune/autoscaler、能够维护私有兼容层”的条件下才适合继续。

若保留，至少需要：

1. 将设备目录、禁用状态和分配 lease 建模为独立调度领域，不再由 Workflow 直接解析 Ray resource key；
2. 使用稳定机器标识和 GPU UUID，部署时验证候选设备仍存在；
3. 将 `auto` 的节点选择推迟到真正调度时，并依据目标 GPU 型号解析预设；
4. 增加 GPU 健康/禁用表，使“停止接收新任务”和“Ray 节点重启后物理下线”成为两个明确阶段；
5. 明确单 Scheduler 约束，或者用数据库锁/lease 处理并发分配；
6. 为 CPU-only Head、混合版本、普通多卡任务和真实 DeepStream 场景增加集成测试；
7. 避免把 Ray 私有模块和实验环境变量扩散到业务代码；
8. 明确自定义资源模式与原生 GPU 模式不可在同一节点无约束混用。

### 19.5 建议结论

- 如果“必须指定 GPU 3”不是硬性产品能力，应删除按卡资源层，恢复 Ray 原生 `num_gpus`。
- 如果必须指定并可独立下线某张卡，优先采用“一卡一个 Worker/容器”，通过节点级调度保证 Ray 预留与物理卡一致。
- 如果主要场景是长期 YOLO/DeepStream 推理，可进一步评估常驻 Executor Actor。
- 当前自定义方案解决了指定卡问题，但代价是接管 Ray 的 GPU 资源模型；在上述高优先级问题解决前，不建议把它作为通用 GPU 调度基础设施。

Ray 2.58 的公开行为仍是：任务/Actor 通过 `num_gpus` 申请数量，由 Ray 选择设备并设置可见设备；节点启动后不能动态修改资源容量。参考 [Ray Accelerator Support](https://docs.ray.io/en/latest/ray-core/scheduling/accelerators.html) 和 [Ray Resources](https://docs.ray.io/en/latest/ray-core/scheduling/resources.html)。
