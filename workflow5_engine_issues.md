# Workflow5 Engine 问题及修改计划

> 分支：`main`  
> 提交：`34aeae8 Add public workflow`

## 1. YOLO DS 路径重复加载模型

**类型：Bug**  
**严重程度：严重**

当前所有 Block 都会先执行 `init()`，YOLO 在此阶段加载 PyTorch `.pt` 模型；启动流任务后，DS 路径又会加载 TensorRT Engine。因此 DS-only 任务仍会产生额外的模型加载、内存和依赖开销，并可能带来额外 GPU 资源影响。

可能考虑将参数配置与后端资源初始化分离，先选择实际执行后端，再加载对应模型；同时抽象统一后端接口，以支持 DeepStream、其他加速平台及纯 Python 环境。

代码依据：

- `backend/workflow5/block_library/models/yolo_detection.py:43`
- `backend/workflow5/engine/engine.py:140`


在 init 的时候指定要使用的加速平台，例如deepstream，在使用某个加速平台的情况下，对于某个block，如果支持deepstream，那么不执行init函数；


## 2. Python 逻辑分支后的 DS Block 可能绕过控制

**类型：Bug**  
**严重程度：严重**

当前 DS 规划会忽略控制边，只检查数据前驱；因此受 Python FlowControl 控制的 DS Block 仍可能被提前注册，并对未进入该分支的帧执行，甚至产生不符合分支语义的输出。

可能考虑将 Python 控制节点视为 DS pipeline 的硬边界；除非控制逻辑能够在 DS 内表达，否则下游 Block 应回到 Python 调度，并只处理实际进入该分支的 sample。

代码依据：

- `backend/workflow5/engine/planner.py:69`
- `backend/workflow5/engine/executor.py:110`

存在flowcontrol节点后，deepstream的图就不往后支持了；


## 3. 多 Image Input 和 Sample 对齐机制存在问题

### 3.1 所有 Image Input 做全局 Source Index 交集

**类型：Bug**  
**严重程度：严重**

当前 Engine 对所有 Image Input 的 source index 做全局交集。任意输入缺少或过期一个 index，都会阻止其他无依赖关系的分支处理该 index。

代码依据：

- `backend/workflow5/engine/engine.py:186`

多image input的情况下，默认先考虑必须所有需要的输入都正常；如果有遇到需要的情况再考虑；


### 3.2 Assembler 无法挽救同批次中的完整 Sample

**类型：Bug**  
**严重程度：中等偏严重**

Assembler 当前以整个 frame tuple 为单位等待所有 boundary。某个 sample 缺失时，同批其他已经完整的 sample 也无法发布，最终可能随 pending 淘汰而静默丢失。

代码依据：

- `backend/workflow5/deepstream/assembler.py:19`





### 3.3 最终输出丢失显式 Source Index

**类型：接口缺陷**  
**严重程度：中等**

内部 `BatchData` 和 `FrameMeta` 一直保留 source index；问题只发生在最终输出被转换成普通 list 时，显式的 index 映射丢失。稀疏 batch 下将无法判断每项来自哪个 source。

代码依据：

- `backend/workflow5/engine/executor.py:155`
- `backend/workflow5/engine/result_store.py:14`

## 4. YOLO DS 推理失败可能被当成零检测结果

**类型：Bug**  
**严重程度：严重**

该问题主要存在于 DS 路径：没有找到输出 tensor 时会传入空数组，tensor 格式异常时也会直接返回空检测，因此推理失败与正常的“未检测到目标”无法区分。

可能考虑分别表示成功零检测、推理失败和后处理失败；缺少 tensor 或 tensor 格式错误时应上报异常，不应返回空结果。

代码依据：

- `backend/workflow5/deepstream/boundary.py:142`
- `backend/workflow5/deepstream/boundary.py:176`

什么情况下会推理失败或者后处理失败？


## 5. 初始化或启动失败时资源清理不完整

**类型：Bug**  
**严重程度：中等，涉及 GPU 资源时严重**

Block 初始化失败时，当前实例及此前已初始化的 Block 不会回滚；`run_stream()` 启动失败时也只停止 DS Manager，没有统一关闭 Block。

可能考虑为初始化和启动过程增加统一的资源所有权管理；失败时按初始化的逆序关闭 Block、pipeline、线程及临时资源，并保证 `close()` 幂等。

代码依据：

- `backend/workflow5/engine/compiler.py:353`
- `backend/workflow5/engine/engine.py:161`

## 6. GStreamer Boundary 缺少完整的实时背压策略

**类型：可靠性 Bug**  
**严重程度：实时流场景严重**

当前并非完全没有丢帧机制：Assembler 结果队列已经支持 RTSP 默认 `drop_oldest`。但该策略位于 Python callback 之后，GStreamer `queue/appsink` 本身没有配置有界缓存和 leaky 策略；callback 处理过慢时，仍可能阻塞 tee 及整个输入 pipeline。

可能考虑在 GStreamer boundary 增加有界队列、latest-only、超时及明确的丢帧策略；同时将背压策略抽象成通用运行时接口，为无 DS 平台提供一致语义。

代码依据：

- `backend/workflow5/deepstream/manager.py:157`
- `backend/workflow5/deepstream/manager.py:697`
- `backend/workflow5/deepstream/assembler.py:62`

## 7. RTSP 重连缺少 Stream Epoch

**类型：潜在 Bug**  
**严重程度：当前中等，引入缓存或录像后严重**

当前 `FrameMeta` 没有连接代际信息，frame identity 只有 `source_id + frame_number`。如果 RTSP 重连后帧号或 PTS 重置，重连前后的帧可能在 Assembler、连续帧缓存和未来录像逻辑中被视为同一条连续流。

可能考虑为每次连接建立递增的 stream epoch，将其加入 `FrameMeta` 和 alignment key；epoch 变化时清理 pending、latest 和有状态窗口，并切分录像片段。

代码依据：

- `backend/workflow5/data_type.py:30`
- `backend/workflow5/deepstream/boundary.py:57`

## 后续优化

### 减少 Image Boundary 的完整图像复制

**类型：性能优化**  
**重要程度：中等，多路高分辨率场景较重要**

代码依据：

- `backend/workflow5/deepstream/boundary.py:92`

### 将 YOLO 后处理进一步下沉到 DeepStream

**类型：性能优化**  
**重要程度：中等**

当前 DS 仅完成推理，tensor 仍会复制到 CPU，并通过 NumPy 完成解码和 NMS。

考虑使用 DS 原生 parser/object metadata 完成后处理，减少 tensor 复制和 Python callback 压力；同时仍需保留明确的推理及解析失败状态。

代码依据：

- `backend/workflow5/deepstream/boundary.py:126`
